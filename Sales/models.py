from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal
from Core.Users.models import BaseModel, CoreModel, ChannelPartnerManager
from Users.models import User
from Masters.models import Retailer, Distributor, Superstockist, State, City, Area, Item, Company


class SalesOrder(CoreModel):
    """
    Sales Order header model
    """

    CODE_PREFIX = 'SO'

    # Order Information
    order_number = models.CharField(max_length=50, unique=True, db_index=True)
    order_date = models.DateField(db_index=True)
    
    # Customer Information
    customer_type = models.CharField(
        max_length=20,
        choices=[
            ('RETAILER', 'Retailer'),
            ('DISTRIBUTOR', 'Distributor'),
            ('SUPERSTOCKIST', 'Superstockist'),
        ],
        db_index=True
    )
    retailer = models.ForeignKey(
        Retailer,
        null=True,
        blank=True,
        on_delete=models.RESTRICT,
        related_name='sales_orders'
    )
    distributor = models.ForeignKey(
        Distributor,
        null=True,
        blank=True,
        on_delete=models.RESTRICT,
        related_name='sales_orders'
    )
    superstockist = models.ForeignKey(
        Superstockist,
        null=True,
        blank=True,
        on_delete=models.RESTRICT,
        related_name='sales_orders'
    )
    credit_days = models.IntegerField(default=0, help_text='Credit days from customer')
    
    # Billing Address
    billing_state = models.ForeignKey(
        State,
        on_delete=models.RESTRICT,
        related_name='sales_orders_billing'
    )
    billing_city = models.ForeignKey(
        City,
        on_delete=models.RESTRICT,
        related_name='sales_orders_billing'
    )
    billing_area = models.ForeignKey(
        Area,
        null=True,
        blank=True,
        on_delete=models.RESTRICT,
        related_name='sales_orders_billing'
    )
    billing_address = models.TextField()
    
    # Shipping Address
    shipping_state = models.ForeignKey(
        State,
        on_delete=models.RESTRICT,
        related_name='sales_orders_shipping'
    )
    shipping_city = models.ForeignKey(
        City,
        on_delete=models.RESTRICT,
        related_name='sales_orders_shipping'
    )
    shipping_area = models.ForeignKey(
        Area,
        null=True,
        blank=True,
        on_delete=models.RESTRICT,
        related_name='sales_orders_shipping'
    )
    shipping_address = models.TextField()
    same_as_billing = models.BooleanField(default=True)
    
    # Company
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name='sales_orders',
        null=True,
        blank=True
    )
    
    # Tax Settings
    tax_type = models.CharField(
        max_length=20,
        choices=[
            ('EXCLUSIVE', 'Tax Exclusive (Price + Tax)'),
            ('INCLUSIVE', 'Tax Inclusive (Price includes Tax)'),
        ],
        default='EXCLUSIVE',
        help_text='Whether item prices include tax or tax is added separately'
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('DRAFT', 'Draft'),
            ('PENDING', 'Pending'),
            ('CONFIRMED', 'Confirmed'),
            ('PARTIALLY_DISPATCHED', 'Partially Dispatched'),
            ('DISPATCHED', 'Dispatched'),
            ('PARTIALLY_INVOICED', 'Partially Invoiced'),
            ('INVOICED', 'Invoiced'),
            ('DELIVERED', 'Delivered'),
            ('CANCELLED', 'Cancelled'),
        ],
        default='DRAFT',
        db_index=True
    )
    
    # Financial Fields
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    taxable_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    freight_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    round_off = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Additional Information
    remarks = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    attachment = models.FileField(upload_to='sales_orders/', null=True, blank=True)
    
    # Approval Fields
    approved_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='approved_sales_orders'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Custom managers
    objects = models.Manager()  # Default manager
    filtered_objects = ChannelPartnerManager()  # Filtered manager
    
    class Meta:
        db_table = 'sales_order'
        ordering = ['-order_date', '-created_on']
        verbose_name = 'Sales Order'
        verbose_name_plural = 'Sales Orders'
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['order_date', 'status']),
            models.Index(fields=['customer_type', 'status']),
            models.Index(fields=['-created_on']),
        ]
    
    def __str__(self):
        return f"{self.order_number} - {self.get_customer_name()}"
    
    @property
    def customer(self):
        """Get the customer object based on customer_type"""
        if self.customer_type == 'RETAILER':
            return self.retailer
        elif self.customer_type == 'DISTRIBUTOR':
            return self.distributor
        elif self.customer_type == 'SUPERSTOCKIST':
            return self.superstockist
        return None
    
    def clean(self):
        """Validate customer has state information"""
        super().clean()
        
        customer = self.customer
        if customer:
            customer_state = getattr(customer, 'state', None)
            customer_gst = getattr(customer, 'gstin', None)
            
            if not customer_state and not customer_gst:
                raise ValidationError({
                    'customer': 'Customer must have either state or GST number for tax calculation'
                })
    
    def is_same_state(self):
        """
        Determine if company and customer are in same state
        Priority: GST number state code > Physical state
        """
        # Get company info
        company_gst = self.company.gst_number if self.company else None
        company_state = self.company.state if self.company else None
        
        # Get customer info
        customer = self.customer
        customer_gst = getattr(customer, 'gstin', None) if customer else None
        customer_state = getattr(customer, 'state', None) if customer else None
        
        # Priority 1: Compare GST state codes
        if company_gst and customer_gst:
            company_state_code = company_gst[:2]
            customer_state_code = customer_gst[:2]
            return company_state_code == customer_state_code
        
        # Priority 2: Compare physical states
        if company_state and customer_state:
            return company_state.id == customer_state.id
        
        # Fallback: inter-state (safer for tax compliance)
        return False
    
    def get_state_info(self):
        """Get detailed state information for frontend display"""
        company_gst = self.company.gst_number if self.company else None
        company_state = self.company.state if self.company else None
        
        customer = self.customer
        customer_gst = getattr(customer, 'gstin', None) if customer else None
        customer_state = getattr(customer, 'state', None) if customer else None
        
        return {
            'company': {
                'gst': company_gst,
                'state': company_state.name if company_state else None,
                'state_code': company_gst[:2] if company_gst else (company_state.gst_code if company_state else None),
            },
            'customer': {
                'gst': customer_gst,
                'state': customer_state.name if customer_state else None,
                'state_code': customer_gst[:2] if customer_gst else (customer_state.gst_code if customer_state else None),
            },
            'is_same_state': self.is_same_state(),
            'comparison_basis': 'GST' if (company_gst and customer_gst) else 'State',
            'tax_category': 'CGST+SGST' if self.is_same_state() else 'IGST',
        }
    
    def get_customer_name(self):
        """Get customer name based on customer type"""
        if self.customer_type == 'RETAILER' and self.retailer:
            return self.retailer.name
        elif self.customer_type == 'DISTRIBUTOR' and self.distributor:
            return self.distributor.name
        elif self.customer_type == 'SUPERSTOCKIST' and self.superstockist:
            return self.superstockist.name
        return 'Unknown'
    
    def get_customer_id(self):
        """Get customer ID based on customer type"""
        if self.customer_type == 'RETAILER':
            return self.retailer_id
        elif self.customer_type == 'DISTRIBUTOR':
            return self.distributor_id
        elif self.customer_type == 'SUPERSTOCKIST':
            return self.superstockist_id
        return None
    
    def calculate_totals(self):
        """Calculate order totals from line items"""
        # Clear any cached items to ensure we get fresh data
        if hasattr(self, '_prefetched_objects_cache'):
            self._prefetched_objects_cache.pop('items', None)
            self._prefetched_objects_cache.pop('applied_schemes', None)
        
        items = self.items.all()
        self.subtotal = sum(item.quantity * item.rate for item in items)
        manual_discount = sum(item.discount_amount for item in items)
        
        # Get item-level scheme discounts
        item_scheme_discount = SalesOrderItemScheme.objects.filter(
            sales_order_item__order=self
        ).aggregate(total=models.Sum('discount_amount'))['total'] or Decimal('0')
        
        # Get order-level scheme discounts from applied schemes (force fresh query)
        from Sales.models import SalesOrderScheme
        order_scheme_discount = SalesOrderScheme.objects.filter(
            sales_order=self
        ).aggregate(total=models.Sum('discount_amount'))['total'] or Decimal('0')
        
        # IMPORTANT: Don't double-count! If we have order-level schemes, use only those
        # Item-level schemes are already reflected in item.taxable_amount
        # Order-level schemes are additional discounts on top
        if order_scheme_discount > 0:
            # Use only order-level scheme discount (item-level already in taxable_amount)
            self.discount_amount = manual_discount + order_scheme_discount
        else:
            # No order-level schemes, use item-level
            self.discount_amount = manual_discount + item_scheme_discount
        
        self.taxable_amount = sum(item.taxable_amount for item in items)
        self.tax_amount = sum(item.tax_amount for item in items)
        
        # Grand total = taxable + tax + freight + other + round_off
        self.grand_total = (
            self.taxable_amount +
            self.tax_amount +
            self.freight_charges +
            self.other_charges +
            self.round_off
        )
        
        self.save()
    
    def get_invoiced_quantities(self):
        """Get invoiced quantities per item"""
        from collections import defaultdict
        invoiced_qty = defaultdict(Decimal)
        
        # Get all confirmed invoices
        for invoice in self.invoices.filter(status__in=['CONFIRMED', 'PAID', 'PARTIALLY_PAID']):
            for invoice_item in invoice.items.all():
                invoiced_qty[invoice_item.sales_order_item_id] += invoice_item.quantity
        
        return dict(invoiced_qty)
    
    def get_item_invoiced_quantity(self, item_id):
        """Get invoiced quantity for a specific item"""
        from Invoice.models import InvoiceItem
        from django.db.models import Sum
        
        total = InvoiceItem.objects.filter(
            sales_order_item_id=item_id,
            invoice__sales_order=self,
            invoice__status__in=['CONFIRMED', 'PAID', 'PARTIALLY_PAID']
        ).aggregate(total=Sum('quantity'))['total'] or Decimal('0')
        
        return total
    
    def is_fully_invoiced(self):
        """Check if all items are fully invoiced"""
        invoiced_qty = self.get_invoiced_quantities()
        
        for item in self.items.all():
            item_invoiced = invoiced_qty.get(item.id, Decimal('0'))
            if item_invoiced < item.quantity:
                return False
        
        return True
    
    def update_dispatch_status(self):
        """Update order status based on dispatched quantities"""
        from Dispatch.models import DispatchOrderItem
        from django.db.models import Sum
        
        # Get total dispatched quantity per item
        for item in self.items.all():
            dispatched_qty = DispatchOrderItem.objects.filter(
                sales_order_item=item,
                dispatch_item__dispatch_plan__status__in=['CONFIRMED', 'DELIVERED']
            ).aggregate(total=Sum('quantity_dispatched'))['total'] or Decimal('0')
            
            if dispatched_qty < item.quantity:
                # At least one item is partially dispatched
                self.status = 'PARTIALLY_DISPATCHED'
                self.save()
                return
        
        # All items fully dispatched
        if self.items.exists():
            self.status = 'DISPATCHED'
            self.save()
    
    def update_invoice_status(self):
        """Update order status based on invoiced quantities"""
        if not self.invoices.filter(status__in=['CONFIRMED', 'PAID', 'PARTIALLY_PAID']).exists():
            # No invoices, keep current status
            return
        
        if self.is_fully_invoiced():
            self.status = 'INVOICED'
        else:
            self.status = 'PARTIALLY_INVOICED'
        
        self.save()
    
    def update_delivery_status(self):
        """Update order status to DELIVERED when POD is created"""
        # Check if all invoices have POD
        invoices = self.invoices.filter(status__in=['CONFIRMED', 'PAID', 'PARTIALLY_PAID'])
        if invoices.exists():
            # Check if all invoices have POD status as RECEIVED
            if all(inv.pod_status == 'RECEIVED' for inv in invoices):
                self.status = 'DELIVERED'
                self.save()


class SalesOrderItem(CoreModel):
    """
    Sales Order line items
    """

    CODE_PREFIX = 'SOI'

    order = models.ForeignKey(
        SalesOrder,
        on_delete=models.CASCADE,
        related_name='items'
    )
    category = models.ForeignKey(
        'Masters.Category',
        on_delete=models.RESTRICT,
        related_name='sales_order_items',
        null=True,
        blank=True
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.RESTRICT,
        related_name='sales_order_items'
    )
    
    # Quantity
    quantity = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    free_quantity = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    
    # Pricing
    pb_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Price Book rate'
    )
    pb_rate_source = models.CharField(
        max_length=50,
        blank=True,
        help_text='Source of PB rate (RETAILER/DISTRIBUTOR/SUPERSTOCKIST/AREA/CITY/STATE/BASE)'
    )
    rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Actual selling rate (editable)'
    )
    
    # Discount
    discount_type = models.CharField(
        max_length=10,
        choices=[
            ('PERCENTAGE', 'Percentage'),
            ('AMOUNT', 'Amount'),
        ],
        default='PERCENTAGE'
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='sales_order_items',
        null=True,
        blank=True,
    )

    discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Tax - Calculated amounts
    taxable_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Tax breakdown (populated based on state comparison)
    cgst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    cgst_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    sgst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    sgst_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    igst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    igst_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cess_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    cess_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Total tax
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Total
    line_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Scheme flag
    is_scheme_item = models.BooleanField(default=False)
    
    # Custom managers
    objects = models.Manager()  # Default manager
    filtered_objects = ChannelPartnerManager()  # Filtered manager
    
    class Meta:
        db_table = 'sales_order_item'
        ordering = ['created_on']
        verbose_name = 'Sales Order Item'
        verbose_name_plural = 'Sales Order Items'
        indexes = [
            models.Index(fields=['order', 'item']),
        ]
    
    def __str__(self):
        return f"{self.order.order_number} - {self.item.name}"
    
    def get_invoiced_quantity(self):
        """Get total invoiced quantity for this order item"""
        return self.order.get_item_invoiced_quantity(self.id)
    
    def get_total_tax_rate(self):
        """Get total tax rate (GST + CESS) from item's current tax composition"""
        if not self.item:
            return Decimal('0')
        
        total = Decimal('0')
        for comp in self.item.current_tax_composition:
            total += comp.tax.tax_rate
        return total
    
    def calculate_amounts(self):
        """
        Calculate taxable and line total based on tax type (Exclusive/Inclusive)
        """
        qty = Decimal(str(self.quantity)) if self.quantity else Decimal('0')
        rate = Decimal(str(self.rate)) if self.rate else Decimal('0')
        disc_val = Decimal(str(self.discount_value)) if self.discount_value else Decimal('0')
        
        # Calculate gross and net amount
        gross_amount = qty * rate
        
        # Discount calculation
        if self.discount_type == 'PERCENTAGE':
            self.discount_amount = (gross_amount * disc_val) / Decimal('100')
        else:  # AMOUNT
            self.discount_amount = disc_val
        
        net_amount = gross_amount - self.discount_amount
        
        # Get total tax rate (GST + CESS)
        tax_rate = self.get_total_tax_rate()
        
        if self.order.tax_type == 'EXCLUSIVE':
            # Tax Extra: net amount is taxable
            self.taxable_amount = net_amount
            self.tax_amount = (net_amount * tax_rate) / Decimal('100')
            self.line_total = net_amount + self.tax_amount
        else:
            # Tax Inclusive: net amount includes tax
            self.line_total = net_amount
            self.taxable_amount = net_amount / (Decimal('1') + tax_rate / Decimal('100'))
            self.tax_amount = net_amount - self.taxable_amount
    
    def calculate_taxes(self):
        """
        Split tax into CGST/SGST/IGST based on state comparison
        and add CESS if applicable
        """
        # First calculate amounts
        self.calculate_amounts()
        
        taxable = Decimal(str(self.taxable_amount)) if self.taxable_amount else Decimal('0')
        
        # Reset all tax fields
        self.cgst_rate = self.cgst_amount = Decimal('0')
        self.sgst_rate = self.sgst_amount = Decimal('0')
        self.igst_rate = self.igst_amount = Decimal('0')
        self.cess_rate = self.cess_amount = Decimal('0')
        
        # Check if same state or different
        is_same_state = self.order.is_same_state()
        
        # Get tax compositions from item
        compositions = self.item.current_tax_composition
        
        for comp in compositions:
            tax = comp.tax
            rate = Decimal(str(tax.tax_rate))
            amount = (taxable * rate) / Decimal('100')
            
            if comp.composition_type == 'PRIMARY' and tax.tax_type == 'GST':
                # Split GST based on state
                if is_same_state:
                    # Intra-state: Split into CGST + SGST (50-50)
                    half_rate = rate / Decimal('2')
                    half_amount = amount / Decimal('2')
                    
                    self.cgst_rate = half_rate
                    self.cgst_amount = half_amount
                    self.sgst_rate = half_rate
                    self.sgst_amount = half_amount
                else:
                    # Inter-state: Use IGST (full rate)
                    self.igst_rate = rate
                    self.igst_amount = amount
            
            elif comp.composition_type == 'CESS' or tax.is_cess:
                # CESS is always added (regardless of state)
                self.cess_rate += rate
                self.cess_amount += amount
        
        # Calculate total tax percentage
        self.tax_percentage = (
            self.cgst_rate + self.sgst_rate + 
            self.igst_rate + self.cess_rate
        )
        
        # Verify tax amount matches breakdown
        calculated_tax = (
            self.cgst_amount + self.sgst_amount + 
            self.igst_amount + self.cess_amount
        )
        
        # Use calculated tax if amounts differ (rounding)
        if abs(self.tax_amount - calculated_tax) > Decimal('0.01'):
            self.tax_amount = calculated_tax
            if self.order.tax_type == 'EXCLUSIVE':
                self.line_total = self.taxable_amount + self.tax_amount
    
    def save(self, *args, **kwargs):
        """Auto-calculate taxes before saving"""
        if self.item and self.order:
            self.calculate_taxes()
        super().save(*args, **kwargs)


class SalesOrderHistory(models.Model):
    """
    Audit trail for sales order changes
    """
    order = models.ForeignKey(
        SalesOrder,
        on_delete=models.CASCADE,
        related_name='history'
    )
    action = models.CharField(
        max_length=50,
        choices=[
            ('CREATED', 'Created'),
            ('UPDATED', 'Updated'),
            ('APPROVED', 'Approved'),
            ('REJECTED', 'Rejected'),
            ('PROCESSING', 'Processing Started'),
            ('INVOICED', 'Invoiced'),
            ('DELIVERED', 'Delivered'),
            ('CANCELLED', 'Cancelled'),
        ],
        db_index=True
    )
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, blank=True)
    changes = models.JSONField(null=True, blank=True, help_text='Field changes in JSON format')
    remarks = models.TextField(blank=True)
    
    # Audit fields
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sales_order_changes'
    )
    changed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'sales_order_history'
        ordering = ['-changed_at']
        verbose_name = 'Sales Order History'
        verbose_name_plural = 'Sales Order History'
        indexes = [
            models.Index(fields=['order', '-changed_at']),
            models.Index(fields=['action', '-changed_at']),
        ]
    
    def __str__(self):
        return f"{self.order.order_number} - {self.action} - {self.changed_at}"

# ============================================================================
# SALES ORDER - SCHEME TRACKING MODELS
# ============================================================================

class SalesOrderScheme(models.Model):
    """
    Tracks schemes applied to a sales order
    """
    
    sales_order = models.ForeignKey(
        'SalesOrder',
        on_delete=models.CASCADE,
        related_name='applied_schemes',
        help_text='Sales order this scheme is applied to'
    )
    scheme = models.ForeignKey(
        'Masters.Scheme',
        on_delete=models.CASCADE,
        related_name='applied_orders',
        help_text='Scheme that was applied'
    )
    
    # Store scheme details at time of application
    scheme_code = models.CharField(max_length=50, help_text='Scheme code at time of application')
    scheme_name = models.CharField(max_length=255, help_text='Scheme name at time of application')
    
    # Discount amount from this scheme
    discount_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text='Total discount amount from this scheme'
    )
    
    # Free items from this scheme
    free_items = models.JSONField(
        default=list,
        blank=True,
        help_text='Free items provided by this scheme as JSON'
    )
    
    # Application timestamp
    applied_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When scheme was applied to order'
    )
    
    class Meta:
        db_table = 'sales_order_scheme'
        ordering = ['applied_at']
        verbose_name = 'Sales Order Scheme'
        verbose_name_plural = 'Sales Order Schemes'
        indexes = [
            models.Index(fields=['sales_order', 'scheme']),
        ]
        unique_together = [['sales_order', 'scheme']]
    
    def __str__(self):
        return f"{self.sales_order.order_number} - {self.scheme_code} (₹{self.discount_amount})"


class SalesOrderItemScheme(models.Model):
    """
    Tracks schemes applied at item level
    """
    
    sales_order_item = models.ForeignKey(
        'SalesOrderItem',
        on_delete=models.CASCADE,
        related_name='applied_schemes',
        help_text='Sales order item this scheme is applied to'
    )
    scheme = models.ForeignKey(
        'Masters.Scheme',
        on_delete=models.CASCADE,
        related_name='applied_order_items',
        help_text='Scheme applied to item'
    )
    
    # Discount amount for this item
    discount_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text='Discount amount for this item'
    )
    
    # Free quantity for this item
    free_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=0,
        help_text='Free quantity provided for this item'
    )
    
    class Meta:
        db_table = 'sales_order_item_scheme'
        ordering = ['id']
        verbose_name = 'Sales Order Item Scheme'
        verbose_name_plural = 'Sales Order Item Schemes'
        indexes = [
            models.Index(fields=['sales_order_item', 'scheme']),
        ]
        unique_together = [['sales_order_item', 'scheme']]
    
    def __str__(self):
        return f"{self.sales_order_item.sales_order.order_number} - Item {self.sales_order_item.item.code} - {self.scheme.code}"
