from rest_framework import serializers
from django.db.models import Sum
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError
from .models import SalesOrder, SalesOrderItem, SalesOrderHistory, SalesOrderScheme, SalesOrderItemScheme
from .attachment_serializers import SalesOrderAttachmentSerializer
from Masters.scheme_engine import SchemeEngine


class SalesOrderItemSerializer(serializers.ModelSerializer):
    """Serializer for Sales Order line items"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    item_code = serializers.CharField(source='item.code', read_only=True)
    item_name = serializers.CharField(source='item.name', read_only=True)
    hsn_code = serializers.CharField(source='item.hsn_code', read_only=True)
    uom_name = serializers.CharField(source='item.base_uom.name', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    invoiced_quantity = serializers.SerializerMethodField()
    authorized_status_name = serializers.SerializerMethodField()
    scheme_discount_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = SalesOrderItem
        fields = (
            'id', 'code', 'company', 'company_name', 'category', 'category_name', 'item', 'item_code', 'item_name', 'hsn_code', 'uom_name',
            'quantity', 'free_quantity',
            'pb_rate', 'pb_rate_source', 'rate',
            'discount_type', 'discount_value', 'discount_amount',
            'taxable_amount', 'tax_percentage', 'tax_amount',
            'cgst_rate', 'cgst_amount',
            'sgst_rate', 'sgst_amount',
            'igst_rate', 'igst_amount',
            'cess_rate', 'cess_amount',
            'line_total',
            'is_scheme_item',
            'invoiced_quantity',
            'scheme_discount_amount',
            'authorized_status', 'authorized_status_name', 'authorized_level', 'authorized_by_type',
            'authorized_by_identifier', 'authorized_on', 'current_authorized_level',
            'current_authorized_status', 'current_authorized_by_type', 'current_authorized_by_identifier',
            'current_authorized_on',
            'created_on', 'modified_on'
        )
        read_only_fields = (
            'id', 'code', 'company_name', 'category_name', 'item_code', 'item_name', 'hsn_code', 'uom_name',
            'taxable_amount', 'tax_percentage', 'tax_amount',
            'cgst_rate', 'cgst_amount', 'sgst_rate', 'sgst_amount',
            'igst_rate', 'igst_amount', 'cess_rate', 'cess_amount',
            'line_total', 'invoiced_quantity', 'authorized_status', 'authorized_status_name',
            'authorized_level', 'authorized_by_type', 'authorized_by_identifier', 'authorized_on',
            'current_authorized_level', 'current_authorized_status', 'current_authorized_by_type',
            'current_authorized_by_identifier', 'current_authorized_on',
            'created_on', 'modified_on'
        )
    
    def get_invoiced_quantity(self, obj):
        return float(obj.get_invoiced_quantity())
    
    def get_authorized_status_name(self, obj):
        return obj.get_authorized_status_display()

    def get_scheme_discount_amount(self, obj):
        total = obj.applied_schemes.aggregate(total=Sum('discount_amount')).get('total') if hasattr(obj, 'applied_schemes') else None
        return float(total or 0)
    
    def validate(self, data):
        """Validate line item data"""
        from decimal import Decimal, ROUND_HALF_UP
        
        if data.get('quantity', 0) <= 0:
            raise ValidationError({'quantity': 'Quantity must be greater than 0'})
        
        if data.get('rate', 0) < 0:
            raise ValidationError({'rate': 'Rate cannot be negative'})
        
        # Check if trying to reduce quantity below invoiced quantity
        if self.instance:
            invoiced_qty = self.instance.get_invoiced_quantity()
            new_qty = data.get('quantity', self.instance.quantity)
            if invoiced_qty > 0 and new_qty < invoiced_qty:
                raise ValidationError({
                    'quantity': f'Cannot reduce quantity below invoiced quantity ({invoiced_qty})'
                })
        
        # Validate and round decimal fields to fit max_digits=15, decimal_places=2
        decimal_fields = ['pb_rate', 'rate', 'discount_amount', 'taxable_amount', 'tax_amount',
                         'cgst_amount', 'sgst_amount', 'igst_amount', 'cess_amount', 'line_total']
        
        for field in decimal_fields:
            if field in data and data[field] is not None:
                value = Decimal(str(data[field]))
                # Round to 2 decimal places
                rounded_value = value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                # Check if it fits in max_digits=15 (13 digits before decimal, 2 after)
                if abs(rounded_value) >= Decimal('10000000000000'):  # 10^13
                    raise ValidationError({field: f'{field} value is too large'})
                data[field] = rounded_value
        
        return data


class SalesOrderSchemeSerializer(serializers.ModelSerializer):
    scheme_code = serializers.CharField(source='scheme.code', read_only=True)
    scheme_name = serializers.CharField(source='scheme.name', read_only=True)
    scheme_type = serializers.CharField(source='scheme.scheme_type', read_only=True)
    scheme_type_display = serializers.CharField(source='scheme.get_scheme_type_display', read_only=True)
    priority = serializers.IntegerField(source='scheme.priority', read_only=True)

    class Meta:
        model = SalesOrderScheme
        fields = (
            'id',
            'scheme',
            'scheme_code',
            'scheme_name',
            'scheme_type',
            'scheme_type_display',
            'priority',
            'discount_amount',
            'free_items',
            'applied_at',
        )
        read_only_fields = fields


class SalesOrderItemSchemeSerializer(serializers.ModelSerializer):
    scheme_code = serializers.CharField(source='scheme.code', read_only=True)
    scheme_name = serializers.CharField(source='scheme.name', read_only=True)
    scheme_type = serializers.CharField(source='scheme.scheme_type', read_only=True)
    scheme_type_display = serializers.CharField(source='scheme.get_scheme_type_display', read_only=True)

    class Meta:
        model = SalesOrderItemScheme
        fields = (
            'id',
            'sales_order_item',
            'scheme',
            'scheme_code',
            'scheme_name',
            'scheme_type',
            'scheme_type_display',
            'discount_amount',
            'free_quantity',
        )
        read_only_fields = fields


class SalesOrderListSerializer(serializers.ModelSerializer):
    """Serializer for sales order list view"""
    customer_name = serializers.SerializerMethodField()
    customer_type_display = serializers.CharField(source='get_customer_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items_count = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    authorized_status_name = serializers.SerializerMethodField()
    pending_approver_names = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = SalesOrder
        fields = (
            'id', 'code', 'order_number', 'order_date',
            'customer_type', 'customer_type_display', 'customer_name',
            'status', 'status_display',
            'items_count', 'grand_total',
            'created_by_name', 'created_on',
            'authorized_status', 'authorized_status_name', 'authorized_level', 'authorized_by_type',
            'authorized_by_identifier', 'authorized_on', 'current_authorized_level',
            'current_authorized_status', 'current_authorized_by_type', 'current_authorized_by_identifier',
            'current_authorized_on', 'pending_approver_names'
        )
        read_only_fields = fields
    
    def get_customer_name(self, obj):
        return obj.get_customer_name()
    
    def get_items_count(self, obj):
        return obj.items.count()
    
    def get_created_by_name(self, obj):
        if obj.created_by_type and obj.created_by_identifier:
            return f"{obj.created_by_type}: {obj.created_by_identifier}"
        return 'System'
    
    def get_authorized_status_name(self, obj):
        return obj.get_authorized_status_display()
    
    def get_pending_approver_names(self, obj):
        """Get pending approver names"""
        from Core.Users.serializers import get_pending_approver_names
        return get_pending_approver_names(obj)


class SalesOrderSerializer(serializers.ModelSerializer):
    """Full serializer for Sales Order create/update"""
    items = SalesOrderItemSerializer(many=True)
    attachments = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField(read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    billing_state_name = serializers.CharField(source='billing_state.name', read_only=True)
    billing_city_name = serializers.CharField(source='billing_city.name', read_only=True)
    billing_area_name = serializers.CharField(source='billing_area.name', read_only=True)
    shipping_state_name = serializers.CharField(source='shipping_state.name', read_only=True)
    shipping_city_name = serializers.CharField(source='shipping_city.name', read_only=True)
    shipping_area_name = serializers.CharField(source='shipping_area.name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    tax_type_display = serializers.CharField(source='get_tax_type_display', read_only=True)
    state_info = serializers.SerializerMethodField(read_only=True)
    authorized_status_name = serializers.SerializerMethodField()
    auto_apply_schemes = serializers.BooleanField(write_only=True, required=False, default=False)
    selected_scheme_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        allow_empty=True,
        help_text="List of scheme IDs selected by user to apply"
    )
    applied_schemes = SalesOrderSchemeSerializer(many=True, read_only=True)
    pending_approver_names = serializers.SerializerMethodField(read_only=True)
    created_by = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = SalesOrder
        fields = (
            'id', 'code', 'order_number', 'order_date',
            'company', 'company_name', 'tax_type', 'tax_type_display',
            'customer_type', 'retailer', 'distributor', 'superstockist', 'customer_name', 'credit_days',
            'billing_state', 'billing_city', 'billing_area', 'billing_address',
            'billing_state_name', 'billing_city_name', 'billing_area_name',
            'shipping_state', 'shipping_city', 'shipping_area', 'shipping_address', 'same_as_billing',
            'shipping_state_name', 'shipping_city_name', 'shipping_area_name',
            'state_info',
            'status',
            'subtotal', 'discount_amount', 'taxable_amount', 'tax_amount',
            'freight_charges', 'other_charges', 'round_off', 'grand_total',
            'remarks', 'internal_notes', 'attachment', 'attachments',
            'approved_by', 'approved_by_name', 'approved_at', 'rejection_reason',
            'items',
            'auto_apply_schemes',
            'selected_scheme_ids',
            'applied_schemes',
            'authorized_status', 'authorized_status_name', 'authorized_level', 'authorized_by_type',
            'authorized_by_identifier', 'authorized_on', 'current_authorized_level',
            'current_authorized_status', 'current_authorized_by_type', 'current_authorized_by_identifier',
            'current_authorized_on', 'pending_approver_names',
            'created_on', 'modified_on', 'created_by_type', 'created_by_identifier', 'created_by'
        )
        read_only_fields = (
            'id', 'code', 'order_number', 'customer_name', 'company_name',
            'billing_state_name', 'billing_city_name', 'billing_area_name',
            'shipping_state_name', 'shipping_city_name', 'shipping_area_name',
            'approved_by_name', 'tax_type_display', 'state_info', 'attachments',
            'subtotal', 'discount_amount', 'taxable_amount', 'tax_amount', 'grand_total',
            'authorized_status', 'authorized_status_name', 'authorized_level', 'authorized_by_type',
            'authorized_by_identifier', 'authorized_on', 'current_authorized_level',
            'current_authorized_status', 'current_authorized_by_type', 'current_authorized_by_identifier',
            'current_authorized_on', 'pending_approver_names', 'created_by',
            'created_on', 'modified_on'
        )
    
    def get_attachments(self, obj):
        qs = obj.attachments.filter(is_deleted=False)
        return SalesOrderAttachmentSerializer(qs, many=True, context=self.context).data
    
    def get_customer_name(self, obj):
        return obj.get_customer_name()
    
    def get_state_info(self, obj):
        """Get detailed state comparison info"""
        return obj.get_state_info()
    
    def get_authorized_status_name(self, obj):
        return obj.get_authorized_status_display()
    
    def get_pending_approver_names(self, obj):
        """Get pending approver names"""
        from Core.Users.serializers import get_pending_approver_names
        return get_pending_approver_names(obj)

    def get_created_by(self, obj):
        if not obj.created_by_identifier:
            return None
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(id=obj.created_by_identifier)
            return {
                'id': str(user.id),
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': f"{user.first_name} {user.last_name}".strip(),
            }
        except User.DoesNotExist:
            return {'id': obj.created_by_identifier, 'username': None, 'first_name': None, 'last_name': None}

    def validate(self, data):
        """Validate sales order data"""
        from decimal import Decimal, ROUND_HALF_UP
        
        customer_type = data.get('customer_type')
        
        # Validate customer selection
        if customer_type == 'RETAILER' and not data.get('retailer'):
            raise ValidationError({'retailer': 'Retailer is required for this customer type'})
        elif customer_type == 'DISTRIBUTOR' and not data.get('distributor'):
            raise ValidationError({'distributor': 'Distributor is required for this customer type'})
        elif customer_type == 'SUPERSTOCKIST' and not data.get('superstockist'):
            raise ValidationError({'superstockist': 'Superstockist is required for this customer type'})
        
        # Validate at least one item
        items = data.get('items', [])
        if not items:
            raise ValidationError({'items': 'At least one item is required'})
        
        # Validate and round decimal fields to fit max_digits=15, decimal_places=2
        decimal_fields = ['subtotal', 'discount_amount', 'taxable_amount', 'tax_amount', 
                         'freight_charges', 'other_charges', 'round_off', 'grand_total']
        
        for field in decimal_fields:
            if field in data and data[field] is not None:
                value = Decimal(str(data[field]))
                # Round to 2 decimal places
                rounded_value = value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                # Check if it fits in max_digits=15 (13 digits before decimal, 2 after)
                if abs(rounded_value) >= Decimal('10000000000000'):  # 10^13
                    raise ValidationError({field: f'{field} value is too large'})
                data[field] = rounded_value
        
        return data
    
    def create(self, validated_data):
        """Create sales order with items"""
        from django.db import transaction
        from django.db.models import F, Value, CharField
        from django.db.models.functions import Substr
        import re
        
        items_data = validated_data.pop('items')
        auto_apply_schemes = validated_data.pop('auto_apply_schemes', False)
        selected_scheme_ids = validated_data.pop('selected_scheme_ids', [])
        
        # Document number should already be provided by frontend
        # If not provided (old clients), generate it as fallback
        if not validated_data.get('order_number'):
            from django.utils import timezone
            
            validated_data['order_number'] = self._generate_unique_order_number()
        
        # Create order with atomic transaction and retries for duplicate handling
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Use atomic transaction for order creation
                with transaction.atomic():
                    # Create order
                    order = SalesOrder.objects.create(**validated_data)
                    
                    # Create items
                    for item_data in items_data:
                        item = SalesOrderItem.objects.create(order=order, **item_data)
                        item.calculate_amounts()
                        item.save()
                    
                    # Calculate order totals (initial calculation)
                    order.calculate_totals()
                    order.save()

                    # For non-draft documents, keep business status aligned with authorization state.
                    if order.status != 'DRAFT':
                        order.status = 'CONFIRMED' if order.authorized_status == order.APPROVED else 'PENDING'
                        order.save(update_fields=['status'])
                    
                    # Apply schemes if requested
                    if auto_apply_schemes and selected_scheme_ids:
                        self._apply_schemes_to_order(order, selected_scheme_ids)
                        
                        # Recalculate totals after applying schemes to include scheme discounts
                        order.calculate_totals()
                        order.save()
                        
                        # Refresh order from DB to get applied_schemes with proper prefetch
                        order = SalesOrder.objects.prefetch_related(
                            'applied_schemes',
                            'applied_schemes__scheme',
                            'items__applied_schemes',
                            'items__applied_schemes__scheme'
                        ).get(id=order.id)
                    
                    # Create history entry
                    SalesOrderHistory.objects.create(
                        order=order,
                        action='CREATED',
                        new_status=order.status,
                        remarks='Order created'
                    )
                    
                    # Final prefetch for the response (ensure we have all related data)
                    order = SalesOrder.objects.prefetch_related(
                        'applied_schemes',
                        'applied_schemes__scheme',
                        'items__applied_schemes',
                        'items__applied_schemes__scheme'
                    ).get(id=order.id)
                    
                    return order
            
            except IntegrityError as e:
                last_error = e
                error_msg = str(e).lower()
                
                # If it's order_number duplicate and not on last attempt, retry with new number
                if 'order_number' in error_msg and attempt < max_retries - 1:
                    validated_data['order_number'] = self._generate_unique_order_number()
                    continue
                else:
                    # For other integrity errors or final retry, re-raise
                    raise
        
        # If we exhausted retries
        if last_error:
            raise last_error
    
    def _generate_unique_order_number(self):
        """
        Generate a unique order number using atomic database operation.
        This prevents race conditions in concurrent requests.
        """
        from django.db import transaction
        from django.utils import timezone
        import re
        
        today = timezone.now().date()
        
        # Determine financial year (April 1 to March 31)
        if today.month >= 4:  # April onwards
            fy_start = today.year
            fy_end = today.year + 1
        else:  # January to March
            fy_start = today.year - 1
            fy_end = today.year
        
        # Format: SO-25-26 (where 25-26 is FY 2025-26)
        fy_suffix = f"{str(fy_start)[-2:]}-{str(fy_end)[-2:]}"
        prefix = f"SO-{fy_suffix}"
        
        # Use atomic transaction with SELECT FOR UPDATE to prevent race conditions
        with transaction.atomic():
            # Get all matching order numbers with row locking
            existing_orders = SalesOrder.objects.filter(
                order_number__startswith=prefix
            ).select_for_update().values_list('order_number', flat=True)
            
            # Find the maximum numeric suffix
            max_suffix = 0
            for on in existing_orders:
                match = re.search(r'-(\d+)$', on or '')
                if match:
                    try:
                        max_suffix = max(max_suffix, int(match.group(1)))
                    except ValueError:
                        continue
            
            next_number = f"{prefix}-{max_suffix + 1}"
        
        return next_number
    
    def _apply_schemes_to_order(self, order, selected_scheme_ids=None):
        """
        Apply applicable schemes to the sales order.
        
        This method:
        1. Gets all applicable schemes for the order
        2. Filters by selected_scheme_ids if provided
        3. Validates scheme conditions
        4. Calculates benefits
        5. Updates order totals with discounts
        
        Args:
            order: SalesOrder instance
            selected_scheme_ids: List of scheme IDs to apply (if None, applies all valid schemes)
        """
        try:
            engine = SchemeEngine()
            
            # Get applicable schemes using the order date
            applicable_schemes = engine.get_applicable_schemes(order, order.order_date)
            
            if not applicable_schemes:
                return
            
            # Filter by selected scheme IDs if provided
            if selected_scheme_ids:
                applicable_schemes = [
                    scheme for scheme in applicable_schemes 
                    if str(scheme.id) in [str(sid) for sid in selected_scheme_ids]
                ]
            
            if not applicable_schemes:
                return
            
            # Validate and apply schemes
            order_items = list(order.items.all())
            valid_schemes = []
            
            for scheme in applicable_schemes:
                is_valid, _, _ = engine.validate_conditions(scheme, order, order_items)
                if is_valid:
                    valid_schemes.append(scheme)
            
            # Apply valid schemes
            if valid_schemes:
                engine.apply_schemes(order, valid_schemes)
        
        except Exception as e:
            # Log error but don't fail order creation
            import traceback
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error applying schemes to order {order.id}: {str(e)}\n{traceback.format_exc()}")
    
    def update(self, instance, validated_data):
        """Update sales order with items"""
        items_data = validated_data.pop('items', None)
        auto_apply_schemes = validated_data.pop('auto_apply_schemes', False)
        selected_scheme_ids = validated_data.pop('selected_scheme_ids', [])
        old_status = instance.status
        
        # Check if order has confirmed invoices
        has_confirmed_invoices = instance.invoices.filter(
            status__in=['CONFIRMED', 'PAID', 'PARTIALLY_PAID']
        ).exists()
        
        if has_confirmed_invoices:
            raise ValidationError({
                'non_field_errors': 'Cannot edit sales order with confirmed invoices'
            })
        
        # Update order fields (excluding calculated fields)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.approved_by = None
        instance.approved_at = None

        # Don't save yet - wait until after items are updated
        
        # Update items if provided
        if items_data is not None:
            # Get existing item IDs
            existing_item_ids = set(instance.items.values_list('id', flat=True))
            incoming_item_ids = set()
            
            for item_data in items_data:
                item_id = item_data.get('id')
                if item_id:
                    incoming_item_ids.add(item_id)
                    # Update existing item
                    try:
                        item = instance.items.get(id=item_id)
                        for attr, value in item_data.items():
                            if attr != 'id':
                                setattr(item, attr, value)
                        item.calculate_amounts()
                        item.save()
                    except SalesOrderItem.DoesNotExist:
                        # Item ID provided but doesn't exist - create new one
                        item_data_copy = item_data.copy()
                        item_data_copy.pop('id', None)
                        item = SalesOrderItem.objects.create(order=instance, **item_data_copy)
                        item.calculate_amounts()
                        item.save()
                else:
                    # Create new item
                    item = SalesOrderItem.objects.create(order=instance, **item_data)
                    item.calculate_amounts()
                    item.save()
            
            # Delete items not in incoming data (only if not invoiced)
            items_to_delete = existing_item_ids - incoming_item_ids
            for item_id in items_to_delete:
                item = instance.items.get(id=item_id)
                if item.get_invoiced_quantity() > 0:
                    raise ValidationError({
                        'items': f'Cannot delete item {item.item.name} - already invoiced'
                    })
                item.delete()
            
            # Recalculate totals after all items are updated
            instance.calculate_totals()
        else:
            # If no items data provided, just save the order
            instance.save()
        
        # Apply schemes if requested
        if auto_apply_schemes:
            if selected_scheme_ids:
                # Apply selected schemes
                self._apply_schemes_to_order(instance, selected_scheme_ids)
            else:
                # Empty list means remove all schemes
                instance.applied_schemes.all().delete()
            
            # Recalculate totals after applying/removing schemes
            instance.calculate_totals()
            instance.save()

        # Keep non-draft business status in sync with latest authorization state.
        if instance.status != 'DRAFT':
            target_status = 'CONFIRMED' if instance.authorized_status == instance.APPROVED else 'PENDING'
            if instance.status != target_status:
                instance.status = target_status
                instance.save(update_fields=['status'])
        
        # Refresh from database to ensure we have the latest calculated values
        instance.refresh_from_db()
        
        # Create history entry
        SalesOrderHistory.objects.create(
            order=instance,
            action='UPDATED',
            old_status=old_status,
            new_status=instance.status,
            remarks='Order updated'
        )
        
        return instance


class SalesOrderHistorySerializer(serializers.ModelSerializer):
    """Serializer for sales order history"""
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)
    
    class Meta:
        model = SalesOrderHistory
        fields = (
            'id', 'order', 'order_number',
            'action', 'action_display',
            'old_status', 'new_status',
            'changes', 'remarks',
            'changed_by', 'changed_by_name', 'changed_at'
        )
        read_only_fields = fields


class SalesOrderStatusCountSerializer(serializers.Serializer):
    DRAFT = serializers.IntegerField(read_only=True, default=0)
    PENDING = serializers.IntegerField(read_only=True, default=0)
    CONFIRMED = serializers.IntegerField(read_only=True, default=0)
    PARTIALLY_DISPATCHED = serializers.IntegerField(read_only=True, default=0)
    DISPATCHED = serializers.IntegerField(read_only=True, default=0)
    PARTIALLY_INVOICED = serializers.IntegerField(read_only=True, default=0)
    INVOICED = serializers.IntegerField(read_only=True, default=0)
    DELIVERED = serializers.IntegerField(read_only=True, default=0)
    CANCELLED = serializers.IntegerField(read_only=True, default=0)
    total = serializers.IntegerField(read_only=True, default=0)


class SalesOrderReportSerializer(serializers.Serializer):
    """
    Product-wise Sales Order Report Serializer
    Each row represents one product from an order
    """
    id = serializers.SerializerMethodField()

    # Order Information
    order_id = serializers.UUIDField()
    order_number = serializers.CharField()
    order_date = serializers.DateField()

    # Customer Information
    customer_name = serializers.CharField()
    customer_type = serializers.CharField()
    customer_type_code = serializers.CharField()

    # Product Information (ONE product per row)
    product_id = serializers.UUIDField()
    product_code = serializers.CharField()
    product_name = serializers.CharField()
    quantity = serializers.DecimalField(max_digits=15, decimal_places=3)
    rate = serializers.DecimalField(max_digits=15, decimal_places=2)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)

    # Order Financial Information
    order_total = serializers.DecimalField(max_digits=15, decimal_places=2)
    order_tax = serializers.DecimalField(max_digits=15, decimal_places=2)
    order_discount = serializers.DecimalField(max_digits=15, decimal_places=2)

    # Status Information
    status = serializers.CharField()
    status_code = serializers.CharField()
    authorization_status = serializers.CharField()
    authorization_status_code = serializers.IntegerField()

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
    agent_name = serializers.CharField(allow_null=True)

    def get_id(self, obj):
        return f"{obj['order_id']}_{obj['product_id']}"
