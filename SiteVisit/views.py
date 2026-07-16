from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.conf import settings
import os
import uuid

from .models import SiteVisit
from .serializers import SiteVisitSerializer


class SiteVisitViewSet(viewsets.ModelViewSet):
    queryset = SiteVisit.objects.select_related('assigned_employee', 'created_by').all()
    serializer_class = SiteVisitSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['customer_name', 'project_name', 'assigned_employee__first_name', 'assigned_employee__last_name']
    filterset_fields = ['status', 'assigned_employee']
    ordering_fields = ['visit_date', 'created_on']
    ordering = ['-visit_date', '-created_on']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'], url_path='upload-photo', parser_classes=[MultiPartParser, FormParser])
    def upload_photo(self, request, pk=None):
        site_visit = self.get_object()
        file = request.FILES.get('photo')
        if not file:
            return Response({'error': 'No photo provided'}, status=400)

        # Save file to media/sitevisit_photos/
        ext = os.path.splitext(file.name)[1]
        filename = f"{uuid.uuid4().hex}{ext}"
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'sitevisit_photos')
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)

        with open(filepath, 'wb+') as dest:
            for chunk in file.chunks():
                dest.write(chunk)

        photo_url = f"{settings.MEDIA_URL}sitevisit_photos/{filename}"
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