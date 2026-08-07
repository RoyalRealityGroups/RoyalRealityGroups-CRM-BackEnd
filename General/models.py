from django.db import models

# Create your models here.


class ImportPermission(models.Model):
    """
    Model to hold custom permissions for Import module.
    This model won't store data, just provides ContentType for permissions.
    """
    
    class Meta:
        verbose_name = "Import Permission"
        verbose_name_plural = "Import Permissions"
        default_permissions = ()  # Don't create default add/change/delete/view permissions
        permissions = [
            ('view_import_data', 'Can view import data'),
            ('view_import_history', 'Can view import history'),
            ('view_general_settings', 'Can view general settings'),
            ('modify_general_settings', 'Can modify general settings'),
        ]


class GeneralSettings(models.Model):
    """
    Global application settings controlled from General Settings screen.
    Singleton model (single row) accessed via get_solo().
    """

    # --- Sales Controls ---
    company_scoped_item_enforcement = models.BooleanField(
        default=False,
        help_text='When enabled, item must belong to selected company in sales flows',
    )
    allow_multiple_schemes = models.BooleanField(
        default=True,
        help_text='When disabled, only one scheme can be selected per sales order',
    )

    # --- Notifications ---
    enable_email_notifications = models.BooleanField(
        default=True,
        help_text='Enable sending email notifications system-wide',
    )
    enable_push_notifications = models.BooleanField(
        default=True,
        help_text='Enable push notifications via Firebase',
    )
    notify_manager_on_booking = models.BooleanField(
        default=True,
        help_text='Send notification to reporting manager when a new booking is created',
    )
    notify_employee_on_lead_assignment = models.BooleanField(
        default=True,
        help_text='Send notification to employee when a lead is assigned to them',
    )

    # --- System ---
    company_name = models.CharField(
        max_length=200, default='Royal Reality Groups',
        help_text='Company name displayed in the application',
    )
    company_logo = models.ImageField(
        upload_to='settings/', null=True, blank=True,
        help_text='Company logo (recommended 200x60px)',
    )
    date_format = models.CharField(
        max_length=20, default='DD-MM-YYYY',
        help_text='Date display format (DD-MM-YYYY, MM-DD-YYYY, YYYY-MM-DD)',
    )
    currency_symbol = models.CharField(
        max_length=10, default='₹',
        help_text='Currency symbol used in reports and display',
    )
    pagination_size = models.PositiveIntegerField(
        default=20,
        help_text='Default number of records per page',
    )
    session_timeout = models.PositiveIntegerField(
        default=60,
        help_text='Session timeout in minutes (0 = no timeout)',
    )

    # --- Security ---
    force_password_reset_on_first_login = models.BooleanField(
        default=True,
        help_text='Require users to change password on their first login',
    )
    password_expiry_days = models.PositiveIntegerField(
        default=0,
        help_text='Force password change after N days (0 = never expires)',
    )
    max_login_attempts = models.PositiveIntegerField(
        default=5,
        help_text='Lock account after N failed login attempts (0 = unlimited)',
    )

    # --- Firebase FCM Configuration ---
    fcm_enabled = models.BooleanField(
        default=False,
        help_text='Enable Firebase Cloud Messaging push notifications',
    )
    fcm_service_account_json = models.TextField(
        blank=True, default='',
        help_text='Firebase service account JSON (from Firebase Console → Project Settings → Service Accounts)',
    )
    fcm_project_id = models.CharField(
        max_length=200, blank=True, default='',
        help_text='Firebase Project ID (e.g., "my-project-12345")',
    )
    fcm_sender_id = models.CharField(
        max_length=100, blank=True, default='',
        help_text='Firebase Cloud Messaging Sender ID',
    )
    fcm_web_app_id = models.CharField(
        max_length=200, blank=True, default='',
        help_text='Firebase Web App ID (from Firebase Console → Project Settings → Your apps)',
    )
    fcm_android_app_id = models.CharField(
        max_length=200, blank=True, default='',
        help_text='Firebase Android App ID (from google-services.json → mobilesdk_app_id)',
    )
    fcm_ios_app_id = models.CharField(
        max_length=200, blank=True, default='',
        help_text='Firebase iOS App ID (from GoogleService-Info.plist → GOOGLE_APP_ID)',
    )
    fcm_api_key = models.CharField(
        max_length=200, blank=True, default='',
        help_text='Firebase Web API Key',
    )
    fcm_auth_domain = models.CharField(
        max_length=200, blank=True, default='',
        help_text='Firebase Auth Domain (e.g., "project-id.firebaseapp.com")',
    )
    fcm_storage_bucket = models.CharField(
        max_length=200, blank=True, default='',
        help_text='Firebase Storage Bucket URL (optional)',
    )
    fcm_vapid_key = models.CharField(
        max_length=500, blank=True, default='',
        help_text='VAPID Key for Web Push (Firebase Console → Cloud Messaging → Web Push certificates)',
    )

    class Meta:
        verbose_name = "General Settings"
        verbose_name_plural = "General Settings"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @classmethod
    def is_company_scoped_item_enforcement_enabled(cls) -> bool:
        return bool(cls.get_solo().company_scoped_item_enforcement)

    @classmethod
    def is_allow_multiple_schemes_enabled(cls) -> bool:
        return bool(cls.get_solo().allow_multiple_schemes)
