from django.db import models
from Core.Users.models import BaseModel
from .models import SalesOrder


class SalesOrderAttachment(BaseModel):
    """Attachments for Sales Orders"""
    
    sales_order = models.ForeignKey(
        SalesOrder, 
        on_delete=models.CASCADE, 
        related_name='attachments'
    )
    file = models.FileField(
        upload_to='sales_orders/attachments/%Y/%m/', 
        help_text='Attachment file'
    )
    original_filename = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        help_text='Original filename'
    )
    description = models.CharField(
        max_length=500, 
        blank=True, 
        null=True, 
        help_text='Description for attachment'
    )
    
    class Meta:
        db_table = 'sales_order_attachments'
        ordering = ['-created_on']
        verbose_name = 'Sales Order Attachment'
        verbose_name_plural = 'Sales Order Attachments'
        indexes = [
            models.Index(fields=['sales_order']),
        ]
    
    def __str__(self):
        return f"{self.original_filename or 'File'} - {self.sales_order.order_number}"
