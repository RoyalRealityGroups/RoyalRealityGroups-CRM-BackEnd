from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from Core.Users.models import BaseModel


class ChannelPartnerAttachment(BaseModel):
    """Attachments for Channel Partners (Distributor, Superstockist, Retailer)"""
    
    ATTACHMENT_TYPE_CHOICES = [
        ('AADHAR', 'Aadhar'),
        ('PAN', 'PAN'),
        ('AGREEMENT', 'Agreement'),
        ('SHOP_PICTURE', 'Shop Picture'),
        ('CANCELLED_CHEQUE', 'Cancelled Cheque'),
        ('OWNER_PICTURE', 'Representative/Shop Owner Picture'),
        ('OTHER', 'Other'),
    ]
    
    # Generic relation to support all channel partner types
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    attachment_type = models.CharField(max_length=20, choices=ATTACHMENT_TYPE_CHOICES, help_text='Type of attachment')
    file = models.FileField(upload_to='channel_partners/attachments/%Y/%m/', help_text='Attachment file')
    original_filename = models.CharField(max_length=255, blank=True, null=True, help_text='Original filename')
    description = models.CharField(max_length=255, blank=True, null=True, help_text='Description for other attachments')
    
    class Meta:
        db_table = 'channel_partner_attachments'
        ordering = ['-created_on']
        verbose_name = 'Channel Partner Attachment'
        verbose_name_plural = 'Channel Partner Attachments'
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['attachment_type']),
        ]
    
    def __str__(self):
        return f"{self.get_attachment_type_display()} - {self.content_object}"
