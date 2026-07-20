"""
Module 5 - Site Visit Management

Schedule Site Visit stores:
  - Customer Name
  - Project Name
  - Visit Date
  - Assigned Employee

Status lifecycle: Scheduled → Confirmed → Completed / Cancelled

Completion Details (when status = COMPLETED):
  - Customer Feedback
  - Remarks
  - Photos
"""
from django.db import models
from Core.Users.models import CoreModel
from Users.models import User


SITE_VISIT_STATUS_CHOICES = [
    ('SCHEDULED', 'Scheduled'),
    ('CONFIRMED', 'Confirmed'),
    ('COMPLETED', 'Completed'),
    ('CANCELLED', 'Cancelled'),
]

# Valid status transitions
SITE_VISIT_STATUS_TRANSITIONS = {
    'SCHEDULED': {'CONFIRMED', 'CANCELLED'},
    'CONFIRMED': {'SCHEDULED', 'COMPLETED', 'CANCELLED'},
    'COMPLETED': set(),   # Terminal
    'CANCELLED': set(),   # Terminal
}


class SiteVisit(CoreModel):
    """
    Site Visit - Module 5: Site Visit Management
    Linked to a Lead. A lead can have multiple site visits.
    """
    CODE_PREFIX = 'SV'

    # --- Link to Lead (optional) ---
    lead = models.ForeignKey(
        'Lead.Lead',
        on_delete=models.CASCADE,
        related_name='site_visits',
        null=True,
        blank=True,
        help_text='Linked lead (optional)'
    )

    # --- Schedule fields (required) ---
    customer_name = models.CharField(max_length=200, db_index=True)
    project = models.ForeignKey(
        'Masters.Project',
        on_delete=models.RESTRICT,
        related_name='site_visits',
        null=True,
        blank=True,
    )
    project_name = models.CharField(
        max_length=200, blank=True, null=True,
        help_text='Denormalized project name for display'
    )
    visit_date = models.DateField(db_index=True)
    assigned_employee = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name='assigned_site_visits',
        null=True,
        blank=True,
    )

    # --- Status ---
    status = models.CharField(
        max_length=20,
        choices=SITE_VISIT_STATUS_CHOICES,
        default='SCHEDULED',
        db_index=True,
    )

    # --- Completion details (filled when COMPLETED) ---
    customer_feedback = models.TextField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-visit_date', '-created_on']
        permissions = [
            ("export_sitevisit", "Can export site visits"),
        ]

    def __str__(self):
        return f"{self.customer_name} - {self.project_name or self.project} - {self.visit_date}"


class SiteVisitPhoto(models.Model):
    """Photos attached to a site visit (typically on completion)"""
    site_visit = models.ForeignKey(SiteVisit, on_delete=models.CASCADE, related_name='photos')
    photo = models.ImageField(upload_to='site_visits/photos/')
    caption = models.CharField(max_length=200, blank=True, null=True)
    uploaded_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_on']

    def __str__(self):
        return f"Photo for {self.site_visit}"
