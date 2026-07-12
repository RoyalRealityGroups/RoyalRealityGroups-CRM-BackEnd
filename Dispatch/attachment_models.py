from django.db import models
from Core.Users.models import BaseModel


class DispatchPlanAttachment(BaseModel):
    """Attachments for Dispatch Plans"""
    
    ATTACHMENT_TYPE_CHOICES = [
        ('VEHICLE_RC', 'Vehicle RC'),
        ('VEHICLE_INSURANCE', 'Vehicle Insurance'),
        ('VEHICLE_PERMIT', 'Vehicle Permit'),
        ('VEHICLE_POLLUTION', 'Vehicle Pollution Certificate'),
        ('DRIVER_LICENSE', 'Driver License'),
        ('OTHER', 'Other'),
    ]
    
    dispatch_plan = models.ForeignKey('DispatchPlan', on_delete=models.CASCADE, related_name='attachments')
    attachment_type = models.CharField(max_length=20, choices=ATTACHMENT_TYPE_CHOICES)
    file = models.FileField(upload_to='dispatch_plans/attachments/%Y/%m/')
    original_filename = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        db_table = 'dispatch_plan_attachments'
        ordering = ['-created_on']
    
    def __str__(self):
        return f"{self.get_attachment_type_display()} - {self.dispatch_plan.dispatch_number}"
