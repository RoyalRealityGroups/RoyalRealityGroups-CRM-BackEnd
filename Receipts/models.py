from django.db import models
from decimal import Decimal
from Core.Users.models import CoreModel, ChannelPartnerManager
from Masters.models import Company, Location
from Invoice.models import Invoice


class Receipt(CoreModel):
    """Receipt header - bulk payment from customer"""
    
    CODE_PREFIX = 'RCP'
    
    # Receipt Information
    receipt_number = models.CharField(max_length=50, unique=True, db_index=True)
    receipt_date = models.DateField(db_index=True)
    
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
    retailer = models.ForeignKey('Masters.Retailer', on_delete=models.PROTECT, null=True, blank=True, related_name='receipts')
    distributor = models.ForeignKey('Masters.Distributor', on_delete=models.PROTECT, null=True, blank=True, related_name='receipts')
    superstockist = models.ForeignKey('Masters.Superstockist', on_delete=models.PROTECT, null=True, blank=True, related_name='receipts')
    
    # Payment Details
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
            ('CREDIT', 'Credit'),
        ]
    )
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Payment Reference
    reference_number = models.CharField(max_length=100, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    remarks = models.TextField(blank=True)
    
    # Company & Location
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name='receipts'
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        related_name='receipts'
    )
    
    # Custom managers
    objects = models.Manager()
    filtered_objects = ChannelPartnerManager()
    
    class Meta:
        db_table = 'receipt'
        ordering = ['-receipt_date', '-created_on']
        verbose_name = 'Receipt'
        verbose_name_plural = 'Receipts'
        permissions = [
            ('cancel_receipt', 'Can cancel receipt'),
        ]
        indexes = [
            models.Index(fields=['receipt_number']),
            models.Index(fields=['receipt_date']),
            models.Index(fields=['payment_date']),
            models.Index(fields=['customer_type']),
            models.Index(fields=['company', 'location']),
            models.Index(fields=['-created_on']),
        ]
    
    def __str__(self):
        return f"{self.receipt_number} - {self.receipt_date}"
    
    @staticmethod
    def generate_receipt_number(location_code):
        """
        Generate receipt number in format: RCP-LOC-FY-INCREMENT
        Example: RCP-VSK-25-26-1
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
        loc_code = location_code[:3].upper()
        prefix = f"RCP-{loc_code}-{fy_string}"
        
        # Use atomic transaction with SELECT FOR UPDATE to prevent race conditions
        with transaction.atomic():
            receipt_numbers = Receipt.objects.filter(
                receipt_number__startswith=prefix
            ).select_for_update().values_list('receipt_number', flat=True)
            
            # Find the maximum numeric suffix
            max_suffix = 0
            for rcpt in receipt_numbers:
                match = re.search(r'-(\d+)$', rcpt or '')
                if match:
                    try:
                        max_suffix = max(max_suffix, int(match.group(1)))
                    except ValueError:
                        continue
            
            return f"{prefix}-{max_suffix + 1}"
    
    def update_invoice_payments(self):
        """Update paid_amount and balance_amount for all allocated invoices"""
        for allocation in self.allocations.all():
            invoice = allocation.invoice
            
            # Recalculate total paid from all approved receipt allocations
            total_paid = ReceiptAllocation.objects.filter(
                invoice=invoice,
                receipt__authorized_status=2  # Only approved receipts
            ).aggregate(total=models.Sum('allocated_amount'))['total'] or Decimal('0')
            
            invoice.paid_amount = total_paid
            invoice.balance_amount = invoice.grand_total - total_paid
            invoice.update_payment_status()
            invoice.save()
    
    def create_customer_credit(self):
        """Create customer credit for unallocated amount"""
        if self.authorized_status != 2:  # Only for approved receipts
            return
        
        allocated_total = self.allocations.aggregate(
            total=models.Sum('allocated_amount')
        )['total'] or Decimal('0')
        
        unallocated = self.total_amount - allocated_total
        
        if unallocated > 0:
            CustomerCredit.objects.create(
                receipt=self,
                customer_type=self.customer_type,
                retailer=self.retailer,
                distributor=self.distributor,
                superstockist=self.superstockist,
                credit_amount=unallocated,
                available_amount=unallocated,
                company=self.company,
                location=self.location,
                remarks=f'Unallocated amount from receipt {self.receipt_number}'
            )
    
    def get_customer_name(self):
        """Get customer name based on customer_type"""
        if self.customer_type == 'RETAILER' and self.retailer:
            return self.retailer.name
        elif self.customer_type == 'DISTRIBUTOR' and self.distributor:
            return self.distributor.name
        elif self.customer_type == 'SUPERSTOCKIST' and self.superstockist:
            return self.superstockist.name
        return None


class CustomerCredit(CoreModel):
    """Track customer advance payments/credits for future use"""
    
    CODE_PREFIX = 'CRC'
    
    receipt = models.ForeignKey(
        Receipt,
        on_delete=models.PROTECT,
        related_name='credits',
        null=True,
        blank=True
    )
    
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
    retailer = models.ForeignKey('Masters.Retailer', on_delete=models.PROTECT, null=True, blank=True, related_name='credits')
    distributor = models.ForeignKey('Masters.Distributor', on_delete=models.PROTECT, null=True, blank=True, related_name='credits')
    superstockist = models.ForeignKey('Masters.Superstockist', on_delete=models.PROTECT, null=True, blank=True, related_name='credits')
    
    credit_amount = models.DecimalField(max_digits=15, decimal_places=2)
    available_amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='customer_credits')
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name='customer_credits')
    
    remarks = models.TextField(blank=True)
    
    objects = models.Manager()
    filtered_objects = ChannelPartnerManager()
    
    class Meta:
        db_table = 'customer_credit'
        ordering = ['-created_on']
        verbose_name = 'Customer Credit'
        verbose_name_plural = 'Customer Credits'
        indexes = [
            models.Index(fields=['customer_type']),
            models.Index(fields=['company', 'location']),
            models.Index(fields=['-created_on']),
        ]
    
    def __str__(self):
        customer_name = ''
        if self.customer_type == 'RETAILER' and self.retailer:
            customer_name = self.retailer.name
        elif self.customer_type == 'DISTRIBUTOR' and self.distributor:
            customer_name = self.distributor.name
        elif self.customer_type == 'SUPERSTOCKIST' and self.superstockist:
            customer_name = self.superstockist.name
        return f"{customer_name} - Credit: {self.available_amount}"


class CreditUtilization(models.Model):
    """Track usage of customer credits against receipts"""
    
    credit = models.ForeignKey(CustomerCredit, on_delete=models.PROTECT, related_name='utilizations')
    receipt = models.ForeignKey(Receipt, on_delete=models.PROTECT, related_name='credit_utilizations')
    utilized_amount = models.DecimalField(max_digits=15, decimal_places=2)
    utilized_on = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True)
    
    class Meta:
        db_table = 'credit_utilization'
        ordering = ['-utilized_on']
        verbose_name = 'Credit Utilization'
        verbose_name_plural = 'Credit Utilizations'
    
    def __str__(self):
        return f"{self.credit} -> {self.receipt.receipt_number}: {self.utilized_amount}"


class CustomerLedgerEntry(CoreModel):
    """Common customer ledger table for invoice and receipt postings."""

    CODE_PREFIX = 'CLG'

    DOCUMENT_TYPE_CHOICES = [
        ('INVOICE', 'Invoice'),
        ('RECEIPT', 'Receipt'),
    ]

    EVENT_TYPE_CHOICES = [
        ('INVOICE_POSTED', 'Invoice Posted'),
        ('RECEIPT_POSTED', 'Receipt Posted'),
    ]

    ENTRY_STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
    ]

    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES, db_index=True)
    document_id = models.UUIDField(db_index=True)
    document_number = models.CharField(max_length=50, db_index=True)
    document_date = models.DateField(db_index=True)
    posting_date = models.DateField(db_index=True)
    event_type = models.CharField(max_length=30, choices=EVENT_TYPE_CHOICES, db_index=True)

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
        'Masters.Retailer',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='ledger_entries'
    )
    distributor = models.ForeignKey(
        'Masters.Distributor',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='ledger_entries'
    )
    superstockist = models.ForeignKey(
        'Masters.Superstockist',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='ledger_entries'
    )

    debit_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credit_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    entry_status = models.CharField(max_length=10, choices=ENTRY_STATUS_CHOICES, default='ACTIVE', db_index=True)
    remarks = models.TextField(blank=True)
    meta_data = models.JSONField(default=dict, blank=True)

    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='customer_ledger_entries')
    location = models.ForeignKey(Location, on_delete=models.PROTECT, null=True, blank=True, related_name='customer_ledger_entries')
    objects = models.Manager()
    filtered_objects = ChannelPartnerManager()

    class Meta:
        db_table = 'customer_ledger_entry'
        ordering = ['posting_date', 'created_on']
        verbose_name = 'Customer Ledger Entry'
        verbose_name_plural = 'Customer Ledger Entries'
        indexes = [
            models.Index(fields=['document_type', 'document_id']),
            models.Index(fields=['customer_type', 'posting_date']),
            models.Index(fields=['company', 'location', 'posting_date']),
            models.Index(fields=['entry_status', '-created_on']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['document_type', 'document_id', 'event_type'],
                name='customer_ledger_unique_document_event'
            ),
            models.CheckConstraint(
                check=models.Q(debit_amount__gte=0) & models.Q(credit_amount__gte=0),
                name='customer_ledger_non_negative_amounts'
            ),
            models.CheckConstraint(
                check=(
                    (models.Q(debit_amount__gt=0) & models.Q(credit_amount=0)) |
                    (models.Q(credit_amount__gt=0) & models.Q(debit_amount=0))
                ),
                name='customer_ledger_single_sided_entry'
            ),
        ]

    def __str__(self):
        return (
            f"{self.document_type}:{self.document_number} | "
            f"D:{self.debit_amount} C:{self.credit_amount}"
        )


class ReceiptAllocation(CoreModel):
    """Receipt allocation to individual invoices"""
    
    CODE_PREFIX = 'RCPA'
    
    receipt = models.ForeignKey(
        Receipt,
        on_delete=models.CASCADE,
        related_name='allocations'
    )
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.RESTRICT,
        related_name='receipt_allocations'
    )
    allocated_amount = models.DecimalField(max_digits=15, decimal_places=2)
    allocation_sequence = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'receipt_allocation'
        ordering = ['allocation_sequence']
        verbose_name = 'Receipt Allocation'
        verbose_name_plural = 'Receipt Allocations'
        indexes = [
            models.Index(fields=['receipt', 'invoice']),
            models.Index(fields=['invoice']),
        ]
    
    def __str__(self):
        return f"{self.receipt.receipt_number} -> {self.invoice.invoice_number}: {self.allocated_amount}"


class ReceiptAttachment(models.Model):
    """Attachments for receipts (cheque images, bank statements, etc.)"""
    
    receipt = models.ForeignKey(
        Receipt,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='receipts/%Y/%m/')
    attachment_type = models.CharField(
        max_length=50,
        choices=[
            ('CHEQUE', 'Cheque Image'),
            ('BANK_STATEMENT', 'Bank Statement'),
            ('OTHER', 'Other'),
        ],
        default='OTHER'
    )
    remarks = models.TextField(blank=True)
    uploaded_on = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'receipt_attachment'
        ordering = ['-uploaded_on']
        verbose_name = 'Receipt Attachment'
        verbose_name_plural = 'Receipt Attachments'
    
    def __str__(self):
        return f"{self.receipt.receipt_number} - {self.attachment_type}"
