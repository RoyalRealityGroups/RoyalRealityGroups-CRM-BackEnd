from django.contrib import admin
from .models import GeneralSettings


@admin.register(GeneralSettings)
class GeneralSettingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'company_name', 'fcm_enabled', 'enable_push_notifications')
    
    fieldsets = (
        ('Sales Controls', {
            'fields': ('company_scoped_item_enforcement', 'allow_multiple_schemes'),
        }),
        ('Notifications', {
            'fields': (
                'enable_email_notifications',
                'enable_push_notifications',
                'notify_manager_on_booking',
                'notify_employee_on_lead_assignment',
            ),
        }),
        ('System', {
            'fields': (
                'company_name', 'company_logo', 'date_format',
                'currency_symbol', 'pagination_size', 'session_timeout',
            ),
        }),
        ('Security', {
            'fields': (
                'force_password_reset_on_first_login',
                'password_expiry_days',
                'max_login_attempts',
            ),
        }),
        ('Firebase FCM Configuration', {
            'fields': (
                'fcm_enabled',
                'fcm_service_account_json',
                'fcm_project_id',
                'fcm_sender_id',
                'fcm_web_app_id',
                'fcm_android_app_id',
                'fcm_ios_app_id',
                'fcm_api_key',
                'fcm_auth_domain',
                'fcm_storage_bucket',
                'fcm_vapid_key',
            ),
            'description': 'Configure Firebase Cloud Messaging for push notifications (web & mobile)',
        }),
    )

    def has_add_permission(self, request):
        # Only allow one instance (singleton)
        if GeneralSettings.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False
