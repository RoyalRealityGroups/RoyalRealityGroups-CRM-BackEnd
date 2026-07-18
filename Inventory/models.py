"""
Module 7 - Inventory Management
Handles Plot and Flat inventory for real estate projects.
Real-world approach:
  - A Project has plots (land) OR units/flats (apartment towers)
  - Both share availability lifecycle: Available → Blocked → Booked → Registered
"""
from django.db import models
from Core.Users.models import CoreModel


INVENTORY_STATUS_CHOICES = [
    ('AVAILABLE', 'Available'),
    ('BLOCKED', 'Blocked'),
    ('BOOKED', 'Booked'),
    ('REGISTERED', 'Registered'),
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


# ============================================================================
# PLOT INVENTORY (for Plot/Villa projects)
# ============================================================================

class PlotInventory(CoreModel):
    """
    Individual plot in a layout project.
    Each plot belongs to one Project (project_type=PLOT or VILLA).
    """
    CODE_PREFIX = 'PLT'

    project = models.ForeignKey(
        'Masters.Project',
        on_delete=models.CASCADE,
        related_name='plots',
    )
    plot_number = models.CharField(max_length=50, db_index=True)
    area_sqyd = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Area in square yards'
    )
    area_sqft = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Area in square feet'
    )
    facing = models.CharField(
        max_length=5, choices=FACING_CHOICES, blank=True, null=True
    )
    road_width = models.CharField(
        max_length=30, blank=True, null=True,
        help_text='e.g. "30 feet", "40 feet"'
    )
    price_per_sqyd = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    total_price = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    status = models.CharField(
        max_length=15, choices=INVENTORY_STATUS_CHOICES,
        default='AVAILABLE', db_index=True
    )
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['project', 'plot_number']
        unique_together = [['project', 'plot_number']]
        verbose_name = 'Plot'
        verbose_name_plural = 'Plots'
        permissions = [
            ("export_plotinventory", "Can export plots"),
        ]

    def __str__(self):
        return f"{self.project.name} - Plot {self.plot_number} [{self.status}]"


# ============================================================================
# FLAT / UNIT INVENTORY (for Apartment/Flat projects)
# ============================================================================

class FlatInventory(CoreModel):
    """
    Individual flat/unit in an apartment project.
    Each flat belongs to one Project (project_type=FLAT or MIXED).
    """
    CODE_PREFIX = 'FLT'

    project = models.ForeignKey(
        'Masters.Project',
        on_delete=models.CASCADE,
        related_name='flats',
    )
    tower = models.CharField(
        max_length=50, blank=True, null=True,
        help_text='Tower / Block name, e.g. "Tower A"'
    )
    floor = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Floor number (0 = Ground)'
    )
    unit_number = models.CharField(
        max_length=50, db_index=True,
        help_text='Unit/Flat number, e.g. "101", "A-203"'
    )
    flat_type = models.CharField(
        max_length=20, blank=True, null=True,
        help_text='e.g. 2BHK, 3BHK, Studio'
    )
    area_sqft = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Built-up area in sq ft'
    )
    carpet_area_sqft = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    facing = models.CharField(
        max_length=5, choices=FACING_CHOICES, blank=True, null=True
    )
    price = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True,
        help_text='Total sale price'
    )
    status = models.CharField(
        max_length=15, choices=INVENTORY_STATUS_CHOICES,
        default='AVAILABLE', db_index=True
    )
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['project', 'tower', 'floor', 'unit_number']
        unique_together = [['project', 'tower', 'unit_number']]
        verbose_name = 'Flat / Unit'
        verbose_name_plural = 'Flats / Units'
        permissions = [
            ("export_flatinventory", "Can export flats"),
        ]

    def __str__(self):
        tower_str = f" {self.tower}" if self.tower else ""
        return f"{self.project.name}{tower_str} - Unit {self.unit_number} [{self.status}]"
