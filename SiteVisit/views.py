from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.conf import settings
import os
import uuid

from .models import SiteVisit
from .serializers import SiteVisitSerializer

# ponytail: AllPermissions (from DRF default) gives us view/add/change/delete +
# the user-level RBAC matrix in Users.UserPermission. Drop the explicit
# IsAuthenticated override that was bypassing RBAC on this screen.


class SiteVisitViewSet(viewsets.ModelViewSet):
    queryset = SiteVisit.objects.select_related('assigned_employee', 'created_by', 'lead').all()
    serializer_class = SiteVisitSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]  # ponytail: allow multipart on create so photos upload in one shot
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['customer_name', 'project_name', 'assigned_employee__first_name', 'assigned_employee__last_name']
    filterset_fields = ['status', 'assigned_employee', 'lead']
    ordering_fields = ['visit_date', 'created_on']
    ordering = ['-visit_date', '-created_on']

    LEAD_STATUS_BY_VISIT = {
        'SCHEDULED': 'SITE_VISIT_SCHEDULED',
        'CONFIRMED': 'SITE_VISIT_SCHEDULED',  # ponytail: confirmed still pre-visit
        'COMPLETED': 'SITE_VISIT_COMPLETED',
        'CANCELLED': None,  # ponytail: don't auto-revert lead; leave it to user
    }

    def _sync_lead(self, site_visit):
        if not site_visit.lead_id:
            return
        target = self.LEAD_STATUS_BY_VISIT.get(site_visit.status)
        if not target or site_visit.lead.status == target:
            return
        # ponytail: lead.status write only — LeadStatusHistory audit row is the
        # upgrade path, not the v1 minimum.
        site_visit.lead.status = target
        site_visit.lead.save(update_fields=['status', 'modified_on'])

    def _save_photo_file(self, file):
        ext = os.path.splitext(file.name)[1]
        filename = f"{uuid.uuid4().hex}{ext}"
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'sitevisit_photos')
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        with open(filepath, 'wb+') as dest:
            for chunk in file.chunks():
                dest.write(chunk)
        return f"{settings.MEDIA_URL}sitevisit_photos/{filename}"

    def _handle_create_photos(self, instance):
        files = self.request.FILES.getlist('photos')
        if not files:
            return
        photos = list(instance.photos or [])
        for f in files:
            photos.append(self._save_photo_file(f))
        instance.photos = photos
        instance.save(update_fields=['photos'])

    def create(self, request, *args, **kwargs):
        # ponytail: serializer validates photos as JSONField — file blobs fail.
        # Strip the file list from parsed data; perform_create persists them.
        if request.FILES.getlist('photos'):
            request.data.pop('photos', None)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user)
        self._handle_create_photos(instance)
        self._sync_lead(instance)

    def update(self, request, *args, **kwargs):
        # Strip file blobs from parsed data so serializer doesn't choke on JSONField
        if request.FILES.getlist('photos'):
            request.data.pop('photos', None)
        return super().update(request, *args, **kwargs)

    def perform_update(self, serializer):
        instance = serializer.save()
        # Handle new photo uploads on update
        files = self.request.FILES.getlist('photos')
        if files:
            photos = list(instance.photos or [])
            for f in files:
                photos.append(self._save_photo_file(f))
            instance.photos = photos
            instance.save(update_fields=['photos'])
        self._sync_lead(instance)

    @action(detail=True, methods=['post'], url_path='upload-photo', parser_classes=[MultiPartParser, FormParser])
    def upload_photo(self, request, pk=None):
        site_visit = self.get_object()
        file = request.FILES.get('photo')
        if not file:
            return Response({'error': 'No photo provided'}, status=400)

        photo_url = self._save_photo_file(file)
        photos = site_visit.photos or []
        photos.append(photo_url)
        site_visit.photos = photos
        site_visit.save(update_fields=['photos'])

        return Response({'url': photo_url, 'photos': photos})

    @action(detail=True, methods=['post'], url_path='remove-photo')
    def remove_photo(self, request, pk=None):
        site_visit = self.get_object()
        photo_url = request.data.get('url')
        if not photo_url:
            return Response({'error': 'No url provided'}, status=400)

        photos = site_visit.photos or []
        photos = [p for p in photos if p != photo_url]
        site_visit.photos = photos
        site_visit.save(update_fields=['photos'])

        return Response({'photos': photos})

    @action(detail=False, methods=['get'], url_path='choices')
    def choices(self, request):
        return Response({
            'statuses': [
                {'value': value, 'label': label}
                for value, label in SiteVisit.STATUS_CHOICES
            ]
        })