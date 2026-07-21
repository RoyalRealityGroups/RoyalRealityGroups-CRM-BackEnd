from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db.models import Count

from .models import PlotInventory, FlatInventory
from .serializers import (
    PlotInventorySerializer, FlatInventorySerializer,
    INVENTORY_STATUS_LIST, FACING_LIST,
)


class PlotInventoryViewSet(viewsets.ModelViewSet):
    """Module 7 - Plot Inventory Management"""
    queryset = PlotInventory.objects.select_related('project').filter(is_deleted=False)
    serializer_class = PlotInventorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'status', 'facing']
    search_fields = ['plot_number', 'code']
    ordering_fields = ['plot_number', 'area_sqyd', 'total_price', 'status']
    ordering = ['plot_number']

    def get_queryset(self):
        qs = super().get_queryset()
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        if from_date:
            qs = qs.filter(created_on__date__gte=from_date)
        if to_date:
            qs = qs.filter(created_on__date__lte=to_date)
        return qs

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update plot status"""
        plot = self.get_object()
        new_status = request.data.get('status')
        if not new_status:
            return Response({'error': 'status is required'}, status=status.HTTP_400_BAD_REQUEST)
        plot.status = new_status
        plot.save(update_fields=['status'])
        return Response(PlotInventorySerializer(plot, context={'request': request}).data)

    @action(detail=False, methods=['get'])
    def choices(self, request):
        return Response({'statuses': INVENTORY_STATUS_LIST, 'facings': FACING_LIST})

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Inventory summary grouped by status"""
        project_id = request.query_params.get('project')
        qs = PlotInventory.objects.filter(is_deleted=False)
        if project_id:
            qs = qs.filter(project_id=project_id)
        summary = {
            item['status']: item['count']
            for item in qs.values('status').annotate(count=Count('id'))
        }
        total = qs.count()
        return Response({
            'total': total,
            'available': summary.get('AVAILABLE', 0),
            'blocked': summary.get('BLOCKED', 0),
            'booked': summary.get('BOOKED', 0),
            'registered': summary.get('REGISTERED', 0),
        })


class FlatInventoryViewSet(viewsets.ModelViewSet):
    """Module 7 - Flat / Unit Inventory Management"""
    queryset = FlatInventory.objects.select_related('project').filter(is_deleted=False)
    serializer_class = FlatInventorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'status', 'facing', 'tower', 'flat_type']
    search_fields = ['unit_number', 'code', 'tower']
    ordering_fields = ['tower', 'floor', 'unit_number', 'price', 'status']
    ordering = ['tower', 'floor', 'unit_number']

    def get_queryset(self):
        qs = super().get_queryset()
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        if from_date:
            qs = qs.filter(created_on__date__gte=from_date)
        if to_date:
            qs = qs.filter(created_on__date__lte=to_date)
        return qs

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update flat status"""
        flat = self.get_object()
        new_status = request.data.get('status')
        if not new_status:
            return Response({'error': 'status is required'}, status=status.HTTP_400_BAD_REQUEST)
        flat.status = new_status
        flat.save(update_fields=['status'])
        return Response(FlatInventorySerializer(flat, context={'request': request}).data)

    @action(detail=False, methods=['get'])
    def choices(self, request):
        return Response({'statuses': INVENTORY_STATUS_LIST, 'facings': FACING_LIST})

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Flat inventory summary"""
        project_id = request.query_params.get('project')
        qs = FlatInventory.objects.filter(is_deleted=False)
        if project_id:
            qs = qs.filter(project_id=project_id)
        summary = {
            item['status']: item['count']
            for item in qs.values('status').annotate(count=Count('id'))
        }
        total = qs.count()
        return Response({
            'total': total,
            'available': summary.get('AVAILABLE', 0),
            'blocked': summary.get('BLOCKED', 0),
            'booked': summary.get('BOOKED', 0),
            'registered': summary.get('REGISTERED', 0),
        })
