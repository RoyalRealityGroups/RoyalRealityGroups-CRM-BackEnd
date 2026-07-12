from rest_framework import serializers
from .models import DispatchPlan, DispatchItem, DispatchOrderItem
from .attachment_models import DispatchPlanAttachment
from Sales.models import SalesOrder
from Users.models import User
from uuid import UUID
from Masters.validators import validate_contact_phone


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


class DispatchOrderItemSerializer(serializers.ModelSerializer):
    """Serializer for dispatch order items with full details"""
    item_name = serializers.CharField(source='sales_order_item.item.name', read_only=True)
    item_code = serializers.CharField(source='sales_order_item.item.code', read_only=True)
    hsn_code = serializers.CharField(source='sales_order_item.item.hsn_code', read_only=True)
    unit_name = serializers.CharField(source='sales_order_item.item.unit.name', read_only=True)
    rate = serializers.DecimalField(source='sales_order_item.rate', max_digits=15, decimal_places=2, read_only=True)
    discount_amount = serializers.DecimalField(source='sales_order_item.discount_amount', max_digits=15, decimal_places=2, read_only=True)
    taxable_amount = serializers.DecimalField(source='sales_order_item.taxable_amount', max_digits=15, decimal_places=2, read_only=True)
    cgst_amount = serializers.DecimalField(source='sales_order_item.cgst_amount', max_digits=15, decimal_places=2, read_only=True)
    sgst_amount = serializers.DecimalField(source='sales_order_item.sgst_amount', max_digits=15, decimal_places=2, read_only=True)
    igst_amount = serializers.DecimalField(source='sales_order_item.igst_amount', max_digits=15, decimal_places=2, read_only=True)
    tax_amount = serializers.DecimalField(source='sales_order_item.tax_amount', max_digits=15, decimal_places=2, read_only=True)
    line_total = serializers.DecimalField(source='sales_order_item.line_total', max_digits=15, decimal_places=2, read_only=True)
    invoiced_quantity = serializers.SerializerMethodField()
    company_name = serializers.CharField(source='company.name', read_only=True)
    authorized_status_name = serializers.SerializerMethodField()
    
    class Meta:
        model = DispatchOrderItem
        fields = [
            'id', 'code', 'sales_order_item', 'quantity_ordered', 'quantity_dispatched',
            'item_name', 'item_code', 'hsn_code', 'unit_name', 'rate',
            'discount_amount', 'taxable_amount', 'cgst_amount', 'sgst_amount',
            'igst_amount', 'tax_amount', 'line_total', 'invoiced_quantity', 'company_name',
            'authorized_status', 'authorized_status_name', 'authorized_level', 'authorized_by_type',
            'authorized_by_identifier', 'authorized_on', 'current_authorized_level',
            'current_authorized_status', 'current_authorized_by_type', 'current_authorized_by_identifier',
            'current_authorized_on',
            'created_on', 'modified_on'
        ]
        read_only_fields = (
            'id', 'code', 'item_name', 'item_code', 'hsn_code', 'unit_name', 'rate',
            'discount_amount', 'taxable_amount', 'cgst_amount', 'sgst_amount',
            'igst_amount', 'tax_amount', 'line_total', 'invoiced_quantity',
            'authorized_status', 'authorized_status_name', 'authorized_level', 'authorized_by_type',
            'authorized_by_identifier', 'authorized_on', 'current_authorized_level',
            'current_authorized_status', 'current_authorized_by_type', 'current_authorized_by_identifier',
            'current_authorized_on',
            'created_on', 'modified_on'
        )
    
    def get_invoiced_quantity(self, obj):
        return float(obj.get_invoiced_quantity())
    
    def get_authorized_status_name(self, obj):
        return obj.get_authorized_status_display()


class DispatchItemSerializer(serializers.ModelSerializer):
    sales_order_number = serializers.CharField(source='sales_order.order_number', read_only=True)
    order_date = serializers.DateField(source='sales_order.order_date', read_only=True)
    customer_name = serializers.CharField(source='sales_order.get_customer_name', read_only=True)
    customer_type = serializers.CharField(source='sales_order.customer_type', read_only=True)
    shipping_address = serializers.CharField(source='sales_order.shipping_address', read_only=True)
    shipping_state_name = serializers.CharField(source='sales_order.shipping_state.name', read_only=True)
    shipping_state_id = serializers.UUIDField(source='sales_order.shipping_state_id', read_only=True)
    shipping_city_name = serializers.CharField(source='sales_order.shipping_city.name', read_only=True)
    shipping_city_id = serializers.UUIDField(source='sales_order.shipping_city_id', read_only=True)
    shipping_area_name = serializers.CharField(source='sales_order.shipping_area.name', read_only=True)
    shipping_area_id = serializers.UUIDField(source='sales_order.shipping_area_id', read_only=True)
    order_value = serializers.DecimalField(source='sales_order.grand_total', max_digits=15, decimal_places=2, read_only=True)
    remaining_quantity = serializers.ReadOnlyField()
    dispatch_percentage = serializers.ReadOnlyField()
    sales_order_item = serializers.SerializerMethodField()
    order_items = DispatchOrderItemSerializer(many=True, read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    authorized_status_name = serializers.SerializerMethodField()
    
    class Meta:
        model = DispatchItem
        fields = [
            'id', 'code', 'sales_order', 'sales_order_item', 'sales_order_number', 'order_date', 'customer_name', 'customer_type',
            'shipping_address', 'shipping_state_name','shipping_state_id', 'shipping_city_name', 'shipping_city_id', 'shipping_area_name', 'shipping_area_id', 'order_value', 'company_name',
            'quantity_ordered', 'quantity_dispatched', 'remaining_quantity', 'dispatch_percentage',
            'delivery_sequence', 'loading_sequence', 'unloading_sequence', 'status',
            'estimated_delivery_time', 'actual_delivery_time', 'delivery_notes',
            'delivered_by', 'received_by', 'order_items',
            'authorized_status', 'authorized_status_name', 'authorized_level', 'authorized_by_type',
            'authorized_by_identifier', 'authorized_on', 'current_authorized_level',
            'current_authorized_status', 'current_authorized_by_type', 'current_authorized_by_identifier',
            'current_authorized_on',
            'created_on', 'modified_on'
        ]
        read_only_fields = (
            'id', 'code', 'sales_order_number', 'order_date', 'customer_name', 'customer_type',
            'shipping_address', 'shipping_state_name','shipping_state_id', 'shipping_city_name', 'shipping_city_id', 'shipping_area_name', 'shipping_area_id', 'order_value',
            'remaining_quantity', 'dispatch_percentage',
            'order_items',
            'authorized_status', 'authorized_status_name', 'authorized_level', 'authorized_by_type',
            'authorized_by_identifier', 'authorized_on', 'current_authorized_level',
            'current_authorized_status', 'current_authorized_by_type', 'current_authorized_by_identifier',
            'current_authorized_on',
            'created_on', 'modified_on'
        )
    
    def get_sales_order_item(self, obj):
        # Get the first order item if this is item-level dispatch
        order_item = obj.order_items.first()
        if order_item and order_item.sales_order_item:
            return order_item.sales_order_item.id
        return None
    
    def get_authorized_status_name(self, obj):
        return obj.get_authorized_status_display()


class DispatchPlanAttachmentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = DispatchPlanAttachment
        fields = ['id', 'attachment_type', 'file', 'file_url', 'original_filename', 'description', 'created_on']
        read_only_fields = ['id', 'file_url', 'created_on']

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url if obj.file else None


class DispatchPlanSerializer(serializers.ModelSerializer):
    items = DispatchItemSerializer(many=True, read_only=True)
    attachments = DispatchPlanAttachmentSerializer(many=True, read_only=True)
    location_name = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    route_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField(read_only=True)
    authorized_status_name = serializers.SerializerMethodField()
    pending_approver_names = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = DispatchPlan
        fields = [
            'id', 'code', 'dispatch_number', 'dispatch_date', 'planned_dispatch_date',
            'location', 'location_name', 'company_name', 'vehicle_number', 'vehicle_type', 'vehicle_capacity',
            'driver_name', 'driver_phone', 'driver_license', 'route', 'route_name', 'lr_no', 'stock_insurance',
            'status', 'total_orders', 'total_weight', 'total_volume', 'total_value',
            'estimated_start_time', 'estimated_end_time', 'actual_start_time', 'actual_end_time',
            'remarks', 'items', 'attachments',
            'authorized_status', 'authorized_status_name', 'authorized_level', 'authorized_by_type',
            'authorized_by_identifier', 'authorized_on', 'current_authorized_level',
            'current_authorized_status', 'current_authorized_by_type', 'current_authorized_by_identifier',
            'current_authorized_on', 'pending_approver_names',
            'created_by_type', 'created_by_identifier', 'created_by_name',
            'created_on', 'modified_on'
        ]
        read_only_fields = ['id', 'code', 'location_name', 'route_name', 'total_orders', 'total_value',
                            'attachments',
                            'authorized_status', 'authorized_status_name', 'authorized_level', 'authorized_by_type',
                            'authorized_by_identifier', 'authorized_on', 'current_authorized_level',
                            'current_authorized_status', 'current_authorized_by_type', 'current_authorized_by_identifier',
                            'current_authorized_on', 'pending_approver_names',
                            'created_by_type', 'created_by_identifier', 'created_by_name',
                            'created_on', 'modified_on']
    
    def validate_stock_insurance(self, value):
        if value is None:
            raise serializers.ValidationError("Stock insurance selection is required")
        return value

    def validate_driver_phone(self, value):
        try:
            return validate_contact_phone(value)
        except Exception as exc:
            raise serializers.ValidationError(str(exc))
    
    def get_location_name(self, obj):
        return obj.location.name if obj.location else None

    def get_company_name(self, obj):
        return obj.location.company.name if obj.location and obj.location.company else None

    def get_route_name(self, obj):
        return obj.route.name if obj.route else None
    
    def get_authorized_status_name(self, obj):
        return obj.get_authorized_status_display()

    def get_created_by_name(self, obj):
        return get_creator_display_name(obj.created_by_type, obj.created_by_identifier)
    
    def get_pending_approver_names(self, obj):
        """Get pending approver names"""
        from Core.Users.serializers import get_pending_approver_names
        result = get_pending_approver_names(obj)
        if obj.authorized_status == 1:
            return result if result else 'TEST: No approvers found'
        return result


class DispatchPlanListSerializer(serializers.ModelSerializer):
    location_name = serializers.SerializerMethodField()
    items_count = serializers.IntegerField(source='items.count', read_only=True)
    authorized_status_name = serializers.SerializerMethodField()
    pending_approver_names = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = DispatchPlan
        fields = [
            'id', 'code', 'dispatch_number', 'dispatch_date', 'planned_dispatch_date',
            'location_name', 'status', 'total_orders', 'total_value',
            'items_count', 'vehicle_number', 'driver_name', 'lr_no', 'stock_insurance',
            'authorized_status', 'authorized_status_name', 'authorized_level', 'authorized_by_type',
            'authorized_by_identifier', 'authorized_on', 'current_authorized_level',
            'current_authorized_status', 'current_authorized_by_type', 'current_authorized_by_identifier',
            'current_authorized_on', 'pending_approver_names'
        ]
        read_only_fields = fields

    def get_location_name(self, obj):
        return obj.location.name if obj.location else None

    def get_authorized_status_name(self, obj):
        return obj.get_authorized_status_display()
    
    def get_pending_approver_names(self, obj):
        """Get pending approver names"""
        from Core.Users.serializers import get_pending_approver_names
        result = get_pending_approver_names(obj)
        if obj.authorized_status == 1:
            return result if result else 'TEST: No approvers found'
        return result


class SalesOrderForDispatchSerializer(serializers.ModelSerializer):
    """Serializer for sales orders available for dispatch"""
    customer_name = serializers.CharField(source='get_customer_name', read_only=True)
    customer_id = serializers.SerializerMethodField()
    shipping_area = serializers.CharField(source='shipping_area.id', read_only=True)
    shipping_state_name = serializers.CharField(source='shipping_state.name', read_only=True)
    shipping_city_name = serializers.CharField(source='shipping_city.name', read_only=True)
    shipping_area_name = serializers.CharField(source='shipping_area.name', read_only=True)
    total_quantity = serializers.SerializerMethodField()
    dispatched_quantity = serializers.SerializerMethodField()
    remaining_quantity = serializers.SerializerMethodField()
    items = serializers.SerializerMethodField()
    
    class Meta:
        model = SalesOrder
        fields = [
            'id', 'order_number', 'order_date', 'customer_type', 'customer_id', 'customer_name',
            'shipping_area',
            'shipping_address', 'shipping_state_name', 'shipping_city_name', 'shipping_area_name',
            'grand_total', 'total_quantity', 'dispatched_quantity', 'remaining_quantity', 'items'
        ]

    def get_customer_id(self, obj):
        if obj.customer_type == 'RETAILER' and obj.retailer_id:
            return str(obj.retailer_id)
        if obj.customer_type == 'DISTRIBUTOR' and obj.distributor_id:
            return str(obj.distributor_id)
        if obj.customer_type == 'SUPERSTOCKIST' and obj.superstockist_id:
            return str(obj.superstockist_id)
        return None
    
    def get_total_quantity(self, obj):
        return sum(item.quantity for item in obj.items.all())
    
    def get_dispatched_quantity(self, obj):
        from django.db.models import Q
        excluded_q = Q(dispatch_plan__status='CANCELLED') | Q(dispatch_plan__authorized_status=3)
        dispatch_plan_id = self.context.get('dispatch_plan_id')
        if dispatch_plan_id:
            return sum(
                dispatch_item.quantity_dispatched 
                for dispatch_item in obj.dispatch_items.exclude(
                    excluded_q
                ).exclude(dispatch_plan_id=dispatch_plan_id)
            )
        else:
            return sum(
                dispatch_item.quantity_dispatched 
                for dispatch_item in obj.dispatch_items.exclude(excluded_q)
            )
    
    def get_remaining_quantity(self, obj):
        return self.get_total_quantity(obj) - self.get_dispatched_quantity(obj)
    
    def get_items(self, obj):
        from django.db.models import Q
        excluded_q = Q(dispatch_item__dispatch_plan__status='CANCELLED') | Q(dispatch_item__dispatch_plan__authorized_status=3)
        dispatch_plan_id = self.context.get('dispatch_plan_id')
        items_data = []
        
        for item in obj.items.all():
            if dispatch_plan_id:
                item_dispatched = sum(
                    doi.quantity_dispatched for doi in item.dispatch_order_items.exclude(
                        excluded_q
                    ).exclude(dispatch_item__dispatch_plan_id=dispatch_plan_id)
                )
            else:
                item_dispatched = sum(
                    doi.quantity_dispatched for doi in item.dispatch_order_items.exclude(
                        excluded_q
                    )
                )
            
            remaining_qty = item.quantity - item_dispatched
            
            # Only include items with remaining quantity > 0
            if remaining_qty > 0:
                items_data.append({
                    'id': item.id,
                    'code': item.code,
                    'company': str(item.company_id) if item.company_id else None,
                    'company_name': item.company.name if item.company else None,
                    'item_name': item.item.name,
                    'item_code': item.item.code,
                    'quantity_ordered': item.quantity,
                    'dispatched_quantity': item_dispatched,
                    'remaining_quantity': remaining_qty,
                    'unit_price': item.rate,
                    'is_scheme_item': item.is_scheme_item,
                })
        return items_data


class DispatchPlanStatusCountSerializer(serializers.Serializer):
    DRAFT = serializers.IntegerField(read_only=True, default=0)
    PENDING = serializers.IntegerField(read_only=True, default=0)
    CONFIRMED = serializers.IntegerField(read_only=True, default=0)
    DELIVERED = serializers.IntegerField(read_only=True, default=0)
    CANCELLED = serializers.IntegerField(read_only=True, default=0)
    total = serializers.IntegerField(read_only=True, default=0)


# ============================================================
# Dispatch Planning Report Serializers
# Product-wise dispatch planning report
# ============================================================

class DispatchPlanningReportSerializer(serializers.Serializer):
    """
    Product-wise Dispatch Planning Report Serializer
    Each row represents one product from a dispatch plan
    """
    # Unique identifier for the row
    id = serializers.SerializerMethodField()
    
    # Dispatch Plan Information
    dispatch_plan_id = serializers.UUIDField()
    dispatch_number = serializers.CharField()
    dispatch_date = serializers.DateField()
    planned_dispatch_date = serializers.DateField()
    
    # Sales Order Information
    sales_order_id = serializers.UUIDField()
    sales_order_number = serializers.CharField()
    sales_order_date = serializers.DateField()
    
    # Customer Information
    customer_name = serializers.CharField()
    customer_type = serializers.CharField()
    customer_type_code = serializers.CharField()
    
    # Product Information (ONE product per row, null for order-level fallback)
    product_id = serializers.UUIDField(allow_null=True)
    product_code = serializers.CharField(allow_blank=True)
    product_name = serializers.CharField()
    quantity_ordered = serializers.DecimalField(max_digits=15, decimal_places=3)
    quantity_dispatched = serializers.DecimalField(max_digits=15, decimal_places=3)
    
    # Location Information
    location_name = serializers.CharField(allow_null=True)
    location_code = serializers.CharField(allow_null=True)
    
    # Route Information
    route_name = serializers.CharField(allow_null=True)
    route_code = serializers.CharField(allow_null=True)
    
    # Customer Location
    state = serializers.CharField()
    state_id = serializers.UUIDField()
    city = serializers.CharField()
    city_id = serializers.UUIDField()
    area = serializers.CharField(allow_null=True)
    area_id = serializers.UUIDField(allow_null=True)
    
    # Status Information
    dispatch_status = serializers.CharField()
    dispatch_status_code = serializers.CharField()
    item_status = serializers.CharField()
    item_status_code = serializers.CharField()
    
    # Vehicle Information
    vehicle_number = serializers.CharField(allow_null=True)
    driver_name = serializers.CharField(allow_null=True)
    driver_phone = serializers.CharField(allow_null=True)
    agent_name = serializers.CharField(allow_null=True)
    
    # Delivery Information
    delivery_sequence = serializers.IntegerField()
    estimated_delivery_time = serializers.DateTimeField(allow_null=True)
    actual_delivery_time = serializers.DateTimeField(allow_null=True)
    
    # Authorization Information
    authorization_status = serializers.CharField()
    authorization_status_code = serializers.IntegerField()
    
    def get_id(self, obj):
        """Generate unique ID for each row using the line-item id to avoid collisions"""
        return f"{obj['dispatch_plan_id']}_{obj['dispatch_order_item_id']}"
