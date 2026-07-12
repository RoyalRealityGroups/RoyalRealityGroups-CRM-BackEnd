from django.db import models
from decimal import Decimal
from Core.Users.models import CoreModel, ChannelPartnerManager
from Masters.models import Company, Location
from Sales.models import SalesOrder, SalesOrderItem
from Dispatch.models import DispatchPlan


class Invoice(CoreModel):
    """Invoice header model"""

    CODE_PREFIX = 'INV'
    
    # Invoice Information
    invoice_number = models.CharField(max_length=50, unique=True, db_index=True)
    invoice_date = models.DateField(db_index=True)
    due_date = models.DateField()
    
    # Source Information
    source_type = models.CharField(
        max_length=20,
        choices=[
            ('DISPATCH', 'From Dispatch Plan'),
            ('ORDER', 'From Sales Order'),
        ],
        db_index=True
    )
    sales_order = models.ForeignKey(
        SalesOrder,
        on_delete=models.RESTRICT,
        related_name='invoices'
    )
    dispatch_plan = models.ForeignKey(
        DispatchPlan,
        null=True,
        blank=True,
        on_delete=models.RESTRICT,
        related_name='invoices'
    )
    
    # Company & Location
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name='invoices'
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        related_name='invoices',
        null=True,
        blank=True
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('DRAFT', 'Draft'),
            ('PENDING', 'Pending'),
            ('CONFIRMED', 'Confirmed'),
            ('PAID', 'Paid'),
            ('PARTIALLY_PAID', 'Partially Paid'),
            ('CANCELLED', 'Cancelled'),
        ],
        default='DRAFT',
        db_index=True
    )
    
    # POD Status
    pod_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'POD Pending'),
            ('COMPLETED', 'POD Completed'),
        ],
        default='PENDING',
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
    
    # Payment Tracking
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Additional Information
    remarks = models.TextField(blank=True)
    
    # Custom managers
    objects = models.Manager()
    filtered_objects = ChannelPartnerManager()
    
    class Meta:
        db_table = 'invoice'
        ordering = ['-invoice_date', '-created_on']
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
        permissions = [
            ('cancel_invoice', 'Can cancel invoice'),
        ]
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['invoice_date', 'status']),
            models.Index(fields=['sales_order']),
            models.Index(fields=['-created_on']),
        ]
    
    def __str__(self):
        return f"{self.invoice_number} - {self.invoice_date}"
    
    @staticmethod
    def generate_invoice_number(location_code=None):
        """Generate invoice number atomically.
        With location: INV-LOC-FY-INCREMENT
        Without location: INV-FY-INCREMENT
        """
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
        
        if location_code:
            loc_code = location_code[:3].upper()
            prefix = f"INV-{loc_code}-{fy_string}"
        else:
            prefix = f"INV-{fy_string}"
        
        # Use atomic transaction with SELECT FOR UPDATE to prevent race conditions
        with transaction.atomic():
            # Get all matching invoice numbers with row locking
            invoice_numbers = Invoice.objects.filter(
                invoice_number__startswith=prefix
            ).select_for_update().values_list('invoice_number', flat=True)
            
            # Find the maximum numeric suffix
            max_suffix = 0
            for inv in invoice_numbers:
                match = re.search(r'-(\d+)$', inv or '')
                if match:
                    try:
                        max_suffix = max(max_suffix, int(match.group(1)))
                    except ValueError:
                        continue
            
            return f"{prefix}-{max_suffix + 1}"
    
    def calculate_totals(self):
        """Calculate invoice totals from line items"""
        items = self.items.all()
        self.subtotal = sum(item.quantity * item.rate for item in items)
        self.discount_amount = sum(item.discount_amount for item in items)
        self.taxable_amount = sum(item.taxable_amount for item in items)
        self.tax_amount = sum(item.tax_amount for item in items)
        
        self.grand_total = (
            self.taxable_amount +
            self.tax_amount +
            self.freight_charges +
            self.other_charges +
            self.round_off
        )
        
        # Calculate balance
        self.balance_amount = self.grand_total - self.paid_amount
        self.save()
    
    def update_payment_status(self):
        """Update invoice status based on payments"""
        if self.paid_amount >= self.grand_total:
            self.status = 'PAID'
        elif self.paid_amount > 0:
            self.status = 'PARTIALLY_PAID'
        self.save()


class InvoiceItem(CoreModel):
    """Invoice line items"""

    CODE_PREFIX = 'INVI'
    
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items'
    )
    sales_order_item = models.ForeignKey(
        SalesOrderItem,
        on_delete=models.RESTRICT,
        related_name='invoice_items'
    )
    
    # Quantity
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    
    # Pricing
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Tax
    taxable_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cgst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    cgst_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    sgst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    sgst_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    igst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    igst_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cess_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    cess_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Total
    line_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'invoice_item'
        ordering = ['created_on']
        verbose_name = 'Invoice Item'
        verbose_name_plural = 'Invoice Items'
        indexes = [
            models.Index(fields=['invoice', 'sales_order_item']),
        ]
    
    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.sales_order_item.item.name}"


class Payment(CoreModel):
    """Payment tracking for invoices"""

    CODE_PREFIX = 'PAY'
    
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    
    # Payment Information
    payment_date = models.DateField(db_index=True)
    payment_mode = models.CharField(
        max_length=20,
        choices=[
            ('CASH', 'Cash'),
            ('CHEQUE', 'Cheque'),
            ('NEFT', 'NEFT'),
            ('RTGS', 'RTGS'),
            ('UPI', 'UPI'),
            ('CARD', 'Card'),
        ]
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Payment Details
    reference_number = models.CharField(max_length=100, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    remarks = models.TextField(blank=True)
    
    class Meta:
        db_table = 'payment'
        ordering = ['-payment_date', '-created_on']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        indexes = [
            models.Index(fields=['invoice', '-payment_date']),
        ]
    
    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.amount}"
    
    def save(self, *args, **kwargs):
        """Update invoice paid amount after payment save"""
        super().save(*args, **kwargs)
        
        # Update invoice paid amount
        total_paid = self.invoice.payments.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')
        
        self.invoice.paid_amount = total_paid
        self.invoice.balance_amount = self.invoice.grand_total - total_paid
        self.invoice.update_payment_status()
