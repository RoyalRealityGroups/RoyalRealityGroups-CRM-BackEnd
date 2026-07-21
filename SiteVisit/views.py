from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.utils import timezone

from .models import SiteVisit, SiteVisitPhoto, SITE_VISIT_STATUS_TRANSITIONS
from .serializers import SiteVisitSerializer, SiteVisitPhotoSerializer, SITE_VISIT_STATUS_CHOICES_LIST


class SiteVisitViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Site Visit Management - Module 5.

    Schedule Site Visit: customer_name, project, visit_date, assigned_employee
    Status: Scheduled → Confirmed → Completed / Cancelled
    Completion Details: customer_feedback, remarks, photos
    """
    queryset = SiteVisit.objects.select_related(
        'lead', 'project', 'assigned_employee'
    ).filter(is_deleted=False)
    serializer_class = SiteVisitSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'project', 'assigned_employee', 'lead']
    search_fields = ['customer_name', 'project_name', 'code']
    ordering_fields = ['visit_date', 'created_on']
    ordering = ['-visit_date']
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        if from_date:
            qs = qs.filter(visit_date__gte=from_date)
        if to_date:
            qs = qs.filter(visit_date__lte=to_date)
        return qs

    # Lead status sync mapping
    LEAD_STATUS_BY_VISIT = {
        'SCHEDULED': 'SITE_VISIT_SCHEDULED',
        'CONFIRMED': 'SITE_VISIT_SCHEDULED',
        'COMPLETED': 'SITE_VISIT_COMPLETED',
        'CANCELLED': None,
    }

    def _sync_lead_status(self, site_visit):
        """Auto-update linked lead status based on visit status."""
        if not site_visit.lead_id:
            return
        target = self.LEAD_STATUS_BY_VISIT.get(site_visit.status)
        if not target:
            return
        if site_visit.lead.status == target:
            return
        site_visit.lead.status = target
        site_visit.lead.save(update_fields=['status', 'modified_on'])

    def perform_create(self, serializer):
        instance = serializer.save()
        self._handle_photos(instance)
        self._sync_lead_status(instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        self._handle_photos(instance)
        self._sync_lead_status(instance)

    def _handle_photos(self, instance):
        """Save uploaded photo files as SiteVisitPhoto records."""
        files = self.request.FILES.getlist("photos")
        if not files:
            return
        for photo in files:
            SiteVisitPhoto.objects.create(
                site_visit=instance,
                photo=photo,
            )

    @action(detail=True, methods=['post'])
    def upload_photos(self, request, pk=None):
        """Upload photos for a site visit (typically on completion)."""
        site_visit = self.get_object()
        photos = request.FILES.getlist('photos')
        if not photos:
            return Response({'error': 'No photos provided'}, status=status.HTTP_400_BAD_REQUEST)

        created = []
        for photo in photos:
            obj = SiteVisitPhoto.objects.create(
                site_visit=site_visit,
                photo=photo,
                caption=request.data.get('caption', ''),
            )
            created.append(SiteVisitPhotoSerializer(obj).data)

        return Response({'photos': created, 'count': len(created)}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def delete_photo(self, request, pk=None):
        """Delete a specific photo from a site visit."""
        site_visit = self.get_object()
        photo_id = request.data.get('photo_id')
        if not photo_id:
            return Response({'error': 'photo_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            photo = site_visit.photos.get(id=photo_id)
            photo.delete()
            return Response({'message': 'Photo deleted'}, status=status.HTTP_200_OK)
        except SiteVisitPhoto.DoesNotExist:
            return Response({'error': 'Photo not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update site visit status with optional completion details."""
        sv = self.get_object()
        new_status = request.data.get('status')
        if not new_status:
            return Response({'error': 'status is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate transition
        allowed = SITE_VISIT_STATUS_TRANSITIONS.get(sv.status, set())
        if new_status != sv.status and new_status not in allowed:
            return Response(
                {'error': f'Cannot transition from {sv.status} to {new_status}. Allowed: {sorted(allowed) or "none (terminal)"}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        sv.status = new_status
        if new_status == 'COMPLETED':
            sv.customer_feedback = request.data.get('customer_feedback', sv.customer_feedback)
            sv.remarks = request.data.get('remarks', sv.remarks)
        sv.save()

        # Sync linked lead status
        self._sync_lead_status(sv)

        return Response(SiteVisitSerializer(sv, context={'request': request}).data)

    @action(detail=False, methods=['get'])
    def choices(self, request):
        """Return available status choices for dropdowns."""
        return Response({
            'statuses': SITE_VISIT_STATUS_CHOICES_LIST,
        })

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Site visit statistics for dashboard."""
        today = timezone.now().date()
        qs = SiteVisit.objects.filter(is_deleted=False)
        return Response({
            'total': qs.count(),
            'today': qs.filter(visit_date=today).count(),
            'scheduled': qs.filter(status='SCHEDULED').count(),
            'confirmed': qs.filter(status='CONFIRMED').count(),
            'completed': qs.filter(status='COMPLETED').count(),
            'cancelled': qs.filter(status='CANCELLED').count(),
        })
