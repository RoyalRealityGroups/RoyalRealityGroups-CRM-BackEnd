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

# Lead Bucket choices
LEAD_BUCKET_CHOICES = [
    ('NEW_LEAD', 'New Lead'),
    ('HOT_LEAD', 'Hot Lead'),
    ('PROSPECTS', 'Prospects'),
]

# Lead Status choices
LEAD_STATUS_CHOICES = [
    ('ONGOING', 'Ongoing'),
    ('LIVE', 'Live'),
    ('DEAD', 'Dead'),
]

class Lead(CoreModel):
    """Lead model - Module 2: Lead Management"""

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

    # Project interest
    interested_project = models.ForeignKey(
        'ProjectManagement.Project',
        on_delete=models.SET_NULL,
        related_name='interested_leads',
        null=True,
        blank=True
    )

    # Status
    status = models.CharField(max_length=30, choices=LEAD_STATUS_CHOICES, default='ONGOING', db_index=True)

    # Bucket
    bucket = models.CharField(max_length=20, choices=LEAD_BUCKET_CHOICES, blank=True, null=True, db_index=True)

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
    """Track lead status changes"""
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
    """Follow-ups - Module 4: Follow-Up Management"""

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
    """Cross Lead Check - Module 3"""
    original_lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='cross_checks')
    duplicate_of = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='duplicates_found')
    match_field = models.CharField(max_length=50)
    override_reason = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.RESTRICT)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.original_lead.name} → {self.duplicate_of.name} ({self.match_field})"



class CallLog(models.Model):
    """
    Call Log — synced from Android mobile app.
    Auto-matches to a Lead by phone number on create.
    """
    CALL_TYPE_CHOICES = [
        ('outgoing', 'Outgoing'),
        ('incoming', 'Incoming'),
        ('missed',   'Missed'),
        ('rejected', 'Rejected'),
        ('unknown',  'Unknown'),
    ]

    phone_number    = models.CharField(max_length=20, db_index=True)
    call_type       = models.CharField(max_length=10, choices=CALL_TYPE_CHOICES)
    duration_secs   = models.PositiveIntegerField(default=0)
    called_at       = models.DateTimeField(db_index=True)
    device_platform = models.CharField(max_length=10, default='android')
    called_by       = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='call_logs'
    )
    lead            = models.ForeignKey(
        Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name='call_logs'
    )
    created_at      = models.DateTimeField(auto_now_add=True)
    call_count      = models.PositiveIntegerField(default=1, help_text='How many times this call was synced (same phone+time)')
    call_times      = models.JSONField(default=list, blank=True, help_text='List of all called_at timestamps for this number')

    class Meta:
        ordering = ['-called_at']
        indexes = [
            models.Index(fields=['phone_number', 'called_by']),
            models.Index(fields=['called_at']),
        ]

    def __str__(self):
        return f"{self.call_type} — {self.phone_number} by {self.called_by} at {self.called_at}"


class PhoneComment(models.Model):
    """
    User comment on a phone number (contact-level note).
    One comment per phone_number per user — upserted on POST.
    """
    phone_number = models.CharField(max_length=20, db_index=True)
    commented_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='phone_comments'
    )
    call_log = models.ForeignKey(
        CallLog, on_delete=models.CASCADE,
        related_name='phone_comments',
        null=True, blank=True,
        help_text='Linked call log — deleted automatically when call log is deleted'
    )
    lead = models.ForeignKey(
        Lead, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='phone_comments',
        help_text='Auto-matched lead by phone number'
    )
    comment = models.TextField()
    comment_history = models.JSONField(default=list, blank=True, help_text='List of all previous comments with timestamps')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        unique_together = [['phone_number', 'commented_by']]
        indexes = [
            models.Index(fields=['phone_number', 'commented_by']),
        ]

    def __str__(self):
        return f"{self.phone_number} — {self.commented_by} — {self.comment[:40]}"

