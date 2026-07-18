"""
Module 9 - Document Management
Upload and store documents linked to Projects, Leads, and Bookings.
Supported types: Brochures, Layout Plans, Approval Docs, Customer KYC,
                 Booking Forms, Agreements.
Supported formats: PDF, JPG, PNG, Excel.
"""
import os
from django.db import models
from Core.Users.models import CoreModel


DOCUMENT_TYPE_CHOICES = [
    ('BROCHURE', 'Brochure'),
    ('LAYOUT_PLAN', 'Layout Plan'),
    ('FLOOR_PLAN', 'Floor Plan'),
    ('APPROVAL_DOC', 'Approval Document'),
    ('CUSTOMER_KYC', 'Customer KYC'),
    ('BOOKING_FORM', 'Booking Form'),
    ('AGREEMENT', 'Agreement'),
    ('PHOTO', 'Photo'),
    ('OTHER', 'Other'),
]

LINKED_TO_CHOICES = [
    ('PROJECT', 'Project'),
    ('LEAD', 'Lead'),
    ('BOOKING', 'Booking'),
]


def document_upload_path(instance, filename):
    """Organise uploads into sub-folders by linked entity type."""
    ext = filename.rsplit('.', 1)[-1].lower()
    safe_name = os.path.basename(filename)
    entity = instance.linked_to.lower() if instance.linked_to else 'general'
    return f"documents/{entity}/{instance.document_type.lower()}/{safe_name}"


class Document(CoreModel):
    """
    Generic document store for Module 9.
    Can be linked to a Project, Lead, or Booking.
    """
    CODE_PREFIX = 'DOC'

    # Document metadata
    title = models.CharField(max_length=200, db_index=True)
    document_type = models.CharField(
        max_length=20, choices=DOCUMENT_TYPE_CHOICES, db_index=True
    )
    description = models.TextField(blank=True, null=True)

    # The actual file
    file = models.FileField(
        upload_to=document_upload_path,
        help_text='Supported: PDF, JPG, PNG, XLSX'
    )
    original_filename = models.CharField(max_length=255, blank=True, null=True)
    file_size = models.PositiveIntegerField(null=True, blank=True, help_text='File size in bytes')

    # Link to entity
    linked_to = models.CharField(
        max_length=10, choices=LINKED_TO_CHOICES, default='PROJECT'
    )
    project = models.ForeignKey(
        'Masters.Project',
        on_delete=models.CASCADE,
        related_name='documents',
        null=True, blank=True,
    )
    lead = models.ForeignKey(
        'Lead.Lead',
        on_delete=models.CASCADE,
        related_name='documents',
        null=True, blank=True,
    )
    booking = models.ForeignKey(
        'Booking.Booking',
        on_delete=models.CASCADE,
        related_name='documents',
        null=True, blank=True,
    )

    is_public = models.BooleanField(
        default=False,
        help_text='Public documents are visible on the customer website'
    )

    class Meta:
        ordering = ['-created_on']
        permissions = [
            ("export_document", "Can export documents"),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_document_type_display()})"

    def save(self, *args, **kwargs):
        if self.file and not self.original_filename:
            self.original_filename = os.path.basename(self.file.name)
        if self.file and hasattr(self.file, 'size') and not self.file_size:
            try:
                self.file_size = self.file.size
            except Exception:
                pass
        super().save(*args, **kwargs)

    @property
    def file_url(self):
        if self.file:
            return self.file.url
        return None

    @property
    def file_extension(self):
        if self.original_filename:
            return self.original_filename.rsplit('.', 1)[-1].lower()
        return None
