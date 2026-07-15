from django.db import models
from Core.Users.models import CoreModel
from Users.models import User


# Lead Source choices
LEAD_SOURCE_CHOICES = [
    ('WEBSITE', 'Website'),
    ('FACEBOOK', 'Facebook'),
    ('INSTAGRAM', 'Instagram'),
    ('GOOGLE_ADS', 'Google Ads'),
    ('WHATSAPP', 'WhatsApp'),
    ('MAGICBRICKS', 'MagicBricks'),
    ('99ACRES', '99acres'),
    ('REFERRALS', 'Referrals'),
    ('MANUAL', 'Manual Entry'),
]

# Lead Status choices - sequential pipeline
LEAD_STATUS_CHOICES = [
    ('NEW_LEAD', 'New Lead'),
    ('CONTACT_ATTEMPTED', 'Contact Attempted'),
    ('CONNECTED', 'Connected'),
    ('INTERESTED', 'Interested'),
    ('SITE_VISIT_SCHEDULED', 'Site Visit Scheduled'),
    ('SITE_VISIT_COMPLETED', 'Site Visit Completed'),
    ('NEGOTIATION', 'Negotiation'),
    ('BOOKING', 'Booking'),
    ('REGISTRATION', 'Registration'),
    ('LOST', 'Lost'),
]


class Lead(CoreModel):
    """
    Lead model for Module B - Lead Management
    """
    
    CODE_PREFIX = 'LEAD'
    
    # Customer Information
    name = models.CharField(max_length=200, db_index=True)
    mobile = models.CharField(max_length=15, db_index=True)
    alternate_number = models.CharField(max_length=15, blank=True, null=True, db_index=True)
    email = models.EmailField(blank=True, null=True, db_index=True)
    
    # Requirement Details
    budget = models.CharField(max_length=100, blank=True, null=True)
    preferred_area = models.CharField(max_length=200, blank=True, null=True)
    property_requirement = models.CharField(max_length=200, blank=True, null=True)
    
    # Lead Source
    lead_source = models.CharField(max_length=20, choices=LEAD_SOURCE_CHOICES, db_index=True)
    
    # Assignment
    assigned_employee = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name='assigned_leads',
        null=True,
        blank=True
    )
    
    # Status
    status = models.CharField(max_length=30, choices=LEAD_STATUS_CHOICES, default='NEW_LEAD', db_index=True)
    
    # Additional Information
    remarks = models.TextField(blank=True, null=True)
    
    # Cross Lead Check override
    cross_lead_override = models.BooleanField(default=False)
    cross_lead_override_reason = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_on']
        indexes = [
            models.Index(fields=['mobile', 'alternate_number', 'email']),
        ]
        permissions = [
            ("export_lead", "Can export leads"),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.status}"


class LeadStatusHistory(CoreModel):
    """
    Track lead status changes with timestamp and user
    """
    CODE_PREFIX = 'LSH'
    
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='status_history')
    from_status = models.CharField(max_length=30, choices=LEAD_STATUS_CHOICES, blank=True, null=True)
    to_status = models.CharField(max_length=30, choices=LEAD_STATUS_CHOICES)
    changed_by = models.ForeignKey(User, on_delete=models.RESTRICT, related_name='lead_status_changes')
    remarks = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_on']
    
    def __str__(self):
        return f"{self.lead.name}: {self.from_status} → {self.to_status}"


class LeadFollowUp(CoreModel):
    """
    Follow-ups for Module D - Follow-Up Management
    """
    
    CODE_PREFIX = 'FUP'
    
    FOLLOW_UP_TYPE_CHOICES = [
        ('CALL', 'Call'),
        ('WHATSAPP', 'WhatsApp'),
        ('MEETING', 'Meeting'),
        ('SITE_VISIT', 'Site Visit'),
    ]
    
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='follow_ups')
    follow_up_date = models.DateField(db_index=True)
    follow_up_type = models.CharField(max_length=20, choices=FOLLOW_UP_TYPE_CHOICES)
    discussion_notes = models.TextField(blank=True, null=True)
    follow_up_time = models.TimeField(blank=True, null=True)
    next_follow_up_date = models.DateField(blank=True, null=True, db_index=True)
    created_by = models.ForeignKey(User, on_delete=models.RESTRICT, related_name='lead_follow_ups')
    
    class Meta:
        ordering = ['-follow_up_date']
    
    def __str__(self):
        return f"{self.lead.name} - {self.follow_up_date}"


class LeadCrossCheck(models.Model):
    """
    Cross Lead Check - stores duplicate check results
    """
    original_lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='cross_checks')
    duplicate_of = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='duplicates_found')
    match_field = models.CharField(max_length=50)  # mobile, alternate_number, email
    override_reason = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.RESTRICT)
    created_on = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.original_lead.name} → {self.duplicate_of.name} ({self.match_field})"
