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

    @action(detail=False, methods=['get'])
    def export(self, request):
        from django.http import HttpResponse
        from RealEstateReports.services import export_to_excel, export_to_pdf

        export_format = request.query_params.get('export_type', 'excel')
        qs = self.filter_queryset(self.get_queryset())

        data = []
        for plot in qs[:5000]:
            data.append({
                'plot_number': plot.plot_number,
                'project': plot.project.name if plot.project else '-',
                'area_sqyd': str(plot.area_sqyd or '-'),
                'area_sqft': str(plot.area_sqft or '-'),
                'facing': plot.get_facing_display() if plot.facing else '-',
                'road_width': plot.road_width or '-',
                'price_per_sqyd': f"Rs.{plot.price_per_sqyd:,.0f}" if plot.price_per_sqyd else '-',
                'total_price': f"Rs.{plot.total_price:,.0f}" if plot.total_price else '-',
                'status': plot.get_status_display(),
            })

        columns = [
            {'key': 'plot_number', 'label': 'Plot #'},
            {'key': 'project', 'label': 'Project'},
            {'key': 'area_sqyd', 'label': 'Area (sq.yd)'},
            {'key': 'area_sqft', 'label': 'Area (sq.ft)'},
            {'key': 'facing', 'label': 'Facing'},
            {'key': 'road_width', 'label': 'Road Width'},
            {'key': 'price_per_sqyd', 'label': 'Price/sq.yd'},
            {'key': 'total_price', 'label': 'Total Price'},
            {'key': 'status', 'label': 'Status'},
        ]

        if export_format == 'pdf':
            content = export_to_pdf(data, columns, 'Plot Inventory Report')
            response = HttpResponse(content, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="Plot_Report.pdf"'
            return response
        else:
            content = export_to_excel(data, columns, 'Plots')
            response = HttpResponse(content, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="Plot_Report.xlsx"'
            return response


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

    @action(detail=False, methods=['get'])
    def export(self, request):
        from django.http import HttpResponse
        from RealEstateReports.services import export_to_excel, export_to_pdf

        export_format = request.query_params.get('export_type', 'excel')
        qs = self.filter_queryset(self.get_queryset())

        data = []
        for flat in qs[:5000]:
            data.append({
                'unit_number': flat.unit_number,
                'project': flat.project.name if flat.project else '-',
                'tower': flat.tower or '-',
                'floor': str(flat.floor) if flat.floor is not None else '-',
                'flat_type': flat.flat_type or '-',
                'area_sqft': str(flat.area_sqft or '-'),
                'facing': flat.get_facing_display() if flat.facing else '-',
                'price': f"Rs.{flat.price:,.0f}" if flat.price else '-',
                'status': flat.get_status_display(),
            })

        columns = [
            {'key': 'unit_number', 'label': 'Unit #'},
            {'key': 'project', 'label': 'Project'},
            {'key': 'tower', 'label': 'Tower'},
            {'key': 'floor', 'label': 'Floor'},
            {'key': 'flat_type', 'label': 'Type'},
            {'key': 'area_sqft', 'label': 'Area (sq.ft)'},
            {'key': 'facing', 'label': 'Facing'},
            {'key': 'price', 'label': 'Price'},
            {'key': 'status', 'label': 'Status'},
        ]

        if export_format == 'pdf':
            content = export_to_pdf(data, columns, 'Flat Inventory Report')
            response = HttpResponse(content, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="Flat_Report.pdf"'
            return response
        else:
            content = export_to_excel(data, columns, 'Flats')
            response = HttpResponse(content, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="Flat_Report.xlsx"'
            return response
