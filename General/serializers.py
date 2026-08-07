from rest_framework import serializers

from .models import GeneralSettings


class GeneralSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneralSettings
        fields = (
            "id",
            # Sales Controls
            "company_scoped_item_enforcement",
            "allow_multiple_schemes",
            # Notifications
            "enable_email_notifications",
            "enable_push_notifications",
            "notify_manager_on_booking",
            "notify_employee_on_lead_assignment",
            # System
            "company_name",
            "company_logo",
            "date_format",
            "currency_symbol",
            "pagination_size",
            "session_timeout",
            # Security
            "force_password_reset_on_first_login",
            "password_expiry_days",
            "max_login_attempts",
            # Firebase FCM
            "fcm_enabled",
            "fcm_service_account_json",
            "fcm_project_id",
            "fcm_sender_id",
            "fcm_web_app_id",
            "fcm_android_app_id",
            "fcm_ios_app_id",
            "fcm_api_key",
            "fcm_auth_domain",
            "fcm_storage_bucket",
            "fcm_vapid_key",
        )
        read_only_fields = ("id",)
