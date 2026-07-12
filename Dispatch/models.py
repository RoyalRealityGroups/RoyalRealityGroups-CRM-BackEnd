from django.db import models
from decimal import Decimal
from Core.Users.models import CoreModel
from Masters.models import Company
from Sales.models import SalesOrder, SalesOrderItem
from .attachment_models import DispatchPlanAttachment


class DispatchPlan(CoreModel):
    """
    Dispatch Plan header model
    """

    CODE_PREFIX = 'DP'

    # Header Information
    dispatch_number = models.CharField(max_length=50, unique=True, db_index=True)
    dispatch_date = models.DateField(db_index=True)
    planned_dispatch_date = models.DateField()
    
    # Location
    location = models.ForeignKey(
        'Masters.Location',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='dispatch_plans'
    )
    
    # Vehicle Details
    vehicle_number = models.CharField(max_length=50, blank=True, null=True)
    vehicle_type = models.CharField(max_length=100, blank=True, null=True)
    vehicle_capacity = models.CharField(max_length=50, blank=True, null=True)
    
    # Logistics Information
    lr_no = models.CharField(max_length=100, blank=True, null=True, help_text='Lorry Receipt Number')
    stock_insurance = models.BooleanField(default=False, help_text='Whether stock is insured')
    
    # Driver Details
    driver_name = models.CharField(max_length=100, blank=True)
    driver_phone = models.CharField(max_length=20, blank=True)
    driver_license = models.CharField(max_length=50, blank=True)
    
    # Route Details
    route = models.ForeignKey(
        'Masters.Route',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='dispatch_plans'
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('DRAFT', 'Draft'),
            ('PENDING', 'Pending'),
            ('CONFIRMED', 'Confirmed'),
            ('DELIVERED', 'Delivered'),
            ('CANCELLED', 'Cancelled'),
        ],
        default='DRAFT',
        db_index=True
    )
    
    # Summary Fields
    total_orders = models.IntegerField(default=0)
    total_weight = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_volume = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Timing
    estimated_start_time = models.DateTimeField(null=True, blank=True)
    estimated_end_time = models.DateTimeField(null=True, blank=True)
    actual_start_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)
    
    # Additional Information
    remarks = models.TextField(blank=True)
    
    class Meta:
        db_table = 'dispatch_plan'
        ordering = ['-dispatch_date', '-created_on']
        verbose_name = 'Dispatch Plan'
        verbose_name_plural = 'Dispatch Plans'
        indexes = [
            models.Index(fields=['dispatch_number']),
            models.Index(fields=['dispatch_date', 'status']),
            models.Index(fields=['-created_on']),
        ]
    
    def __str__(self):
        return f"{self.dispatch_number} - {self.dispatch_date}"
    
    def calculate_totals(self):
        """Calculate totals from dispatch items"""
        items = self.items.all()
        self.total_orders = items.values('sales_order').distinct().count()
        self.total_value = sum(
            item.quantity_dispatched * item.sales_order.grand_total / 
            sum(order_item.quantity for order_item in item.sales_order.items.all())
            for item in items
        )
        self.save()
    
    @staticmethod
    def generate_dispatch_number(location_code):
        """Generate dispatch number atomically in format: DP-LOC-FY-INCREMENT"""
        from datetime import date
        from django.db import transaction
        import re
        
        today = date.today()
        
        # Calculate financial year (April to March)
        if today.month >= 4:
            fy_start = today.year % 100
            fy_end = (today.year + 1) % 100
        else:
            fy_start = (today.year - 1) % 100
            fy_end = today.year % 100
        
        fy_string = f"{fy_start:02d}-{fy_end:02d}"
        # Take first 3 characters of location code and make uppercase
        loc_code = location_code[:3].upper()
        prefix = f"DP-{loc_code}-{fy_string}"
        
        # Use atomic transaction with SELECT FOR UPDATE to prevent race conditions
        with transaction.atomic():
            # Get all matching dispatch numbers with row locking
            dispatch_numbers = DispatchPlan.objects.filter(
                dispatch_number__startswith=prefix
            ).select_for_update().values_list('dispatch_number', flat=True)
            
            # Find the maximum numeric suffix
            max_suffix = 0
            for dn in dispatch_numbers:
                match = re.search(r'-(\d+)$', dn or '')
                if match:
                    try:
                        max_suffix = max(max_suffix, int(match.group(1)))
                    except ValueError:
                        continue
            
            return f"{prefix}-{max_suffix + 1}"


class DispatchItem(CoreModel):
    """
    Dispatch Plan line items - links to sales orders with partial quantity support
    """

    CODE_PREFIX = 'DPI'
    dispatch_plan = models.ForeignKey(
        DispatchPlan,
        on_delete=models.CASCADE,
        related_name='items'
    )
    sales_order = models.ForeignKey(
        SalesOrder,
        on_delete=models.RESTRICT,
        related_name='dispatch_items'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name='dispatch_items',
        null=True,
        blank=True
    )
    
    # Quantity Support for Partial Dispatch
    quantity_ordered = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        help_text='Total quantity in sales order'
    )
    quantity_dispatched = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        help_text='Quantity being dispatched in this plan'
    )
    
    # Sequence Management
    delivery_sequence = models.IntegerField(default=1)
    loading_sequence = models.IntegerField(default=1)
    unloading_sequence = models.PositiveIntegerField(null=True, blank=True)
    
    # Status Tracking
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('LOADED', 'Loaded'),
            ('DELIVERED', 'Delivered'),
            ('FAILED', 'Failed Delivery'),
        ],
        default='PENDING',
        db_index=True
    )
    
    # Delivery Information
    estimated_delivery_time = models.DateTimeField(null=True, blank=True)
    actual_delivery_time = models.DateTimeField(null=True, blank=True)
    delivery_notes = models.TextField(blank=True)
    
    # Proof of Delivery
    delivered_by = models.CharField(max_length=100, blank=True)
    received_by = models.CharField(max_length=100, blank=True)
    delivery_proof = models.FileField(
        upload_to='dispatch/delivery_proof/',
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'dispatch_item'
        ordering = ['delivery_sequence', 'loading_sequence']
        verbose_name = 'Dispatch Item'
        verbose_name_plural = 'Dispatch Items'
        indexes = [
            models.Index(fields=['dispatch_plan', 'sales_order']),
            models.Index(fields=['company']),
            models.Index(fields=['status']),
            models.Index(fields=['delivery_sequence']),
        ]
    
    def __str__(self):
        return f"{self.dispatch_plan.dispatch_number} - {self.sales_order.order_number}"
    
    def get_invoiced_quantity(self):
        """Get total invoiced quantity for this dispatch item"""
        from Invoice.models import InvoiceItem
        from django.db.models import Sum
        
        total = InvoiceItem.objects.filter(
            sales_order_item__in=self.order_items.values_list('sales_order_item', flat=True),
            invoice__source_type='DISPATCH',
            invoice__status__in=['CONFIRMED', 'PAID', 'PARTIALLY_PAID']
        ).aggregate(total=Sum('quantity'))['total'] or Decimal('0')
        
        return total
    
    def clean(self):
        """Validate dispatch quantity"""
        from django.core.exceptions import ValidationError
        
        if self.quantity_dispatched > self.quantity_ordered:
            raise ValidationError({
                'quantity_dispatched': 'Dispatched quantity cannot exceed ordered quantity'
            })
        
        if self.quantity_dispatched <= 0:
            raise ValidationError({
                'quantity_dispatched': 'Dispatched quantity must be greater than 0'
            })
        
        # Check if already invoiced
        if self.pk:
            invoiced_qty = self.get_invoiced_quantity()
            if invoiced_qty > 0 and self.quantity_dispatched < invoiced_qty:
                raise ValidationError({
                    'quantity_dispatched': f'Cannot reduce quantity below invoiced quantity ({invoiced_qty})'
                })
    
    @property
    def remaining_quantity(self):
        """Calculate remaining quantity to be dispatched"""
        total_dispatched = DispatchItem.objects.filter(
            sales_order=self.sales_order
        ).exclude(
            dispatch_plan__status='CANCELLED'
        ).aggregate(
            total=models.Sum('quantity_dispatched')
        )['total'] or Decimal('0')
        
        return self.quantity_ordered - total_dispatched
    
    @property
    def dispatch_percentage(self):
        """Calculate dispatch completion percentage"""
        if self.quantity_ordered > 0:
            return (self.quantity_dispatched / self.quantity_ordered) * 100
        return 0


class DispatchOrderItem(CoreModel):
    """
    Dispatch Order Item - item-level dispatch details
    """

    CODE_PREFIX = 'DPOI'
    dispatch_item = models.ForeignKey(
        DispatchItem,
        on_delete=models.CASCADE,
        related_name='order_items'
    )
    sales_order_item = models.ForeignKey(
        SalesOrderItem,
        on_delete=models.RESTRICT,
        related_name='dispatch_order_items'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name='dispatch_order_items',
        null=True,
        blank=True
    )
    
    # Quantity Support for Item-level Dispatch
    quantity_ordered = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        help_text='Quantity of this item in sales order'
    )
    quantity_dispatched = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        help_text='Quantity of this item being dispatched'
    )
    
    # Item-level status
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('LOADED', 'Loaded'),
            ('DELIVERED', 'Delivered'),
            ('FAILED', 'Failed Delivery'),
        ],
        default='PENDING',
        db_index=True
    )
    
    # Item-specific notes
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'dispatch_order_item'
        ordering = ['sales_order_item__item__name']
        verbose_name = 'Dispatch Order Item'
        verbose_name_plural = 'Dispatch Order Items'
        indexes = [
            models.Index(fields=['dispatch_item', 'sales_order_item']),
            models.Index(fields=['company']),
            models.Index(fields=['status']),
        ]
        unique_together = ['dispatch_item', 'sales_order_item']
    
    def __str__(self):
        return f"{self.dispatch_item.dispatch_plan.dispatch_number} - {self.sales_order_item.item.name}"
    
    def get_invoiced_quantity(self):
        """Get total invoiced quantity for this dispatch order item"""
        from Invoice.models import InvoiceItem
        from django.db.models import Sum
        
        total = InvoiceItem.objects.filter(
            sales_order_item=self.sales_order_item,
            invoice__source_type='DISPATCH',
            invoice__status__in=['CONFIRMED', 'PAID', 'PARTIALLY_PAID']
        ).aggregate(total=Sum('quantity'))['total'] or Decimal('0')
        
        return total
    
    def clean(self):
        """Validate dispatch quantity"""
        from django.core.exceptions import ValidationError
        
        if self.quantity_dispatched > self.quantity_ordered:
            raise ValidationError({
                'quantity_dispatched': 'Dispatched quantity cannot exceed ordered quantity'
            })
        
        if self.quantity_dispatched <= 0:
            raise ValidationError({
                'quantity_dispatched': 'Dispatched quantity must be greater than 0'
            })
        
        # Check if already invoiced
        if self.pk:
            invoiced_qty = self.get_invoiced_quantity()
            if invoiced_qty > 0 and self.quantity_dispatched < invoiced_qty:
                raise ValidationError({
                    'quantity_dispatched': f'Cannot reduce quantity below invoiced quantity ({invoiced_qty})'
                })
