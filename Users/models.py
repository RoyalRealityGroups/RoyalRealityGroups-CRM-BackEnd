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
    """Extended User model for RRGMS with permission fields"""
    
    # RRGMS Custom Fields
    designation = models.CharField(max_length=100, blank=True, null=True, help_text="Display-only designation (Director, Team Leader, etc.)")
    
    reporting_manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='team_members',
        help_text='Self-referencing FK to build reporting hierarchy'
    )
    
    user_status = models.CharField(
        max_length=20,
        choices=UserStatus.choices,
        default=UserStatus.ACTIVE,
        help_text='User account status'
    )
    
    # Data scope for record-heavy screens
    lead_data_scope = models.CharField(
        max_length=10,
        choices=DataScope.choices,
        default=DataScope.OWN,
        help_text='Data visibility for Leads'
    )
    followup_data_scope = models.CharField(
        max_length=10,
        choices=DataScope.choices,
        default=DataScope.OWN,
        help_text='Data visibility for Follow-ups'
    )
    sitevisit_data_scope = models.CharField(
        max_length=10,
        choices=DataScope.choices,
        default=DataScope.OWN,
        help_text='Data visibility for Site Visits'
    )
    booking_data_scope = models.CharField(
        max_length=10,
        choices=DataScope.choices,
        default=DataScope.OWN,
        help_text='Data visibility for Bookings'
    )
    
    # Password reset tracking
    must_reset_password = models.BooleanField(
        default=True,
        help_text='Force password reset on first login'
    )
    
    class Meta:
        proxy = False

    def __str__(self):
        return self.username
    
    def get_team_users(self):
        """Get all users who report to this user (recursive)"""
        team = set()
        for member in self.team_members.all():
            team.add(member)
            team.update(member.get_team_users())
        return team
    
    def can_access_all_data(self, screen):
        """Check if user has 'All' data scope for a screen"""
        scope_map = {
            'lead': self.lead_data_scope,
            'followup': self.followup_data_scope,
            'sitevisit': self.sitevisit_data_scope,
            'booking': self.booking_data_scope,
        }
        return scope_map.get(screen, DataScope.ALL) == DataScope.ALL
    
    def can_access_team_data(self, screen):
        """Check if user has 'Team' or 'All' data scope"""
        scope = {
            'lead': self.lead_data_scope,
            'followup': self.followup_data_scope,
            'sitevisit': self.sitevisit_data_scope,
            'booking': self.booking_data_scope,
        }.get(screen, DataScope.ALL)
        return scope in (DataScope.TEAM, DataScope.ALL)


# =============================================================================
# RRGMS Permission Models
# =============================================================================

class Screen(models.Model):
    """Screen definitions for RRGMS - 12 screens as per Module A"""
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class UserPermission(models.Model):
    """Permission matrix: Screen × Actions for each user"""
    user = models.ForeignKey('Users.User', on_delete=models.CASCADE, related_name='permissions')
    screen = models.ForeignKey(Screen, on_delete=models.CASCADE, related_name='user_permissions')
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
    
    def has_permission(self, action):
        if self.is_view_only and action != 'view':
            return False
        return getattr(self, f'can_{action}', False)


class PermissionTemplate(models.Model):
    """Save permission matrix as reusable template"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    screens = models.ManyToManyField(Screen, through='PermissionTemplateDetail')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class PermissionTemplateDetail(models.Model):
    template = models.ForeignKey(PermissionTemplate, on_delete=models.CASCADE)
    screen = models.ForeignKey(Screen, on_delete=models.CASCADE)
    can_view = models.BooleanField(default=False)
    can_add = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_export = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['template', 'screen']


class PermissionAuditLog(models.Model):
    """Audit trail for permission changes"""
    changed_by = models.ForeignKey('Users.User', on_delete=models.SET_NULL, null=True, related_name='permission_changes_made')
    target_user = models.ForeignKey('Users.User', on_delete=models.CASCADE, related_name='permission_changes_received')
    action = models.CharField(max_length=50)
    field_changed = models.CharField(max_length=100, blank=True)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']


# =============================================================================
# RRGMS Permission Models
# =============================================================================

class Screen(models.Model):
    """Screen definitions for RRGMS - 12 screens as per Module A requirements"""
    
    SCREEN_CHOICES = [
        ('LEAD', 'Lead Management'),
        ('CROSS_LEAD', 'Cross Lead Check'),
        ('FOLLOWUP', 'Follow-Up Management'),
        ('SITE_VISIT', 'Site Visit Management'),
        ('PROJECT', 'Project Management'),
        ('INVENTORY', 'Inventory Management'),
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
        """Return list of default screen codes"""
        return [s[0] for s in cls.SCREEN_CHOICES]


class UserPermission(models.Model):
    """Permission matrix: Screen × Actions for each user"""
    
    user = models.ForeignKey(
        'Users.User',
        on_delete=models.CASCADE,
        related_name='permissions'
    )
    screen = models.ForeignKey(
        Screen,
        on_delete=models.CASCADE,
        related_name='user_permissions'
    )
    
    # Action flags
    can_view = models.BooleanField(default=False)
    can_add = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_export = models.BooleanField(default=False)
    
    # Dashboards are view-only
    is_view_only = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'screen']
    
    def __str__(self):
        return f"{self.user.username} - {self.screen.name}"
    
    def has_permission(self, action):
        """Check if user has specific action permission"""
        if self.is_view_only and action != 'view':
            return False
        action_map = {
            'view': self.can_view,
            'add': self.can_add,
            'edit': self.can_edit,
            'delete': self.can_delete,
            'export': self.can_export,
        }
        return action_map.get(action, False)


class PermissionTemplate(models.Model):
    """Save permission matrix as reusable template"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class PermissionTemplateDetail(models.Model):
    """Through model for template-screen relationship"""
    
    template = models.ForeignKey(PermissionTemplate, on_delete=models.CASCADE)
    screen = models.ForeignKey(Screen, on_delete=models.CASCADE)
    
    can_view = models.BooleanField(default=False)
    can_add = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_export = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['template', 'screen']


class PermissionAuditLog(models.Model):
    """Audit trail for permission changes"""
    
    changed_by = models.ForeignKey(
        'Users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='permission_changes_made'
    )
    target_user = models.ForeignKey(
        'Users.User',
        on_delete=models.CASCADE,
        related_name='permission_changes_received'
    )
    action = models.CharField(max_length=50)  # CREATE, UPDATE, DELETE
    field_changed = models.CharField(max_length=100, blank=True)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.changed_by} changed {self.target_user} - {self.action} at {self.timestamp}"

