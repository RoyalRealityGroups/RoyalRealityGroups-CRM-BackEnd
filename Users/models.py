from django.db import models
from Core.Users.models import CoreUser


class UserStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    INACTIVE = 'INACTIVE', 'Inactive'
    SUSPENDED = 'SUSPENDED', 'Suspended'


class DataScope(models.TextChoices):
    OWN = 'OWN', 'Own'
    TEAM = 'TEAM', 'Team'
    ALL = 'ALL', 'All'


class User(CoreUser):
    """Extended User model for RRGMS."""

    designation = models.CharField(
        max_length=100, blank=True, null=True,
        help_text="Display-only designation (Director, Team Leader, etc.)"
    )

    reporting_manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='team_members',
        help_text='Self-referencing FK to build reporting hierarchy'
    )

    user_status = models.CharField(
        max_length=20,
        choices=UserStatus.choices,
        default=UserStatus.ACTIVE,
    )

    # Data scope — controls record-level visibility per module
    lead_data_scope = models.CharField(max_length=10, choices=DataScope.choices, default=DataScope.OWN)
    followup_data_scope = models.CharField(max_length=10, choices=DataScope.choices, default=DataScope.OWN)
    sitevisit_data_scope = models.CharField(max_length=10, choices=DataScope.choices, default=DataScope.OWN)
    booking_data_scope = models.CharField(max_length=10, choices=DataScope.choices, default=DataScope.OWN)

    must_reset_password = models.BooleanField(default=True)

    # Employee stats (denormalized counters)
    joining_date = models.DateField(null=True, blank=True)
    leads_assigned = models.PositiveIntegerField(default=0)
    site_visits = models.PositiveIntegerField(default=0)
    bookings = models.PositiveIntegerField(default=0)
    registrations = models.PositiveIntegerField(default=0)

    class Meta:
        proxy = False

    def __str__(self):
        return self.username

    def get_team_users(self, _visited=None):
        """Recursively get all users reporting to this user. Cycle-safe."""
        if _visited is None:
            _visited = set()
        if self.id in _visited:
            return set()
        _visited.add(self.id)
        team = set()
        for member in self.team_members.all():
            team.add(member)
            team.update(member.get_team_users(_visited=_visited))
        return team

    def can_access_all_data(self, screen):
        scope_map = {
            'lead': self.lead_data_scope,
            'followup': self.followup_data_scope,
            'sitevisit': self.sitevisit_data_scope,
            'booking': self.booking_data_scope,
        }
        return scope_map.get(screen, DataScope.OWN) == DataScope.ALL

    def can_access_team_data(self, screen):
        scope = {
            'lead': self.lead_data_scope,
            'followup': self.followup_data_scope,
            'sitevisit': self.sitevisit_data_scope,
            'booking': self.booking_data_scope,
        }.get(screen, DataScope.OWN)
        return scope in (DataScope.TEAM, DataScope.ALL)


# =============================================================================
# Screen & Permission Models
# =============================================================================

class Screen(models.Model):
    """A screen/module in RRGMS that can be permission-gated."""

    SCREEN_CHOICES = [
        ('LEAD', 'Lead Management'),
        ('CROSS_LEAD', 'Cross Lead Check'),
        ('FOLLOWUP', 'Follow-Up Management'),
        ('SITE_VISIT', 'Site Visit Management'),
        ('PROJECT', 'Project Management'),
        ('INVENTORY', 'Availability List'),
        ('BOOKING', 'Booking Management'),
        ('DOCUMENT', 'Document Management'),
        ('EMPLOYEE', 'Employee Management'),
        ('REPORTS', 'Reports'),
        ('DASHBOARD', 'Dashboards'),
        ('USER_PERMISSION', 'User & Permission Management'),
    ]

    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} ({self.code})"

    @classmethod
    def get_default_screens(cls):
        return [s[0] for s in cls.SCREEN_CHOICES]


class UserPermission(models.Model):
    """Per-user, per-screen permission matrix. Single source of truth."""

    user = models.ForeignKey(
        'Users.User',
        on_delete=models.CASCADE,
        related_name='screen_permissions',
    )
    screen = models.ForeignKey(
        Screen,
        on_delete=models.CASCADE,
        related_name='user_permissions',
    )

    can_view = models.BooleanField(default=False)
    can_add = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_export = models.BooleanField(default=False)
    is_view_only = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'screen']

    def __str__(self):
        return f"{self.user.username} — {self.screen.name}"

    def has_permission(self, action):
        if self.is_view_only and action != 'view':
            return False
        action_map = {
            'view':   self.can_view,
            'add':    self.can_add,
            'edit':   self.can_edit,
            'delete': self.can_delete,
            'export': self.can_export,
        }
        return action_map.get(action, False)


class PermissionTemplate(models.Model):
    """Reusable permission template — apply a pre-set to a new user."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class PermissionTemplateDetail(models.Model):
    template = models.ForeignKey(PermissionTemplate, on_delete=models.CASCADE, related_name='details')
    screen = models.ForeignKey(Screen, on_delete=models.CASCADE)
    can_view = models.BooleanField(default=False)
    can_add = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_export = models.BooleanField(default=False)

    class Meta:
        unique_together = ['template', 'screen']


class PermissionAuditLog(models.Model):
    """Audit trail for every permission change."""
    changed_by = models.ForeignKey(
        'Users.User', on_delete=models.SET_NULL, null=True,
        related_name='permission_changes_made',
    )
    target_user = models.ForeignKey(
        'Users.User', on_delete=models.CASCADE,
        related_name='permission_changes_received',
    )
    action = models.CharField(max_length=50)
    field_changed = models.CharField(max_length=100, blank=True)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
