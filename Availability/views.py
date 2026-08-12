"""
Availability List — Views
"""
from django.db import transaction
from django.db.models import Count, Q

from rest_framework import viewsets, status, permissions, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import (
    AvailabilityProject, AvailabilityProjectImage,
    AvailabilityBlock, AvailabilityUnit,
)
from .serializers import (
    AvailabilityProjectSerializer,
    AvailabilityProjectListSerializer,
    AvailabilityProjectImageSerializer,
    AvailabilityBlockSerializer,
    AvailabilityBlockLightSerializer,
    AvailabilityUnitSerializer,
    build_choices,
)


# ──────────────────────────────────────────────────────────────────────────────
# PROJECT  (the "folder")
# ──────────────────────────────────────────────────────────────────────────────

class AvailabilityProjectViewSet(viewsets.ModelViewSet):
    """
    CRUD for top-level project folders.

    Custom actions:
      GET  /choices/                — all dropdown choices
      GET  /{pk}/stats/             — unit count breakdown for the project
      POST /{pk}/images/upload/     — bulk image upload
      DELETE /images/{image_pk}/   — delete a single image (via separate view)
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'project_type', 'is_active']
    search_fields = ['name', 'developer_name', 'location', 'city', 'code']
    ordering_fields = ['name', 'status', 'created_on']
    ordering = ['name']
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return (
            AvailabilityProject.objects
            .filter(is_deleted=False)
            .prefetch_related('blocks', 'images')
        )

    def get_serializer_class(self):
        # List action → lightweight serializer (no nested units)
        if self.action == 'list':
            return AvailabilityProjectListSerializer
        return AvailabilityProjectSerializer

    # ── choices ──────────────────────────────────────────────────────────────

    @action(detail=False, methods=['get'], url_path='choices')
    def choices(self, request):
        return Response(build_choices())

    # ── per-project stats ─────────────────────────────────────────────────────

    @action(detail=True, methods=['get'], url_path='stats')
    def stats(self, request, pk=None):
        project = self.get_object()
        qs = AvailabilityUnit.objects.filter(
            block__project=project, is_deleted=False
        )
        summary = {
            item['status']: item['count']
            for item in qs.values('status').annotate(count=Count('id'))
        }
        total = qs.count()
        # per-block breakdown
        blocks = []
        for block in project.blocks.filter(is_deleted=False).order_by('order', 'name'):
            bqs = AvailabilityUnit.objects.filter(block=block, is_deleted=False)
            bsummary = {
                i['status']: i['count']
                for i in bqs.values('status').annotate(count=Count('id'))
            }
            blocks.append({
                'id': str(block.id),
                'name': block.name,
                'total': bqs.count(),
                'available': bsummary.get('AVAILABLE', 0),
                'blocked': bsummary.get('BLOCKED', 0),
                'booked': bsummary.get('BOOKED', 0),
                'registered': bsummary.get('REGISTERED', 0),
            })
        return Response({
            'project_id': str(project.id),
            'project_name': project.name,
            'total': total,
            'available': summary.get('AVAILABLE', 0),
            'blocked': summary.get('BLOCKED', 0),
            'booked': summary.get('BOOKED', 0),
            'registered': summary.get('REGISTERED', 0),
            'blocks': blocks,
        })

    # ── bulk image upload ─────────────────────────────────────────────────────

    @action(detail=True, methods=['post'], url_path='images/upload',
            parser_classes=[MultiPartParser, FormParser])
    def upload_images(self, request, pk=None):
        project = self.get_object()
        files = request.FILES.getlist('images')
        image_type = request.data.get('image_type', 'GALLERY')
        if not files:
            return Response({'error': 'No images provided.'}, status=status.HTTP_400_BAD_REQUEST)
        created = []
        for f in files:
            img = AvailabilityProjectImage.objects.create(
                project=project,
                image=f,
                image_type=image_type,
                title=request.data.get('title', ''),
                created_by_type='User',
                created_by_identifier=str(request.user.id),
                modified_by_type='User',
                modified_by_identifier=str(request.user.id),
            )
            created.append(AvailabilityProjectImageSerializer(img, context={'request': request}).data)
        return Response(created, status=status.HTTP_201_CREATED)

    # ── soft-delete override ──────────────────────────────────────────────────

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save(update_fields=['is_deleted'])


# ──────────────────────────────────────────────────────────────────────────────
# PROJECT IMAGE (single delete / update)
# ──────────────────────────────────────────────────────────────────────────────

class AvailabilityProjectImageDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AvailabilityProjectImageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AvailabilityProjectImage.objects.filter(is_deleted=False)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save(update_fields=['is_deleted'])


# ──────────────────────────────────────────────────────────────────────────────
# BLOCK
# ──────────────────────────────────────────────────────────────────────────────

class AvailabilityBlockViewSet(viewsets.ModelViewSet):
    """
    CRUD for blocks within a project.

    Custom actions:
      GET  /{pk}/units/          — all units for this block
      POST /{pk}/bulk_units/     — create / replace all units for a block atomically
      GET  /{pk}/stats/          — unit counts for this block
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['project']
    ordering_fields = ['order', 'name']
    ordering = ['order', 'name']

    def get_queryset(self):
        return AvailabilityBlock.objects.filter(is_deleted=False).select_related('project')

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve') and self.request.query_params.get('light'):
            return AvailabilityBlockLightSerializer
        return AvailabilityBlockSerializer

    # ── all units for block ───────────────────────────────────────────────────

    @action(detail=True, methods=['get'], url_path='units')
    def units(self, request, pk=None):
        block = self.get_object()
        qs = AvailabilityUnit.objects.filter(block=block, is_deleted=False).order_by('floor', 'unit_number')
        serializer = AvailabilityUnitSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    # ── bulk create / replace units ───────────────────────────────────────────

    @action(detail=True, methods=['post'], url_path='bulk_units')
    def bulk_units(self, request, pk=None):
        """
        Replace all units for a block in one atomic transaction.
        Body: { "units": [ { unit_number, unit_type, floor, area_sqft, price, status, ... } ] }

        We bypass the serializer UniqueTogetherValidator because DRF runs it
        against the DB before our delete completes, causing false conflicts.
        Instead we validate manually then use bulk_create directly.
        """
        block = self.get_object()
        units_data = request.data.get('units', [])
        if not isinstance(units_data, list):
            return Response({'error': 'units must be a list.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate unit_number uniqueness within the submitted batch
        seen_numbers = set()
        for idx, unit_data in enumerate(units_data):
            num = str(unit_data.get('unit_number', '')).strip()
            if not num:
                return Response(
                    {'errors': [{'index': idx, 'errors': {'unit_number': ['This field is required.']}}]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if num in seen_numbers:
                return Response(
                    {'errors': [{'index': idx, 'errors': {'unit_number': [f'Duplicate unit_number "{num}" in submitted list.']}}]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            seen_numbers.add(num)

        valid_statuses = [c[0] for c in AvailabilityUnit._meta.get_field('status').choices]
        user_type = 'User'
        user_id = str(request.user.id)

        with transaction.atomic():
            # Hard-delete existing units so the DB unique constraint is clean
            AvailabilityUnit.objects.filter(block=block).delete()

            to_create = []
            for unit_data in units_data:
                raw_status = unit_data.get('status', 'AVAILABLE')
                to_create.append(AvailabilityUnit(
                    block=block,
                    unit_number=str(unit_data.get('unit_number', '')).strip(),
                    unit_type=unit_data.get('unit_type') or None,
                    floor=unit_data.get('floor') or None,
                    area_sqft=unit_data.get('area_sqft') or None,
                    area_sqyd=unit_data.get('area_sqyd') or None,
                    carpet_area_sqft=unit_data.get('carpet_area_sqft') or None,
                    facing=unit_data.get('facing') or None,
                    price=unit_data.get('price') or None,
                    status=raw_status if raw_status in valid_statuses else 'AVAILABLE',
                    remarks=unit_data.get('remarks') or None,
                    created_by_type=user_type,
                    created_by_identifier=user_id,
                    modified_by_type=user_type,
                    modified_by_identifier=user_id,
                ))

            created_objs = AvailabilityUnit.objects.bulk_create(to_create)

        serializer = AvailabilityUnitSerializer(created_objs, many=True, context={'request': request})
        return Response({'created': len(created_objs), 'units': serializer.data}, status=status.HTTP_201_CREATED)

    # ── block stats ───────────────────────────────────────────────────────────

    @action(detail=True, methods=['get'], url_path='stats')
    def stats(self, request, pk=None):
        block = self.get_object()
        qs = AvailabilityUnit.objects.filter(block=block, is_deleted=False)
        summary = {
            item['status']: item['count']
            for item in qs.values('status').annotate(count=Count('id'))
        }
        total = qs.count()
        return Response({
            'block_id': str(block.id),
            'block_name': block.name,
            'total': total,
            'available': summary.get('AVAILABLE', 0),
            'blocked': summary.get('BLOCKED', 0),
            'booked': summary.get('BOOKED', 0),
            'registered': summary.get('REGISTERED', 0),
        })

    # ── soft-delete ────────────────────────────────────────────────────────────

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save(update_fields=['is_deleted'])


# ──────────────────────────────────────────────────────────────────────────────
# UNIT
# ──────────────────────────────────────────────────────────────────────────────

class AvailabilityUnitViewSet(viewsets.ModelViewSet):
    """
    CRUD for individual units. Also supports:
      PATCH /{pk}/update_status/  — quick status change
    """
    serializer_class = AvailabilityUnitSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['block', 'status', 'unit_type', 'facing', 'floor']
    search_fields = ['unit_number']
    ordering_fields = ['floor', 'unit_number', 'status', 'price']
    ordering = ['floor', 'unit_number']

    def get_queryset(self):
        return (
            AvailabilityUnit.objects
            .filter(is_deleted=False)
            .select_related('block__project')
        )

    @action(detail=True, methods=['patch'], url_path='update_status')
    def update_status(self, request, pk=None):
        unit = self.get_object()
        new_status = request.data.get('status')
        if not new_status:
            return Response({'error': 'status is required.'}, status=status.HTTP_400_BAD_REQUEST)
        valid = [c[0] for c in AvailabilityUnit._meta.get_field('status').choices]
        if new_status not in valid:
            return Response({'error': f'Invalid status. Choose from: {valid}'}, status=status.HTTP_400_BAD_REQUEST)
        unit.status = new_status
        unit.modified_by_type = 'User'
        unit.modified_by_identifier = str(request.user.id)
        unit.save(update_fields=['status', 'modified_by_type', 'modified_by_identifier'])
        return Response(AvailabilityUnitSerializer(unit, context={'request': request}).data)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save(update_fields=['is_deleted'])
