from django.db import models
from django.core.validators import RegexValidator
from Core.Users.models import BaseModel, CoreModel, ChannelPartnerManager
from django.utils import timezone
import uuid


class ProofOfDelivery(CoreModel):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Delivered'),
        ('FAILED', 'Failed Delivery'),
        ('PARTIAL', 'Partial Delivery'),
    ]

    CODE_PREFIX = 'POD'

    pod_number = models.CharField(max_length=50, unique=True, null=True, db_index=True)
    invoice = models.ForeignKey(
        'Invoice.Invoice',
        on_delete=models.PROTECT,
        related_name='proofs'
    )
    sales_order = models.ForeignKey(
        'Sales.SalesOrder',
        on_delete=models.PROTECT,
        related_name='proofs'
    )
    customer_type = models.CharField(max_length=20, db_index=True, default='RETAILER')
    customer_id = models.UUIDField(db_index=True, null=True, blank=True)

    pod_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    
    # Receiver Details
    receiver_name = models.CharField(max_length=120, default='', blank=True)
    receiver_phone = models.CharField(
        max_length=50, 
        default='', 
        blank=True,
    )
    
    # Delivery Details
    delivered_by = models.CharField(max_length=120, default='', blank=True)
    delivered_date = models.DateField(null=True, blank=True)
    
    remarks = models.TextField(blank=True, default='')

    objects = models.Manager()
    filtered_objects = ChannelPartnerManager()

    class Meta:
        db_table = 'proof_of_delivery'
        ordering = ['-delivered_date']
        indexes = [
            models.Index(fields=['invoice']),
            models.Index(fields=['sales_order']),
            models.Index(fields=['status']),
            models.Index(fields=['customer_type', 'customer_id']),
        ]

    def __str__(self):
        return f"{self.pod_number} - {self.invoice.invoice_number}"


class ProofOfDeliveryFile(BaseModel):
    proof = models.ForeignKey(
        ProofOfDelivery,
        on_delete=models.CASCADE,
        related_name='files'
    )
    file = models.FileField(upload_to='pod/')
    original_filename = models.CharField(max_length=255, blank=True, default='')
    description = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        db_table = 'proof_of_delivery_file'
        ordering = ['-created_on']
        indexes = [
            models.Index(fields=['proof']),
        ]

    def __str__(self):
        return f"POD File {self.original_filename or self.file.name}"
