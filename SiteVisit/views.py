from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

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

    @action(detail=False, methods=['get'], url_path='choices')
    def choices(self, request):
        return Response({
            'statuses': [
                {'value': value, 'label': label}
                for value, label in SiteVisit.STATUS_CHOICES
            ]
        })