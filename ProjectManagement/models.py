from django.db import models

from Core.Users.models import CoreModel, BaseModel


class Project(CoreModel):
    """
    Real Estate Project Master.
    Stores projects (Plot/Flat developments) that Leads → Site Visits → Bookings hang off.
    """
    CODE_PREFIX = 'PROJ'

    PROJECT_STATUS_CHOICES = [
        ('UPCOMING', 'Upcoming'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('SOLD_OUT', 'Sold Out'),
    ]

    PROJECT_TYPE_CHOICES = [
        ('PLOT', 'Plot'),
        ('FLAT', 'Flat'),
        ('VILLA', 'Villa'),
        ('MIXED', 'Mixed'),
    ]

    APPROVAL_TYPE_CHOICES = [
        ('GVMC', 'GVMC'),
        ('VMRDA', 'VMRDA'),
        ('DTCP', 'DTCP'),
        ('HMDA', 'HMDA'),
        ('PANCHAYAT', 'Panchayat'),
        ('PENDING', 'Pending'),
        ('NA', 'N/A'),
    ]

    name = models.CharField(max_length=200, db_index=True)
    developer_name = models.CharField(max_length=200, blank=True, null=True)
    project_type = models.CharField(
        max_length=20, choices=PROJECT_TYPE_CHOICES, default='PLOT', db_index=True,
    )
    location = models.CharField(
        max_length=255, blank=True, null=True,
        help_text='Project location (free text)',
    )
    approval_type = models.CharField(
        max_length=20, choices=APPROVAL_TYPE_CHOICES, default='PENDING',
    )

    status = models.CharField(
        max_length=20, choices=PROJECT_STATUS_CHOICES, default='UPCOMING', db_index=True,
    )
    sub = models.ImageField(upload_to='projects/', null=True, blank=True)

    # New fields for enhanced project presentation
    # Overview & Description
    overview = models.TextField(
        blank=True, null=True,
        help_text='Brief project overview (shown in cards/previews)',
    )
    description = models.TextField(
        blank=True, null=True,
        help_text='Detailed project description',
    )

    # Amenities & Specifications
    amenities = models.TextField(
        blank=True, null=True,
        help_text='List of amenities (can be JSON or comma-separated)',
    )
    specifications = models.TextField(
        blank=True, null=True,
        help_text='Project specifications (can be JSON or structured text)',
    )

    # Floor Plans (text description)
    floor_plans_text = models.TextField(
        blank=True, null=True,
        help_text='Floor plan details as text description',
    )

    # Media - Images
    elevation_image = models.ImageField(
        upload_to='projects/elevation/', null=True, blank=True,
        help_text='Main elevation image for project preview',
    )
    thumbnail = models.ImageField(
        upload_to='projects/thumbnails/', null=True, blank=True,
        help_text='Thumbnail image for cards/lists',
    )

    # Floor Plans (can store multiple as JSON array of URLs or use separate model)
    floor_plans = models.JSONField(
        default=list, blank=True,
        help_text='List of floor plan image URLs',
    )

    # Gallery (multiple images as JSON array)
    gallery = models.JSONField(
        default=list, blank=True,
        help_text='List of gallery image URLs',
    )

    # Documents
    brochure = models.FileField(
        upload_to='projects/brochures/', null=True, blank=True,
        help_text='Project brochure PDF',
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['project_type']),
            models.Index(fields=['is_active']),
        ]
        permissions = [
            ("export_project", "Can export projects"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def delete(self, *args, **kwargs):
        """Soft-delete: flip is_deleted instead of removing the row."""
        from django.utils import timezone
        self.is_deleted = True
        self.modified_on = timezone.now()
        self.save(update_fields=['is_deleted', 'modified_on'])

    def hard_delete(self, *args, **kwargs):
        """Force a real DELETE — bypass soft-delete."""
        super().delete(*args, **kwargs)


class ProjectStatusHistory(BaseModel):
    """
    Audit trail for Project status changes.
    Mirrors the LeadStatusHistory pattern from the Lead app.
    """
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='status_history',
    )
    from_status = models.CharField(
        max_length=20, choices=Project.PROJECT_STATUS_CHOICES,
        blank=True, null=True,
    )
    to_status = models.CharField(
        max_length=20, choices=Project.PROJECT_STATUS_CHOICES,
    )
    changed_by_identifier = models.CharField(max_length=255, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_on']
        verbose_name = 'Project Status History'
        verbose_name_plural = 'Project Status History'
        indexes = [
            models.Index(fields=['project', '-created_on']),
        ]

    def __str__(self):
        return f"{self.project.code}: {self.from_status or 'NEW'} → {self.to_status}"


class ProjectImage(BaseModel):
    """
    Stores multiple images for project gallery, floor plans, and elevation images.
    """
    IMAGE_TYPE_CHOICES = [
        ('GALLERY', 'Gallery'),
        ('FLOOR_PLAN', 'Floor Plan'),
        ('ELEVATION', 'Elevation'),
    ]

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='images',
    )
    image = models.ImageField(upload_to='projects/images/')
    image_type = models.CharField(
        max_length=20, choices=IMAGE_TYPE_CHOICES, default='GALLERY',
    )
    title = models.CharField(max_length=200, blank=True, null=True)
    description = models.CharField(max_length=500, blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'created_on']
        verbose_name = 'Project Image'
        verbose_name_plural = 'Project Images'

    def __str__(self):
        return f"{self.project.code} - {self.image_type} - {self.title or self.id}"
