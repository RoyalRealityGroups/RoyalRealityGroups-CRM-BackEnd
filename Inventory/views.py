from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Plot, Flat
from .serializers import PlotSerializer, FlatSerializer


class PlotViewSet(viewsets.ModelViewSet):
    queryset = Plot.objects.select_related('project').all()
    serializer_class = PlotSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['plot_number', 'project__name', 'facing']
    filterset_fields = ['status', 'project']
    ordering_fields = ['plot_number', 'price', 'created_on']
    ordering = ['project', 'plot_number']

    @action(detail=False, methods=['get'], url_path='choices')
    def choices(self, request):
        return Response({
            'statuses': [{'value': v, 'label': l} for v, l in Plot.STATUS_CHOICES]
        })


class FlatViewSet(viewsets.ModelViewSet):
    queryset = Flat.objects.select_related('project').all()
    serializer_class = FlatSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['tower', 'unit_number', 'project__name', 'facing']
    filterset_fields = ['status', 'project', 'tower', 'floor']
    ordering_fields = ['tower', 'floor', 'unit_number', 'price']
    ordering = ['project', 'tower', 'floor', 'unit_number']

    @action(detail=False, methods=['get'], url_path='choices')
    def choices(self, request):
        return Response({
            'statuses': [{'value': v, 'label': l} for v, l in Flat.STATUS_CHOICES]
        })