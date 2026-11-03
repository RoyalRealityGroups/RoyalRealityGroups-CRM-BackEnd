"""
Module 8 - Booking Management
Covers the full booking lifecycle after a lead visits a site.
"""
from django.db import models
from Core.Users.models import CoreModel
from Users.models import User


BOOKING_STATUS_CHOICES = [
    ('BOOKED', 'Booked'),
    ('AGREEMENT', 'Agreement'),
    ('REGISTERED', 'Registered'),
    ('CANCELLED', 'Cancelled'),
]

UNIT_TYPE_CHOICES = [
    ('PLOT', 'Plot'),
    ('FLAT', 'Flat / Unit'),
]


class Booking(CoreModel):
    """
    Booking record - Module 8: Booking Management.
    Links a customer (Lead) to a specific project unit (plot or flat).
    """
    CODE_PREFIX = 'BKG'

    # Customer
    lead = models.ForeignKey(
        'Lead.Lead',
        on_delete=models.RESTRICT,
        related_name='bookings',
        null=True,
        blank=True,
        help_text='Linked lead (customer)'
    )
    customer_name = models.CharField(max_length=200, db_index=True)
    customer_mobile = models.CharField(max_length=15, blank=True, null=True)
    customer_email = models.EmailField(blank=True, null=True)

    # Project & Unit
    # Legacy FK to ProjectManagement — now nullable because bookings can
    # instead reference an Availability project. Kept for backward compatibility.
    project = models.ForeignKey(
        'ProjectManagement.Project',
        on_delete=models.RESTRICT,
        related_name='bookings',
        null=True,
        blank=True,
    )
    unit_type = models.CharField(
        max_length=10, choices=UNIT_TYPE_CHOICES, default='PLOT'
    )
    # Generic unit reference — either a plot or a flat
    plot = models.ForeignKey(
        'Inventory.PlotInventory',
        on_delete=models.RESTRICT,
        related_name='bookings',
        null=True,
        blank=True,
    )
    flat = models.ForeignKey(
        'Inventory.FlatInventory',
        on_delete=models.RESTRICT,
        related_name='bookings',
        null=True,
        blank=True,
    )
    unit_number = models.CharField(
        max_length=50, blank=True, null=True,
        help_text='Denormalised unit number for quick display'
    )

    # Availability List integration (new source of projects/units).
    # These are nullable so existing bookings (linked to old Inventory) keep working.
    availability_project = models.ForeignKey(
        'Availability.AvailabilityProject',
        on_delete=models.RESTRICT,
        related_name='bookings',
        null=True,
        blank=True,
        help_text='Project selected from the Availability List',
    )
    availability_unit = models.ForeignKey(
        'Availability.AvailabilityUnit',
        on_delete=models.RESTRICT,
        related_name='bookings',
        null=True,
        blank=True,
        help_text='Unit (flat/plot) selected from the Availability List',
    )

    # Financials
    agreed_price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    booking_amount = models.DecimalField(max_digits=14, decimal_places=2)
    booking_date = models.DateField(db_index=True)
    property_cost = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, help_text='Total property cost')
    revenue = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, help_text='Revenue from this booking')
    incentive = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, help_text='Incentive/commission for sales executive')

    # Team
    sales_executive = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name='bookings_as_executive',
        null=True,
        blank=True,
    )

    # Status
    status = models.CharField(
        max_length=15, choices=BOOKING_STATUS_CHOICES,
        default='BOOKED', db_index=True
    )

    # Cancellation
    cancellation_reason = models.TextField(blank=True, null=True)
    cancelled_date = models.DateField(null=True, blank=True)

    remarks = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-booking_date', '-created_on']
        permissions = [
            ("export_booking", "Can export bookings"),
        ]

    def __str__(self):
        proj = self.project.name if self.project else (
            self.availability_project.name if self.availability_project else '—'
        )
        return f"{self.code} - {self.customer_name} | {proj} [{self.status}]"

    def save(self, *args, **kwargs):
        # Denormalise unit number from whichever source is set
        if not self.unit_number:
            if self.availability_unit:
                self.unit_number = self.availability_unit.unit_number
            elif self.plot:
                self.unit_number = self.plot.plot_number
            elif self.flat:
                self.unit_number = self.flat.unit_number
        super().save(*args, **kwargs)


class BookingStatusHistory(models.Model):
    """Audit trail for booking status changes"""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='status_history')
    from_status = models.CharField(max_length=15, choices=BOOKING_STATUS_CHOICES, blank=True, null=True)
    to_status = models.CharField(max_length=15, choices=BOOKING_STATUS_CHOICES)
    changed_by = models.ForeignKey(User, on_delete=models.RESTRICT)
    remarks = models.TextField(blank=True, null=True)
    changed_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_on']

    def __str__(self):
        return f"{self.booking.code}: {self.from_status} → {self.to_status}"
