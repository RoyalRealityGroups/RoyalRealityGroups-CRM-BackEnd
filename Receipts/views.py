from rest_framework import generics, permissions, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters import FilterSet, CharFilter, DateFilter, NumberFilter, UUIDFilter, ChoiceFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.db.models import Q, Sum, Count
from decimal import Decimal
from datetime import datetime, timedelta, date

from Core.Core.permissions.permissions import GetPermission

from .models import (
    Receipt, ReceiptAllocation, ReceiptAttachment, CustomerCredit,
    CreditUtilization, CustomerLedgerEntry
)
from .serializers import (
    ReceiptListSerializer, ReceiptDetailSerializer, CustomerLedgerEntrySerializer,
)
from Invoice.models import Invoice
from utils import apply_company_location_filter


class ReceiptFilter(FilterSet):
    receipt_number = CharFilter(field_name='receipt_number', lookup_expr='icontains')
    payment_mode = CharFilter(field_name='payment_mode')
    receipt_date_from = DateFilter(field_name='receipt_date', lookup_expr='gte')
    receipt_date_to = DateFilter(field_name='receipt_date', lookup_expr='lte')
    location = CharFilter(field_name='location')
    customer_type = CharFilter(field_name='customer_type')
    authorized_status = NumberFilter(field_name='authorized_status')
    
    class Meta:
        model = Receipt
        fields = ['receipt_number', 'payment_mode', 'receipt_date_from', 'receipt_date_to', 'location', 'customer_type', 'authorized_status']


class ReceiptListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ReceiptListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ReceiptFilter
    search_fields = [
        'receipt_number', 'code', 'reference_number',
        'retailer__name', 'retailer__code',
        'distributor__name', 'distributor__code',
        'superstockist__name', 'superstockist__code',
        'remarks'
    ]
    ordering_fields = ['receipt_date', 'receipt_number', 'total_amount', 'authorized_status', 'created_on']
    ordering = ['-receipt_date', '-created_on']
    
    def get_queryset(self):
        queryset = Receipt.filtered_objects.get_qs(
            user=self.request.user
        ).select_related(
            'company', 'location', 'retailer', 'distributor', 'superstockist'
        ).prefetch_related('allocations')
        return apply_company_location_filter(
            queryset, self.request.user,
            company_field='company', location_field='location'
        )


class ReceiptDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ReceiptDetailSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_queryset(self):
        queryset = Receipt.filtered_objects.get_qs(
            user=self.request.user
        ).select_related(
            'company', 'location', 'retailer', 'distributor', 'superstockist'
        ).prefetch_related(
            'allocations', 'allocations__invoice', 'attachments'
        )
        return apply_company_location_filter(
            queryset, self.request.user,
            company_field='company', location_field='location'
        )
    
    def update(self, request, *args, **kwargs):
        import json
        
        # Convert QueryDict to regular dict and flatten single-item lists
        data = {}
        for key, value in request.data.items():
            if key == 'allocations' and isinstance(value, str):
                data[key] = json.loads(value)
            elif isinstance(value, list) and len(value) == 1:
                data[key] = value[0]
            else:
                data[key] = value
        
        # Get credit_amount and pass to serializer context
        credit_amount = float(request.data.get('credit_amount', 0))
        
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=data, partial=False, context={'credit_amount': credit_amount})
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer, credit_amount)
        
        return Response(serializer.data)
    
    @transaction.atomic
    def perform_update(self, serializer, credit_amount):
        instance = serializer.instance
        
        # Check if saving as draft
        is_draft = self.request.data.get('authorized_status') == '0'
        
        # Step 1: Reverse existing invoice payments
        for allocation in instance.allocations.all():
            invoice = allocation.invoice
            invoice.paid_amount -= allocation.allocated_amount
            invoice.balance_amount += allocation.allocated_amount
            invoice.update_payment_status()
            invoice.save()
        
        # Step 2: Reverse credit utilizations (must be done before deleting credits)
        from decimal import Decimal
        for utilization in instance.credit_utilizations.all():
            credit = utilization.credit
            credit.available_amount += utilization.utilized_amount
            credit.save()
            utilization.delete()
        
        # Step 3: Reverse customer credit created by this receipt
        # Check if credit was used by other receipts
        credits_created = CustomerCredit.objects.filter(receipt=instance)
        for credit in credits_created:
            if credit.utilizations.exists():
                # Credit was used by other receipts, cannot delete
                raise serializers.ValidationError({
                    'error': f'Cannot edit this receipt because the credit it created (₹{credit.credit_amount}) has been used by other receipts. Please reverse those receipts first.'
                })
            credit.delete()
        
        # Step 4: Delete old allocations
        instance.allocations.all().delete()
        
        # Step 5: Validate new allocations against restored invoice balances
        new_allocations = serializer.validated_data.get('allocations', [])
        for alloc_data in new_allocations:
            invoice = alloc_data.get('invoice')
            allocated_amount = alloc_data.get('allocated_amount')
            
            # Now validate against the restored balance
            if allocated_amount > invoice.balance_amount:
                raise serializers.ValidationError({
                    'allocations': f'Amount {allocated_amount} cannot exceed invoice {invoice.invoice_number} balance of {invoice.balance_amount}'
                })
        
        # Step 6: Save updated receipt
        receipt = serializer.save(
            modified_by_type='User',
            modified_by_identifier=str(self.request.user.id) if self.request.user.is_authenticated else 'Anonymous'
        )
        
        # Override authorization status if explicitly saving as draft
        if is_draft:
            receipt.authorized_status = 0
            receipt.current_authorized_status = 0
            receipt.authorized_level = 0
            receipt.current_authorized_level = 0
            receipt.save(update_fields=['authorized_status', 'current_authorized_status', 'authorized_level', 'current_authorized_level'])
        elif receipt.authorized_status == 0:
            # Draft -> normal save path for models without a status field
            receipt.save(force_authorization_recalc=True)
        
        # Step 7: Update invoice payments with new allocations
        receipt.update_invoice_payments()
        
        # Step 8: Handle credit utilization
        if credit_amount and float(credit_amount) > 0:
            self.utilize_customer_credit(receipt, float(credit_amount))
        
        # Step 9: Create customer credit for unallocated amount when approved
        if receipt.authorized_status == 2:
            receipt.create_customer_credit()
    
    def utilize_customer_credit(self, receipt, credit_amount):
        """Utilize customer credit for this receipt"""
        from decimal import Decimal
        
        # Get available credits for this customer
        filter_kwargs = {
            'customer_type': receipt.customer_type,
            'available_amount__gt': 0,
            'authorized_status': 2
        }
        
        if receipt.customer_type == 'RETAILER':
            filter_kwargs['retailer'] = receipt.retailer
        elif receipt.customer_type == 'DISTRIBUTOR':
            filter_kwargs['distributor'] = receipt.distributor
        elif receipt.customer_type == 'SUPERSTOCKIST':
            filter_kwargs['superstockist'] = receipt.superstockist
        
        credits = CustomerCredit.objects.filter(**filter_kwargs).order_by('created_on')
        
        remaining = Decimal(str(credit_amount))
        
        for credit in credits:
            if remaining <= 0:
                break
            
            utilize_amount = min(credit.available_amount, remaining)
            
            # Create utilization record
            CreditUtilization.objects.create(
                credit=credit,
                receipt=receipt,
                utilized_amount=utilize_amount,
                remarks=f'Credit utilized for receipt {receipt.receipt_number}'
            )
            
            # Update available amount
            credit.available_amount -= utilize_amount
            credit.save(update_fields=['available_amount'])
            
            remaining -= utilize_amount
    
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.authorized_status != 0:
            return Response(
                {'error': 'Only DRAFT receipts can be deleted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Reverse invoice payments
            for allocation in instance.allocations.all():
                invoice = allocation.invoice
                invoice.paid_amount -= allocation.allocated_amount
                invoice.balance_amount += allocation.allocated_amount
                invoice.save()
            
            instance.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReceiptCreateView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ReceiptDetailSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def create(self, request, *args, **kwargs):
        import json
        
        # Convert QueryDict to regular dict and flatten single-item lists
        data = {}
        for key, value in request.data.items():
            if key == 'allocations' and isinstance(value, str):
                data[key] = json.loads(value)
            elif isinstance(value, list) and len(value) == 1:
                data[key] = value[0]
            else:
                data[key] = value
        
        # Get credit_amount and pass to serializer context
        credit_amount = float(request.data.get('credit_amount', 0))
        
        serializer = self.get_serializer(data=data, context={'credit_amount': credit_amount})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @transaction.atomic
    def perform_create(self, serializer):
        # Generate receipt number if not provided
        location = serializer.validated_data.get('location')
        if location and not serializer.validated_data.get('receipt_number'):
            receipt_number = Receipt.generate_receipt_number(location.code)
            serializer.validated_data['receipt_number'] = receipt_number
        
        # Get credit amount if provided
        credit_amount = self.request.data.get('credit_amount')
        
        # Check if saving as draft
        is_draft = self.request.data.get('authorized_status') == '0'
        
        receipt = serializer.save(
            created_by_type='User',
            created_by_identifier=str(self.request.user.id) if self.request.user.is_authenticated else 'Anonymous'
        )
        
        # Override authorization status if explicitly saving as draft
        if is_draft:
            receipt.authorized_status = 0
            receipt.current_authorized_status = 0
            receipt.authorized_level = 0
            receipt.current_authorized_level = 0
            receipt.save(update_fields=['authorized_status', 'current_authorized_status', 'authorized_level', 'current_authorized_level'])
        elif receipt.authorized_status == 0:
            # Safety for legacy/defaulted auth values on non-draft create
            receipt.save(force_authorization_recalc=True)
        
        receipt.update_invoice_payments()
        
        # Handle credit utilization
        if credit_amount and float(credit_amount) > 0:
            self.utilize_customer_credit(receipt, float(credit_amount))
        
        # Create customer credit for unallocated amount when approved
        if receipt.authorized_status == 2:
            receipt.create_customer_credit()
    
    def utilize_customer_credit(self, receipt, credit_amount):
        """Utilize customer credit for this receipt"""
        from decimal import Decimal
        from django.db.models import F
        
        # Get available credits for this customer
        filter_kwargs = {
            'customer_type': receipt.customer_type,
            'available_amount__gt': 0,
            'authorized_status': 2
        }
        
        if receipt.customer_type == 'RETAILER':
            filter_kwargs['retailer'] = receipt.retailer
        elif receipt.customer_type == 'DISTRIBUTOR':
            filter_kwargs['distributor'] = receipt.distributor
        elif receipt.customer_type == 'SUPERSTOCKIST':
            filter_kwargs['superstockist'] = receipt.superstockist
        
        credits = CustomerCredit.objects.filter(**filter_kwargs).order_by('created_on')
        
        remaining = Decimal(str(credit_amount))
        
        for credit in credits:
            if remaining <= 0:
                break
            
            utilize_amount = min(credit.available_amount, remaining)
            
            # Create utilization record
            from .models import CreditUtilization
            CreditUtilization.objects.create(
                credit=credit,
                receipt=receipt,
                utilized_amount=utilize_amount,
                remarks=f'Credit utilized for receipt {receipt.receipt_number}'
            )
            
            # Update available amount
            credit.available_amount -= utilize_amount
            credit.save(update_fields=['available_amount'])
            
            remaining -= utilize_amount


class PendingInvoicesForReceiptView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        customer_type = request.query_params.get('customer_type')
        customer_id = request.query_params.get('customer_id')
        
        if not customer_type or not customer_id:
            return Response(
                {'error': 'Both customer_type and customer_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        filter_kwargs = {
            'status__in': ['CONFIRMED', 'PARTIALLY_PAID'],
            'balance_amount__gt': 0,
            'authorized_status': 2
        }
        
        if customer_type == 'RETAILER':
            filter_kwargs['sales_order__retailer_id'] = customer_id
        elif customer_type == 'DISTRIBUTOR':
            filter_kwargs['sales_order__distributor_id'] = customer_id
        elif customer_type == 'SUPERSTOCKIST':
            filter_kwargs['sales_order__superstockist_id'] = customer_id
        else:
            return Response({'error': 'Invalid customer_type'}, status=status.HTTP_400_BAD_REQUEST)
        
        invoices = Invoice.filtered_objects.get_qs(
            user=request.user,
            **filter_kwargs
        ).select_related('sales_order').order_by('invoice_date')
        
        invoices = apply_company_location_filter(
            invoices, request.user,
            company_field='company', location_field='location'
        )
        
        data = [{
            'id': str(inv.id),
            'invoice_number': inv.invoice_number,
            'invoice_date': inv.invoice_date,
            'grand_total': float(inv.grand_total),
            'paid_amount': float(inv.paid_amount),
            'balance_amount': float(inv.balance_amount)
        } for inv in invoices]
        
        return Response(data)


class GenerateReceiptNumberView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        location_id = request.query_params.get('location')
        if not location_id:
            return Response(
                {'error': 'Location parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from Masters.models import Location
            location = Location.objects.get(id=location_id, is_deleted=False)
            receipt_number = Receipt.generate_receipt_number(location.code)
            return Response({'receipt_number': receipt_number})
        except Location.DoesNotExist:
            return Response({'error': 'Invalid location'}, status=status.HTTP_400_BAD_REQUEST)


class CustomerCreditBalanceView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        customer_type = request.query_params.get('customer_type')
        customer_id = request.query_params.get('customer_id')
        receipt_date = request.query_params.get('receipt_date')  # Filter by receipt date
        receipt_id = request.query_params.get('receipt_id')  # Exclude self-created credit
        
        if not customer_type or not customer_id:
            return Response(
                {'error': 'Both customer_type and customer_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        filter_kwargs = {
            'customer_type': customer_type,
            'available_amount__gt': 0,
            'authorized_status': 2
        }
        
        if customer_type == 'RETAILER':
            filter_kwargs['retailer_id'] = customer_id
        elif customer_type == 'DISTRIBUTOR':
            filter_kwargs['distributor_id'] = customer_id
        elif customer_type == 'SUPERSTOCKIST':
            filter_kwargs['superstockist_id'] = customer_id
        
        # Filter credits created BEFORE the receipt date
        if receipt_date:
            filter_kwargs['created_on__lt'] = receipt_date
        
        credits = CustomerCredit.filtered_objects.get_qs(
            user=request.user,
            **filter_kwargs
        ).order_by('created_on')
        
        # Exclude credit created by this receipt (in edit mode)
        if receipt_id:
            credits = credits.exclude(receipt_id=receipt_id)
        
        total_available = sum(c.available_amount for c in credits)
        
        return Response({
            'total_available': float(total_available),
            'credits': [{
                'id': str(c.id),
                'receipt_number': c.receipt.receipt_number if c.receipt else 'N/A',
                'credit_amount': float(c.credit_amount),
                'available_amount': float(c.available_amount),
                'created_on': c.created_on
            } for c in credits]
        })


class ReceiptLastWeekDailyTotalView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from datetime import date, timedelta
        from django.db.models.functions import TruncDate

        today = date.today()
        # Go back to last Friday: Friday=4 in weekday()
        days_since_friday = (today.weekday() - 4) % 7
        last_friday = today - timedelta(days=days_since_friday)

        queryset = Receipt.filtered_objects.get_qs(user=request.user).filter(
            receipt_date__gte=last_friday,
            receipt_date__lte=today,
        )
        queryset = apply_company_location_filter(
            queryset, request.user,
            company_field='company', location_field='location'
        )

        daily_totals = (
            queryset
            .annotate(date=TruncDate('receipt_date'))
            .values('date')
            .annotate(total_amount=Sum('total_amount'))
            .order_by('date')
        )

        # Build a dict for all days in range, default 0
        result = []
        current = last_friday
        totals_map = {entry['date']: float(entry['total_amount']) for entry in daily_totals}
        while current <= today:
            result.append({
                'date': current.isoformat(),
                'day': current.strftime('%A'),
                'total_amount': totals_map.get(current, 0),
            })
            current += timedelta(days=1)

        week_total = sum(d['total_amount'] for d in result)
        return Response({'week_start': last_friday.isoformat(), 'week_end': today.isoformat(), 'week_total': week_total, 'daily_totals': result})


class ReceiptTotalAmountView(APIView):
    permission_classes = [GetPermission('Receipts.view_receipt')]

    def get(self, request):
        queryset = Receipt.filtered_objects.get_qs(user=request.user)
        queryset = apply_company_location_filter(
            queryset, request.user,
            company_field='company', location_field='location'
        )
        total = queryset.aggregate(total_amount=Sum('total_amount'))['total_amount'] or 0
        return Response({'total_amount': float(total)})


class CustomerLedgerFilter(FilterSet):
    document_type = CharFilter(field_name='document_type')
    entry_status = CharFilter(field_name='entry_status')
    customer_type = CharFilter(field_name='customer_type')
    posting_date_from = DateFilter(field_name='posting_date', lookup_expr='gte')
    posting_date_to = DateFilter(field_name='posting_date', lookup_expr='lte')
    document_number = CharFilter(field_name='document_number', lookup_expr='icontains')

    class Meta:
        model = CustomerLedgerEntry
        fields = [
            'document_type', 'entry_status', 'customer_type',
            'posting_date_from', 'posting_date_to', 'document_number'
        ]


class CustomerLedgerListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CustomerLedgerEntrySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CustomerLedgerFilter
    search_fields = [
        'document_number', 'code', 'remarks',
        'retailer__name', 'distributor__name', 'superstockist__name'
    ]
    ordering_fields = [
        'posting_date', 'document_date', 'document_number',
        'debit_amount', 'credit_amount', 'created_on'
    ]
    ordering = ['posting_date', 'created_on']

    def get_queryset(self):
        queryset = CustomerLedgerEntry.filtered_objects.get_qs(
            user=self.request.user
        ).select_related(
            'company', 'location', 'retailer', 'distributor', 'superstockist'
        )
        queryset = apply_company_location_filter(
            queryset, self.request.user,
            company_field='company', location_field='location'
        )

        customer_type = self.request.query_params.get('customer_type')
        customer_id = self.request.query_params.get('customer_id')
        if customer_type and customer_id:
            customer_map = {
                'RETAILER': 'retailer_id',
                'DISTRIBUTOR': 'distributor_id',
                'SUPERSTOCKIST': 'superstockist_id',
            }
            customer_field = customer_map.get(customer_type)
            if not customer_field:
                return queryset.none()
            queryset = queryset.filter(**{customer_field: customer_id})
        elif customer_type or customer_id:
            return queryset.none()

        if not self.request.query_params.get('entry_status'):
            queryset = queryset.filter(entry_status='ACTIVE')

        return queryset


class CustomerLedgerSummaryView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        customer_type = request.query_params.get('customer_type')
        customer_id = request.query_params.get('customer_id')
        posting_date_from = request.query_params.get('posting_date_from')
        posting_date_to = request.query_params.get('posting_date_to')

        if not customer_type or not customer_id:
            return Response(
                {'error': 'Both customer_type and customer_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        customer_map = {
            'RETAILER': 'retailer_id',
            'DISTRIBUTOR': 'distributor_id',
            'SUPERSTOCKIST': 'superstockist_id',
        }
        customer_field = customer_map.get(customer_type)
        if not customer_field:
            return Response({'error': 'Invalid customer_type'}, status=status.HTTP_400_BAD_REQUEST)

        base_qs = CustomerLedgerEntry.filtered_objects.get_qs(
            user=request.user,
            customer_type=customer_type,
            entry_status='ACTIVE',
            **{customer_field: customer_id}
        )
        base_qs = apply_company_location_filter(
            base_qs, request.user,
            company_field='company', location_field='location'
        )

        opening_balance = Decimal('0.00')
        period_qs = base_qs
        if posting_date_from:
            opening_totals = base_qs.filter(posting_date__lt=posting_date_from).aggregate(
                total_debit=Sum('debit_amount'),
                total_credit=Sum('credit_amount')
            )
            opening_debit = opening_totals['total_debit'] or Decimal('0.00')
            opening_credit = opening_totals['total_credit'] or Decimal('0.00')
            opening_balance = opening_debit - opening_credit
            period_qs = period_qs.filter(posting_date__gte=posting_date_from)

        if posting_date_to:
            period_qs = period_qs.filter(posting_date__lte=posting_date_to)

        totals = period_qs.aggregate(
            total_debit=Sum('debit_amount'),
            total_credit=Sum('credit_amount')
        )
        period_debit = totals['total_debit'] or Decimal('0.00')
        period_credit = totals['total_credit'] or Decimal('0.00')
        closing_balance = opening_balance + period_debit - period_credit

        return Response({
            'customer_type': customer_type,
            'customer_id': customer_id,
            'posting_date_from': posting_date_from,
            'posting_date_to': posting_date_to,
            'opening_balance': float(opening_balance),
            'period_debit': float(period_debit),
            'period_credit': float(period_credit),
            'closing_balance': float(closing_balance),
            'entries_count': period_qs.count(),
        })


# ============================================================
# Receipt Report Views
# ============================================================

class ReceiptExportFilter(FilterSet):
    """FilterSet for Receipt report — frontend resolves date presets to from_date/to_date."""

    from_date = DateFilter(field_name='receipt_date', lookup_expr='gte')
    to_date = DateFilter(field_name='receipt_date', lookup_expr='lte')
    company = UUIDFilter(field_name='company_id')
    location = UUIDFilter(field_name='location_id')
    receipt_number = CharFilter(field_name='receipt_number', lookup_expr='icontains')
    payment_mode = ChoiceFilter(
        field_name='payment_mode',
        choices=[
            ('CASH', 'Cash'), ('CHEQUE', 'Cheque'), ('NEFT', 'NEFT'),
            ('RTGS', 'RTGS'), ('UPI', 'UPI'), ('CARD', 'Card'), ('CREDIT', 'Credit'),
        ],
    )
    customer_type = ChoiceFilter(
        field_name='customer_type',
        choices=[('RETAILER', 'Retailer'), ('DISTRIBUTOR', 'Distributor'), ('SUPERSTOCKIST', 'Superstockist')],
    )
    customer_id = CharFilter(method='filter_customer')
    invoice_number = CharFilter(method='filter_invoice_number')
    authorization_status = ChoiceFilter(
        field_name='authorized_status',
        choices=[
            (1, 'Pending'),
            (2, 'Approved'),
            (3, 'Rejected'),
        ],
    )
    agent = UUIDFilter(field_name='distributor__agent_id')

    class Meta:
        model = Receipt
        fields = [
            'from_date', 'to_date', 'company', 'location',
            'receipt_number', 'payment_mode',
            'customer_type', 'customer_id', 'invoice_number', 'authorization_status', 'agent',
        ]

    def filter_customer(self, queryset, name, value):
        return queryset.filter(
            Q(retailer_id=value) | Q(distributor_id=value) | Q(superstockist_id=value)
        )

    def filter_invoice_number(self, queryset, name, value):
        return queryset.filter(allocations__invoice__invoice_number__icontains=value).distinct()
