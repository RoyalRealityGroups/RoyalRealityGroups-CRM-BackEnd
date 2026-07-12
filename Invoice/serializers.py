from rest_framework import serializers
from .models import Invoice, InvoiceItem, Payment
from Sales.models import SalesOrder
from Dispatch.models import DispatchPlan
from Users.models import User
from uuid import UUID


def get_creator_display_name(created_by_type, created_by_identifier):
    identifier = (created_by_identifier or '').strip()
    if not identifier:
        return 'System'

    lowered_identifier = identifier.lower()
    if lowered_identifier == 'anonymous':
        return 'Anonymous'
    if lowered_identifier == 'system':
        return 'System'

    creator = None
    try:
        creator = User.objects.filter(id=UUID(identifier)).only('first_name', 'last_name', 'username').first()
    except (TypeError, ValueError, AttributeError):
        creator = None

    if creator:
        full_name = f"{creator.first_name} {creator.last_name}".strip()
        if full_name:
            return full_name
        if creator.username:
            return creator.username

    if created_by_type:
        return f"{created_by_type}: {identifier}"
    return identifier


class InvoiceItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='sales_order_item.item.name', read_only=True)
    item_code = serializers.CharField(source='sales_order_item.item.code', read_only=True)
    category_name = serializers.CharField(source='sales_order_item.item.category.name', read_only=True)
    hsn_code = serializers.CharField(source='sales_order_item.item.hsn_code', read_only=True)
    unit_name = serializers.CharField(source='sales_order_item.item.base_uom.name', read_only=True)
    authorized_status_name = serializers.SerializerMethodField()
    
    class Meta:
        model = InvoiceItem
        fields = [
            'id', 'code', 'sales_order_item', 'item_name', 'item_code', 'category_name', 'hsn_code', 'unit_name',
            'quantity', 'rate', 'discount_amount', 'taxable_amount',
            'cgst_rate', 'cgst_amount', 'sgst_rate', 'sgst_amount',
            'igst_rate', 'igst_amount', 'cess_rate', 'cess_amount',
            'tax_amount', 'line_total',
            'authorized_status', 'authorized_status_name', 'authorized_level', 'authorized_by_type',
            'authorized_by_identifier', 'authorized_on', 'current_authorized_level',
            'current_authorized_status', 'current_authorized_by_type', 'current_authorized_by_identifier',
            'current_authorized_on',
            'created_on', 'modified_on'
        ]
        read_only_fields = (
            'id', 'code', 'item_name', 'item_code', 'category_name', 'hsn_code', 'unit_name',
            'discount_amount', 'taxable_amount',
            'cgst_rate', 'cgst_amount', 'sgst_rate', 'sgst_amount',
            'igst_rate', 'igst_amount', 'cess_rate', 'cess_amount',
            'tax_amount', 'line_total',
            'authorized_status', 'authorized_status_name', 'authorized_level', 'authorized_by_type',
            'authorized_by_identifier', 'authorized_on', 'current_authorized_level',
            'current_authorized_status', 'current_authorized_by_type', 'current_authorized_by_identifier',
            'current_authorized_on',
            'created_on', 'modified_on'
        )

    def get_authorized_status_name(self, obj):
        return obj.get_authorized_status_display()


class PaymentSerializer(serializers.ModelSerializer):
    authorized_status_name = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            'id', 'code', 'payment_date', 'payment_mode', 'amount',
            'reference_number', 'bank_name', 'remarks',
            'authorized_status', 'authorized_status_name', 'authorized_level', 'authorized_by_type',
            'authorized_by_identifier', 'authorized_on', 'current_authorized_level',
            'current_authorized_status', 'current_authorized_by_type', 'current_authorized_by_identifier',
            'current_authorized_on',
            'created_on', 'modified_on'
        ]
        read_only_fields = (
            'id', 'code', 'authorized_status', 'authorized_status_name', 'authorized_level', 'authorized_by_type',
            'authorized_by_identifier', 'authorized_on', 'current_authorized_level',
            'current_authorized_status', 'current_authorized_by_type', 'current_authorized_by_identifier',
            'current_authorized_on',
            'created_on', 'modified_on'
        )

    def get_authorized_status_name(self, obj):
        return obj.get_authorized_status_display()


class InvoiceListSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    customer_name = serializers.CharField(source='sales_order.get_customer_name', read_only=True)
    order_number = serializers.CharField(source='sales_order.order_number', read_only=True)
    items_count = serializers.IntegerField(source='items.count', read_only=True)
    authorized_status_name = serializers.SerializerMethodField()
    pending_approver_names = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'code', 'invoice_number', 'invoice_date', 'due_date',
            'company_name', 'location_name', 'customer_name', 'order_number',
            'source_type', 'status', 'pod_status', 'grand_total', 'paid_amount', 'balance_amount',
            'items_count',
            'authorized_status', 'authorized_status_name', 'authorized_level', 'authorized_by_type',
            'authorized_by_identifier', 'authorized_on', 'current_authorized_level',
            'current_authorized_status', 'current_authorized_by_type', 'current_authorized_by_identifier',
            'current_authorized_on', 'pending_approver_names'
        ]
        read_only_fields = fields

    def get_authorized_status_name(self, obj):
        return obj.get_authorized_status_display()
    
    def get_pending_approver_names(self, obj):
        """Get pending approver names"""
        from Core.Users.serializers import get_pending_approver_names
        result = get_pending_approver_names(obj)
        if obj.authorized_status == 1:
            return result if result else 'TEST: No approvers found'
        return result


class InvoiceDetailSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    location_code = serializers.CharField(source='location.code', read_only=True)
    customer_name = serializers.CharField(source='sales_order.get_customer_name', read_only=True)
    customer_type = serializers.CharField(source='sales_order.customer_type', read_only=True)
    customer_id = serializers.SerializerMethodField()
    order_number = serializers.CharField(source='sales_order.order_number', read_only=True)
    order_date = serializers.DateField(source='sales_order.order_date', read_only=True)
    dispatch_number = serializers.CharField(source='dispatch_plan.dispatch_number', read_only=True)
    tax_type = serializers.CharField(source='sales_order.tax_type', read_only=True)
    
    # Customer details
    billing_address = serializers.CharField(source='sales_order.billing_address', read_only=True)
    billing_state = serializers.CharField(source='sales_order.billing_state.name', read_only=True)
    billing_city = serializers.CharField(source='sales_order.billing_city.name', read_only=True)
    shipping_address = serializers.CharField(source='sales_order.shipping_address', read_only=True)
    shipping_state = serializers.CharField(source='sales_order.shipping_state.name', read_only=True)
    shipping_city = serializers.CharField(source='sales_order.shipping_city.name', read_only=True)
    created_by_name = serializers.SerializerMethodField(read_only=True)
    authorized_status_name = serializers.SerializerMethodField()
    pending_approver_names = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'code', 'invoice_number', 'invoice_date', 'due_date',
            'source_type', 'sales_order', 'dispatch_plan', 'order_number', 'order_date', 'dispatch_number',
            'company', 'company_name', 'location', 'location_name', 'location_code',
            'customer_name', 'customer_type', 'customer_id', 'tax_type',
            'billing_address', 'billing_state', 'billing_city',
            'shipping_address', 'shipping_state', 'shipping_city',
            'status', 'subtotal', 'discount_amount', 'taxable_amount', 'tax_amount',
            'freight_charges', 'other_charges', 'round_off', 'grand_total',
            'paid_amount', 'balance_amount', 'remarks',
            'authorized_status', 'authorized_status_name', 'authorized_level', 'authorized_by_type',
            'authorized_by_identifier', 'authorized_on', 'current_authorized_level',
            'current_authorized_status', 'current_authorized_by_type', 'current_authorized_by_identifier',
            'current_authorized_on', 'pending_approver_names',
            'items', 'payments',
            'created_by_type', 'created_by_identifier', 'created_by_name',
            'created_on', 'modified_on'
        ]
        read_only_fields = (
            'id', 'code', 'invoice_number', 'invoice_date', 'dispatch_number',
            'company_name', 'location_name', 'location_code',
            'customer_name', 'customer_type', 'customer_id', 'tax_type',
            'billing_state', 'billing_city', 'shipping_state', 'shipping_city',
            'paid_amount', 'balance_amount',
            'authorized_status', 'authorized_status_name', 'authorized_level', 'authorized_by_type',
            'authorized_by_identifier', 'authorized_on', 'current_authorized_level',
            'current_authorized_status', 'current_authorized_by_type', 'current_authorized_by_identifier',
            'current_authorized_on', 'pending_approver_names',
            'items', 'payments',
            'created_by_type', 'created_by_identifier', 'created_by_name',
            'created_on', 'modified_on'
        )
    
    def get_customer_id(self, obj):
        """Get customer ID based on customer type"""
        if obj.sales_order.customer_type == 'RETAILER':
            return obj.sales_order.retailer_id
        elif obj.sales_order.customer_type == 'DISTRIBUTOR':
            return obj.sales_order.distributor_id
        elif obj.sales_order.customer_type == 'SUPERSTOCKIST':
            return obj.sales_order.superstockist_id
        return None
    
    def get_authorized_status_name(self, obj):
        return obj.get_authorized_status_display()

    def get_created_by_name(self, obj):
        return get_creator_display_name(obj.created_by_type, obj.created_by_identifier)
    
    def get_pending_approver_names(self, obj):
        """Get pending approver names"""
        from Core.Users.serializers import get_pending_approver_names
        return get_pending_approver_names(obj)


class DispatchPlanForInvoiceSerializer(serializers.ModelSerializer):
    """Serializer for dispatch plans available for invoicing"""
    customer_name = serializers.CharField(source='items.first.sales_order.get_customer_name', read_only=True)
    order_number = serializers.CharField(source='items.first.sales_order.order_number', read_only=True)
    order_date = serializers.DateField(source='items.first.sales_order.order_date', read_only=True)
    total_quantity = serializers.SerializerMethodField()
    total_amount = serializers.DecimalField(source='total_value', max_digits=15, decimal_places=2, read_only=True)
    invoiced = serializers.SerializerMethodField()
    
    class Meta:
        model = DispatchPlan
        fields = [
            'id', 'dispatch_number', 'dispatch_date', 'order_number', 'order_date',
            'customer_name', 'status', 'total_quantity', 'total_amount', 'total_value', 'invoiced'
        ]
    
    def get_total_quantity(self, obj):
        from django.db.models import Sum
        return obj.items.aggregate(total=Sum('quantity_dispatched'))['total'] or 0
    
    def get_invoiced(self, obj):
        return obj.invoices.filter(status__in=['CONFIRMED', 'PAID', 'PARTIALLY_PAID']).exists()


class PendingInvoiceSerializer(serializers.ModelSerializer):
    """Serializer for displaying pending invoices for a customer"""
    invoice_date_formatted = serializers.DateField(source='invoice_date', read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'invoice_date', 'invoice_date_formatted',
            'grand_total', 'balance_amount'
        ]
        read_only_fields = fields


class SalesOrderForInvoiceSerializer(serializers.ModelSerializer):
    """Serializer for sales orders available for invoicing"""
    customer_name = serializers.CharField(source='get_customer_name', read_only=True)
    total_quantity = serializers.SerializerMethodField()
    invoiced = serializers.SerializerMethodField()
    items = serializers.SerializerMethodField()
    billing_address = serializers.CharField(read_only=True)
    shipping_address = serializers.CharField(read_only=True)
    credit_days = serializers.SerializerMethodField()
    credit_limit = serializers.SerializerMethodField()
    dispatch_number = serializers.SerializerMethodField()
    
    class Meta:
        model = SalesOrder
        fields = [
            'id', 'order_number', 'order_date', 'customer_type', 'customer_name',
            'status', 'total_quantity', 'grand_total', 'invoiced', 'items', 'tax_type',
            'billing_address', 'shipping_address', 'credit_days', 'credit_limit',
            'dispatch_number'
        ]
    
    def get_total_quantity(self, obj):
        from django.db.models import Sum
        source_type = self.context.get('source_type')
        
        if source_type == 'DISPATCH':
            # Return total available dispatched quantity
            from Dispatch.models import DispatchOrderItem
            total_dispatched = 0
            for item in obj.items.all():
                dispatched_qty = DispatchOrderItem.objects.filter(
                    sales_order_item=item,
                    dispatch_item__dispatch_plan__status__in=['CONFIRMED', 'DELIVERED'],
                    dispatch_item__dispatch_plan__authorized_status=2
                ).aggregate(total=Sum('quantity_dispatched'))['total'] or 0
                
                invoiced_qty = InvoiceItem.objects.filter(
                    sales_order_item=item,
                    invoice__source_type='DISPATCH',
                    invoice__status__in=['DRAFT', 'CONFIRMED', 'PAID', 'PARTIALLY_PAID']
                ).aggregate(total=Sum('quantity'))['total'] or 0
                
                total_dispatched += (dispatched_qty - invoiced_qty)
            return total_dispatched
        else:
            # Return order quantity
            return obj.items.aggregate(total=Sum('quantity'))['total'] or 0
    
    def get_invoiced(self, obj):
        return obj.invoices.filter(
            source_type='ORDER',
            status__in=['CONFIRMED', 'PAID', 'PARTIALLY_PAID']
        ).exists()
    
    def get_credit_days(self, obj):
        """Get credit days from customer"""
        if obj.customer_type == 'RETAILER' and obj.retailer:
            return obj.retailer.credit_days
        elif obj.customer_type == 'DISTRIBUTOR' and obj.distributor:
            return obj.distributor.credit_days
        elif obj.customer_type == 'SUPERSTOCKIST' and obj.superstockist:
            return obj.superstockist.credit_days
        return 0
    
    def get_credit_limit(self, obj):
        """Get credit limit from customer"""
        if obj.customer_type == 'RETAILER' and obj.retailer:
            return float(obj.retailer.credit_limit)
        elif obj.customer_type == 'DISTRIBUTOR' and obj.distributor:
            return float(obj.distributor.credit_limit)
        elif obj.customer_type == 'SUPERSTOCKIST' and obj.superstockist:
            return float(obj.superstockist.credit_limit)
        return 0
    
    def get_dispatch_number(self, obj):
        """Get dispatch numbers where this sales order is tagged"""
        if self.context.get('source_type') != 'DISPATCH':
            return []
        from Dispatch.models import DispatchItem
        return list(
            DispatchItem.objects.filter(
                sales_order=obj,
                dispatch_plan__status__in=['CONFIRMED', 'DELIVERED']
            ).values_list('dispatch_plan__dispatch_number', flat=True).distinct()
        )
    
    def get_items(self, obj):
        """Return items with dispatch and invoice quantities for DISPATCH source type"""
        source_type = self.context.get('source_type')
        
        if source_type == 'DISPATCH':
            from django.db.models import Sum, Q
            from Dispatch.models import DispatchOrderItem
            
            items_data = []
            for item in obj.items.all():
                # Calculate total dispatched quantity
                dispatch_order_items = DispatchOrderItem.objects.filter(
                    sales_order_item=item,
                    dispatch_item__dispatch_plan__status__in=['CONFIRMED', 'DELIVERED']
                ).select_related('dispatch_item__dispatch_plan')
                
                dispatched_qty = sum(doi.quantity_dispatched for doi in dispatch_order_items)
                
                # Collect dispatch numbers for this item
                dispatch_number = list(
                    dispatch_order_items.values_list(
                        'dispatch_item__dispatch_plan__dispatch_number', flat=True
                    ).distinct()
                )
                
                # Calculate invoiced quantity from DISPATCH source
                invoiced_qty = InvoiceItem.objects.filter(
                    sales_order_item=item,
                    invoice__source_type='DISPATCH',
                    invoice__status__in=['CONFIRMED', 'PAID', 'PARTIALLY_PAID']
                ).aggregate(total=Sum('quantity'))['total'] or 0
                
                available_qty = dispatched_qty - invoiced_qty
                
                if available_qty > 0:
                    # Calculate proportional amounts based on available quantity
                    ratio = available_qty / item.quantity
                    
                    items_data.append({
                        'id': item.id,
                        'code': item.code,
                        'company': str(item.company_id) if item.company_id else None,
                        'company_name': item.company.name if item.company else None,
                        'item_name': item.item.name,
                        'item_code': item.item.code,
                        'category_name': item.item.category.name if item.item.category else None,
                        'hsn_code': item.item.hsn_code,
                        'unit_name': item.item.base_uom.name if item.item.base_uom else None,
                        'quantity': item.quantity,
                        'dispatched_quantity': available_qty,
                        'dispatch_number': dispatch_number,
                        'rate': float(item.rate),
                        'discount_amount': float(item.discount_amount * ratio),
                        'taxable_amount': float(item.taxable_amount * ratio),
                        'cgst_rate': float(item.cgst_rate),
                        'cgst_amount': float(item.cgst_amount * ratio),
                        'sgst_rate': float(item.sgst_rate),
                        'sgst_amount': float(item.sgst_amount * ratio),
                        'igst_rate': float(item.igst_rate),
                        'igst_amount': float(item.igst_amount * ratio),
                        'tax_amount': float(item.tax_amount * ratio),
                        'line_total': float(item.line_total * ratio),
                        'is_scheme_item': item.is_scheme_item,
                    })
            return items_data
        else:
            # For ORDER type, return all items
            items_data = []
            for item in obj.items.all():
                items_data.append({
                    'id': item.id,
                    'code': item.code,
                    'company': str(item.company_id) if item.company_id else None,
                    'company_name': item.company.name if item.company else None,
                    'item_name': item.item.name,
                    'item_code': item.item.code,
                    'category_name': item.item.category.name if item.item.category else None,
                    'hsn_code': item.item.hsn_code,
                    'unit_name': item.item.base_uom.name if item.item.base_uom else None,
                    'quantity': item.quantity,
                    'rate': float(item.rate),
                    'discount_amount': float(item.discount_amount),
                    'taxable_amount': float(item.taxable_amount),
                    'cgst_rate': float(item.cgst_rate),
                    'cgst_amount': float(item.cgst_amount),
                    'sgst_rate': float(item.sgst_rate),
                    'sgst_amount': float(item.sgst_amount),
                    'igst_rate': float(item.igst_rate),
                    'igst_amount': float(item.igst_amount),
                    'tax_amount': float(item.tax_amount),
                    'line_total': float(item.line_total),
                    'is_scheme_item': item.is_scheme_item,
                })
            return items_data



class InvoiceStatusCountSerializer(serializers.Serializer):
    """Serializer for invoice status counts"""
    DRAFT = serializers.IntegerField(read_only=True, default=0)
    PENDING = serializers.IntegerField(read_only=True, default=0)
    CONFIRMED = serializers.IntegerField(read_only=True, default=0)
    PAID = serializers.IntegerField(read_only=True, default=0)
    PARTIALLY_PAID = serializers.IntegerField(read_only=True, default=0)
    CANCELLED = serializers.IntegerField(read_only=True, default=0)
    total = serializers.IntegerField(read_only=True, default=0)


# ============================================================
# Invoice Report Serializers
# ============================================================

class InvoiceReportSerializer(serializers.Serializer):
    """
    Invoice Report Serializer.
    Each row represents one invoice with all relevant details.
    """
    # Invoice Information
    id = serializers.UUIDField()
    invoice_number = serializers.CharField()
    invoice_date = serializers.DateField()
    due_date = serializers.DateField()

    # Source Information
    source_type = serializers.CharField()
    source_type_display = serializers.CharField()
    dispatch_number = serializers.CharField(allow_null=True)
    sales_order_number = serializers.CharField()

    # Customer Information
    customer_name = serializers.CharField()
    customer_type = serializers.CharField()
    customer_type_code = serializers.CharField()

    # Financial Information
    subtotal = serializers.DecimalField(max_digits=15, decimal_places=2)
    discount_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    taxable_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    tax_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    freight_charges = serializers.DecimalField(max_digits=10, decimal_places=2)
    other_charges = serializers.DecimalField(max_digits=10, decimal_places=2)
    round_off = serializers.DecimalField(max_digits=10, decimal_places=2)
    grand_total = serializers.DecimalField(max_digits=15, decimal_places=2)

    # Payment Information
    paid_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    balance_amount = serializers.DecimalField(max_digits=15, decimal_places=2)

    # Status Information
    status = serializers.CharField()
    status_code = serializers.CharField()
    pod_status = serializers.CharField()
    pod_status_code = serializers.CharField()
    
    # Authorization Information
    authorization_status = serializers.IntegerField(allow_null=True)
    authorization_status_code = serializers.CharField(allow_null=True)
    authorization_level = serializers.IntegerField(allow_null=True)
    current_authorized_level = serializers.IntegerField(allow_null=True)

    # Location Information
    country = serializers.CharField(allow_null=True)
    state = serializers.CharField()
    state_id = serializers.UUIDField()
    district = serializers.CharField(allow_null=True)
    mandal = serializers.CharField(allow_null=True)
    city = serializers.CharField()
    city_id = serializers.UUIDField()
    area = serializers.CharField(allow_null=True)
    area_id = serializers.UUIDField(allow_null=True)

    # Company Information
    company_name = serializers.CharField()
    location_name = serializers.CharField(allow_null=True)
    agent_name = serializers.CharField(allow_null=True)

    # Timestamps
    created_on = serializers.DateTimeField()
    modified_on = serializers.DateTimeField()
