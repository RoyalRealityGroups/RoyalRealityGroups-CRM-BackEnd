"""
Saved Filters Models

Allows users to save and reuse filter configurations.
"""

from django.db import models
from django.conf import settings
from Core.Users.models import BaseModel,CodeMixModel


class SavedFilter(CodeMixModel):
    """
    Model to store user's saved filter configurations.
    """
    
    # Filter identification
    name = models.CharField(max_length=255, help_text="Filter name")
    description = models.TextField(blank=True, null=True, help_text="Filter description")
    
    # Filter configuration
    filter_config = models.JSONField(help_text="JSON configuration of filters")
    
    # Context
    screen_name = models.CharField(
        max_length=255,
        help_text="Screen/page where filter applies (e.g., 'orders', 'invoices')"
    )
    
    # Visibility
    is_public = models.BooleanField(
        default=False,
        help_text="If True, filter is visible to all users"
    )
    is_default = models.BooleanField(
        default=False,
        help_text="If True, filter is applied by default"
    )
    
    # Metadata
    usage_count = models.IntegerField(default=0, help_text="Number of times filter has been used")
    last_used = models.DateTimeField(null=True, blank=True, help_text="Last time filter was used")
    
    class Meta:
        db_table = 'saved_filters'
        verbose_name = 'Saved Filter'
        verbose_name_plural = 'Saved Filters'
        ordering = ['-created_on']
        indexes = [
            models.Index(fields=['screen_name', 'is_deleted']),
            models.Index(fields=['created_by_type', 'created_by_identifier']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.screen_name})"


class FilterPreset(CodeMixModel):
    """
    Predefined filter templates for common use cases.
    """
    
    # Preset identification
    name = models.CharField(max_length=255, help_text="Preset name")
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True, help_text="Icon name")
    
    # Configuration
    filter_config = models.JSONField(help_text="JSON configuration of filters")
    screen_name = models.CharField(max_length=255, help_text="Applicable screen")
    
    # Display
    sort_order = models.IntegerField(default=0, help_text="Display order")
    is_active = models.BooleanField(default=True)
    
    # Examples:
    # - "Today's Orders" -> created_on__gte: today
    # - "Pending Approval" -> status: pending
    # - "High Value" -> amount__gte: 10000
    
    class Meta:
        db_table = 'filter_presets'
        verbose_name = 'Filter Preset'
        verbose_name_plural = 'Filter Presets'
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.screen_name})"
