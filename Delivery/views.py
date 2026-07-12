from rest_framework import generics, permissions, filters, status
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters import FilterSet, CharFilter, DateFilter, NumberFilter, ChoiceFilter, UUIDFilter
from django_filters.rest_framework import DjangoFilterBackend

from Core.Core.permissions.permissions import GetPermission
from .models import ProofOfDelivery, ProofOfDeliveryFile
from .serializers import (
    ProofOfDeliveryListSerializer,
    ProofOfDeliveryDetailSerializer,
    ProofOfDeliveryFileSerializer,
    ProofOfDeliveryStatusCountSerializer,
)
from .services import update_pod_effects
from utils import apply_company_location_filter
import re
from django.utils import timezone
from django.db.models import Count

class ProofOfDeliveryFilter(FilterSet):
    invoice_number = CharFilter(field_name='invoice__invoice_number', lookup_expr='icontains')
    status = CharFilter(field_name='status')
    delivered_from = DateFilter(field_name='delivered_date', lookup_expr='gte')
    delivered_to = DateFilter(field_name='delivered_date', lookup_expr='lte')
    sales_order = CharFilter(field_name='sales_order')
    authorized_status = NumberFilter(field_name='authorized_status')

    class Meta:
        model = ProofOfDelivery
        fields = ['invoice_number', 'status', 'sales_order', 'authorized_status', 'delivered_from', 'delivered_to']


class ProofOfDeliveryReportFilter(FilterSet):
    """FilterSet for POD report export with date range and business filters."""

    from_date = DateFilter(field_name='pod_date', lookup_expr='gte')
    to_date = DateFilter(field_name='pod_date', lookup_expr='lte')
    customer_type = ChoiceFilter(
        field_name='customer_type',
        choices=[('RETAILER', 'Retailer'), ('DISTRIBUTOR', 'Distributor'), ('SUPERSTOCKIST', 'Superstockist')],
    )
    invoice_number = CharFilter(field_name='invoice__invoice_number', lookup_expr='icontains')
    pod_number = CharFilter(field_name='pod_number', lookup_expr='icontains')
    status = ChoiceFilter(field_name='status', choices=ProofOfDelivery.STATUS_CHOICES)
    authorization_status = ChoiceFilter(
        field_name='authorized_status',
        choices=[
            (1, 'Pending'),
            (2, 'Approved'),
            (3, 'Rejected'),
        ],
    )
    agent = UUIDFilter(field_name='sales_order__distributor__agent_id')

    class Meta:
        model = ProofOfDelivery
        fields = ['from_date', 'to_date', 'customer_type', 'invoice_number', 'pod_number', 'status', 'authorization_status', 'agent']


class GeneratePODNumber(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        from django.db import transaction
        
        today = timezone.now().date()
        
        # Determine financial year (April 1 to March 31)
        if today.month >= 4:
            fy_start = today.year
            fy_end = today.year + 1
        else:
            fy_start = today.year - 1
            fy_end = today.year
        
        fy_suffix = f"{str(fy_start)[-2:]}-{str(fy_end)[-2:]}"
        prefix = f"POD-{fy_suffix}"
        
        # Use atomic transaction with SELECT FOR UPDATE to prevent race conditions
        with transaction.atomic():
            # Get all matching POD numbers and compute the max numeric suffix
            pod_numbers = ProofOfDelivery.objects.filter(
                pod_number__startswith=prefix
            ).select_for_update().values_list('pod_number', flat=True)

            max_suffix = 0
            for pn in pod_numbers:
                match = re.search(r'-(\d+)$', pn or '')
                if match:
                    try:
                        max_suffix = max(max_suffix, int(match.group(1)))
                    except ValueError:
                        continue

            pod_number = f"{prefix}-{max_suffix + 1}"
        
        return Response({
            'pod_number': pod_number,
            'financial_year': fy_suffix
        }, status=status.HTTP_200_OK)


class ProofOfDeliveryListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProofOfDeliveryFilter
    search_fields = ['code', 'invoice__invoice_number', 'sales_order__order_number', 'receiver_name']
    ordering_fields = ['delivered_date', 'pod_date', 'code', 'authorized_status', 'authorized_on', 'created_on']
    ordering = ['-created_on']
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProofOfDeliveryDetailSerializer
        return ProofOfDeliveryListSerializer

    def get_queryset(self):
        queryset = ProofOfDelivery.filtered_objects.get_qs(
            user=self.request.user
        ).select_related(
            'invoice', 'sales_order', 'sales_order__retailer',
            'sales_order__distributor', 'sales_order__superstockist'
        ).prefetch_related('files')
        return apply_company_location_filter(
            queryset, self.request.user,
            company_field='invoice__company', location_field='invoice__location'
        )

    def perform_create(self, serializer):
        pod = serializer.save()
        files = self.request.FILES.getlist('files')
        descriptions = self.request.data.getlist('file_descriptions')

        for idx, uploaded in enumerate(files):
            ProofOfDeliveryFile.objects.create(
                proof=pod,
                file=uploaded,
                original_filename=uploaded.name or '',
                description=descriptions[idx] if idx < len(descriptions) else '',
            )
        update_pod_effects(pod)


class ProofOfDeliveryDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProofOfDeliveryDetailSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        queryset = ProofOfDelivery.filtered_objects.get_qs(
            user=self.request.user
        ).select_related(
            'invoice', 'sales_order', 'sales_order__retailer',
            'sales_order__distributor', 'sales_order__superstockist',
            'sales_order__billing_state', 'sales_order__billing_city', 'sales_order__billing_area',
            'sales_order__shipping_state', 'sales_order__shipping_city', 'sales_order__shipping_area'
        ).prefetch_related('files')
        return apply_company_location_filter(
            queryset, self.request.user,
            company_field='invoice__company', location_field='invoice__location'
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Handle additional files on update
        files = request.FILES.getlist('files')
        descriptions = request.data.getlist('file_descriptions')

        for idx, uploaded in enumerate(files):
            ProofOfDeliveryFile.objects.create(
                proof=instance,
                file=uploaded,
                original_filename=uploaded.name or '',
                description=descriptions[idx] if idx < len(descriptions) else '',
            )

        update_pod_effects(instance)
        
        # Re-fetch instance with files to return updated data
        instance = self.get_queryset().get(pk=instance.pk)

        return Response(self.get_serializer(instance).data)


class ProofOfDeliveryFileDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk, file_id):
        queryset = ProofOfDelivery.filtered_objects.get_qs(user=request.user)
        queryset = apply_company_location_filter(
            queryset,
            request.user,
            company_field='invoice__company',
            location_field='invoice__location'
        )
        proof = get_object_or_404(queryset, pk=pk)
        attachment = get_object_or_404(
            ProofOfDeliveryFile,
            id=file_id,
            proof=proof,
            is_deleted=False
        )
        attachment.is_deleted = True
        attachment.save(update_fields=['is_deleted', 'modified_on'])
        return Response({"message": "Attachment deleted successfully"}, status=status.HTTP_200_OK)


class AvailableCustomersForPODView(generics.ListAPIView):
    """Get customers who have invoices pending for POD"""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code']
    
    def get_queryset(self):
        customer_type = self.request.query_params.get('customer_type')
        
        if not customer_type:
            return []
        
        from Invoice.models import Invoice
        
        # Get invoices with pod_status PENDING, filtered by user's company/location access
        pending_invoices = Invoice.filtered_objects.get_qs(
            user=self.request.user,
            pod_status='PENDING',
            status__in=['CONFIRMED', 'PAID', 'PARTIALLY_PAID'],
            is_deleted=False
        )
        pending_invoices = apply_company_location_filter(
            pending_invoices, self.request.user,
            company_field='company', location_field='location'
        )
        
        # Get unique customer IDs
        customer_field = f'{customer_type.lower()}'
        customer_ids = pending_invoices.filter(
            sales_order__customer_type=customer_type
        ).values_list(f'sales_order__{customer_field}', flat=True).distinct()
        
        # Get customer model based on type
        if customer_type == 'RETAILER':
            from Masters.models import Retailer
            return Retailer.objects.filter(id__in=customer_ids, is_deleted=False)
        elif customer_type == 'DISTRIBUTOR':
            from Masters.models import Distributor
            return Distributor.objects.filter(id__in=customer_ids, is_deleted=False)
        elif customer_type == 'SUPERSTOCKIST':
            from Masters.models import Superstockist
            return Superstockist.objects.filter(id__in=customer_ids, is_deleted=False)
        
        return []
    
    def get_serializer_class(self):
        from rest_framework import serializers
        
        class CustomerSerializer(serializers.Serializer):
            id = serializers.UUIDField()
            name = serializers.CharField()
            code = serializers.CharField()
        
        return CustomerSerializer


class ProofOfDeliveryStatusCountView(generics.ListAPIView):
    """Get count of proof of deliveries grouped by status"""
    permission_classes = [GetPermission('Delivery.view_proofofdelivery')]
    serializer_class = ProofOfDeliveryStatusCountSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProofOfDeliveryFilter
    
    def get_queryset(self):
        queryset = ProofOfDelivery.objects.filter(is_deleted=False)
        queryset = apply_company_location_filter(
            queryset,
            self.request.user,
            company_field='invoice__company',
            location_field='invoice__location'
        )
        return queryset
    
    def get(self, request, *args, **kwargs):
        try:
            # Get filtered queryset
            queryset = self.get_queryset()
            
            # Get counts by status
            status_counts = queryset.values('status').annotate(
                count=Count('id')
            ).order_by('status')
            
            # Build response with all statuses
            all_statuses = {
                'PENDING': 0,
                'SUCCESS': 0,
                'FAILED': 0,
                'PARTIAL': 0,
            }
            
            # Populate with actual counts
            for item in status_counts:
                if item['status'] in all_statuses:
                    all_statuses[item['status']] = item['count']
            
            # Add total count
            all_statuses['total'] = sum(all_statuses.values())
            
            serializer = ProofOfDeliveryStatusCountSerializer(all_statuses)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Error fetching status counts: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
