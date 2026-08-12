"""
Availability List Module
Manages marketing/sales-facing project folders with blocks/sections and individual units.

Structure:
  AvailabilityProject  (folder — e.g. "Iconica", "MVV")
    └── AvailabilityBlock  (block/section — "Block A", "Tower 1", or just "Plots")
          └── AvailabilityUnit  (individual unit — flat or plot)

Supports both flat-based (multi-block towers) and plot-based layouts.
"""
from django.db import models
from Core.Users.models import CoreModel, BaseModel

# ──────────────────────────────────────────────────────────────────────────────
# CHOICES
# ──────────────────────────────────────────────────────────────────────────────

PROJECT_TYPE_CHOICES = [
    ('FLATS', 'Flats / Apartments'),
    ('PLOTS', 'Plots / Villas'),
    ('MIXED', 'Mixed (Flats + Plots)'),
]

PROJECT_STATUS_CHOICES = [
    ('UPCOMING', 'Upcoming'),
    ('ACTIVE', 'Active / On Sale'),
    ('COMPLETED', 'Completed'),
    ('SOLD_OUT', 'Sold Out'),
]

APPROVAL_TYPE_CHOICES = [
    ('GVMC', 'GVMC'),
    ('VMRDA', 'VMRDA'),
    ('DTCP', 'DTCP'),
    ('HMDA', 'HMDA'),
    ('RERA', 'RERA'),
    ('PANCHAYAT', 'Panchayat'),
    ('PENDING', 'Approval Pending'),
    ('NA', 'Not Applicable'),
]

UNIT_STATUS_CHOICES = [
    ('AVAILABLE', 'Available'),
    ('BLOCKED', 'Blocked / Hold'),
    ('BOOKED', 'Booked'),
    ('REGISTERED', 'Registered'),
]

UNIT_TYPE_CHOICES = [
    ('1BHK', '1 BHK'),
    ('2BHK', '2 BHK'),
    ('3BHK', '3 BHK'),
    ('4BHK', '4 BHK'),
    ('PENTHOUSE', 'Penthouse'),
    ('STUDIO', 'Studio'),
    ('DUPLEX', 'Duplex'),
    ('PLOT', 'Plot'),
    ('VILLA', 'Villa'),
    ('COMMERCIAL', 'Commercial'),
    ('OTHER', 'Other'),
]

FACING_CHOICES = [
    ('EAST', 'East'),
    ('WEST', 'West'),
    ('NORTH', 'North'),
    ('SOUTH', 'South'),
    ('NE', 'North East'),
    ('NW', 'North West'),
    ('SE', 'South East'),
    ('SW', 'South West'),
]


# ──────────────────────────────────────────────────────────────────────────────
# AVAILABILITY PROJECT  (the "folder")
# ──────────────────────────────────────────────────────────────────────────────

class AvailabilityProject(CoreModel):
    """
    Top-level project / venture folder.
    E.g.: Iconica, MVV, MK Heights, etc.
    """
    CODE_PREFIX = 'AVP'

    name = models.CharField(max_length=200, db_index=True, help_text="Project / venture name")
    developer_name = models.CharField(max_length=200, blank=True, null=True, help_text="Builder or developer")
    project_type = models.CharField(max_length=10, choices=PROJECT_TYPE_CHOICES, default='FLATS', db_index=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    total_area = models.CharField(max_length=100, blank=True, null=True, help_text="e.g. 2.5 Acres")
    price_range_min = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    price_range_max = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    approval_type = models.CharField(max_length=20, choices=APPROVAL_TYPE_CHOICES, default='PENDING')
    approval_number = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=PROJECT_STATUS_CHOICES, default='ACTIVE', db_index=True)
    possession_date = models.DateField(null=True, blank=True, help_text="Expected possession / handover date")
    contact_person = models.CharField(max_length=200, blank=True, null=True)
    contact_phone = models.CharField(max_length=15, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    amenities = models.TextField(blank=True, null=True, help_text="Comma-separated or free text list")
    rera_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="RERA Number")
    is_active = models.BooleanField(default=True)

    # Media
    thumbnail = models.ImageField(upload_to='availability/thumbnails/', null=True, blank=True)
    brochure = models.FileField(upload_to='availability/brochures/', null=True, blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Availability Project'
        verbose_name_plural = 'Availability Projects'
        permissions = [
            ("export_availabilityproject", "Can export availability projects"),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_project_type_display()})"

    @property
    def total_units(self):
        return AvailabilityUnit.objects.filter(block__project=self, is_deleted=False).count()

    @property
    def available_units(self):
        return AvailabilityUnit.objects.filter(block__project=self, status='AVAILABLE', is_deleted=False).count()

    @property
    def booked_units(self):
        return AvailabilityUnit.objects.filter(block__project=self, status='BOOKED', is_deleted=False).count()

    @property
    def blocked_units(self):
        return AvailabilityUnit.objects.filter(block__project=self, status='BLOCKED', is_deleted=False).count()

    @property
    def registered_units(self):
        return AvailabilityUnit.objects.filter(block__project=self, status='REGISTERED', is_deleted=False).count()


# ──────────────────────────────────────────────────────────────────────────────
# AVAILABILITY PROJECT IMAGE
# ──────────────────────────────────────────────────────────────────────────────

class AvailabilityProjectImage(BaseModel):
    """Gallery images for an AvailabilityProject."""
    IMAGE_TYPE_CHOICES = [
        ('GALLERY', 'Gallery'),
        ('FLOOR_PLAN', 'Floor Plan'),
        ('ELEVATION', 'Elevation / 3D View'),
        ('AMENITY', 'Amenity'),
        ('LOCATION_MAP', 'Location Map'),
    ]
    project = models.ForeignKey(
        AvailabilityProject, on_delete=models.CASCADE, related_name='images'
    )
    image = models.ImageField(upload_to='availability/images/')
    image_type = models.CharField(max_length=20, choices=IMAGE_TYPE_CHOICES, default='GALLERY')
    title = models.CharField(max_length=200, blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'created_on']

    def __str__(self):
        return f"{self.project.name} — {self.get_image_type_display()}"


# ──────────────────────────────────────────────────────────────────────────────
# AVAILABILITY BLOCK  (block / tower / section)
# ──────────────────────────────────────────────────────────────────────────────

class AvailabilityBlock(BaseModel):
    """
    A block, tower, or section within a project.
    For plots-only projects there is typically one block ("Plots").
    For apartment projects there may be multiple towers / wings.
    """
    project = models.ForeignKey(
        AvailabilityProject, on_delete=models.CASCADE, related_name='blocks'
    )
    name = models.CharField(max_length=100, help_text="e.g. Block A, Tower 1, East Wing, Plots")
    description = models.CharField(max_length=500, blank=True, null=True)
    total_floors = models.PositiveIntegerField(null=True, blank=True, help_text="Applicable for flat towers")
    order = models.PositiveIntegerField(default=0, help_text="Display order")

    class Meta:
        ordering = ['project', 'order', 'name']
        unique_together = [['project', 'name']]
        verbose_name = 'Availability Block'
        verbose_name_plural = 'Availability Blocks'

    def __str__(self):
        return f"{self.project.name} — {self.name}"

    @property
    def total_units(self):
        return self.units.filter(is_deleted=False).count()

    @property
    def available_units(self):
        return self.units.filter(status='AVAILABLE', is_deleted=False).count()

    @property
    def booked_units(self):
        return self.units.filter(status='BOOKED', is_deleted=False).count()

    @property
    def blocked_units(self):
        return self.units.filter(status='BLOCKED', is_deleted=False).count()

    @property
    def registered_units(self):
        return self.units.filter(status='REGISTERED', is_deleted=False).count()


# ──────────────────────────────────────────────────────────────────────────────
# AVAILABILITY UNIT  (individual flat / plot)
# ──────────────────────────────────────────────────────────────────────────────

class AvailabilityUnit(BaseModel):
    """
    An individual sellable unit — flat, plot, villa, etc.
    Linked to a Block (which belongs to a Project).
    """
    block = models.ForeignKey(
        AvailabilityBlock, on_delete=models.CASCADE, related_name='units'
    )
    unit_number = models.CharField(max_length=50, db_index=True, help_text="e.g. A-101, Plot-23")
    unit_type = models.CharField(max_length=20, choices=UNIT_TYPE_CHOICES, blank=True, null=True)
    floor = models.PositiveIntegerField(null=True, blank=True, help_text="Floor number (for flats)")
    area_sqft = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    area_sqyd = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Applicable for plots")
    carpet_area_sqft = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    facing = models.CharField(max_length=5, choices=FACING_CHOICES, blank=True, null=True)
    price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=15, choices=UNIT_STATUS_CHOICES, default='AVAILABLE', db_index=True)
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['block', 'floor', 'unit_number']
        unique_together = [['block', 'unit_number']]
        verbose_name = 'Availability Unit'
        verbose_name_plural = 'Availability Units'

    def __str__(self):
        return f"{self.block} — Unit {self.unit_number} [{self.status}]"
