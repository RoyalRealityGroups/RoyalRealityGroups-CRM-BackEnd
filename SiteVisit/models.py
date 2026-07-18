from django.db import models
from django.conf import settings


class SiteVisit(models.Model):
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('CONFIRMED', 'Confirmed'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    customer_name = models.CharField(max_length=200)
    project_name = models.CharField(max_length=200)
    visit_date = models.DateField()
    assigned_employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='assigned_site_visits',
    )
    # ponytail: nullable FK keeps existing rows valid during migration; add lead
    # sync + LeadStatusHistory write in the same iteration when wiring the UI.
    lead = models.ForeignKey(
        'Lead.Lead',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='site_visits',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')

    customer_feedback = models.TextField(blank=True, default='')
    remarks = models.TextField(blank=True, default='')
    photos = models.JSONField(default=list, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='site_visits_created',
    )
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-visit_date', '-created_on']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['visit_date']),
        ]

    def __str__(self):
        return f"{self.customer_name} - {self.project_name} ({self.visit_date})"