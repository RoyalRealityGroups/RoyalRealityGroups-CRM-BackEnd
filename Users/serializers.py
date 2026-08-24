import string

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password as django_validate_password
from django.utils.crypto import get_random_string
from rest_framework import serializers, status

from Core.Users.models import DEVICE_ACCESS_CHOICES, GENDER_CHOICES

User = get_user_model()


# =============================================================================
# Helpers
# =============================================================================

def validate_contact_email(value):
    if value:
        import re
        value = value.strip().lower()
        if not re.match(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$', value):
            raise ValueError('Enter a valid email address.')
    return value


def validate_contact_phone(value):
    if value:
        import re
        digits = re.sub(r'[\s\-\+\(\)]', '', value)
        if not digits.isdigit() or not (7 <= len(digits) <= 15):
            raise ValueError('Enter a valid phone number (7–15 digits).')
    return value


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


# =============================================================================
# User Serializers
# =============================================================================

class UserSerializer(serializers.ModelSerializer):
    """
    Full user serializer for create / update / list.

    screen_permissions_input (write-only):
        List of { screen_code, can_view, can_add, can_edit, can_delete, can_export }
        Saved to UserPermission table on create/update.
    """

    fullname = serializers.SerializerMethodField()
    gender_name = serializers.SerializerMethodField()
    device_access_name = serializers.SerializerMethodField()
    reporting_manager_name = serializers.SerializerMethodField()
    team_count = serializers.SerializerMethodField()
    screen_permissions = serializers.SerializerMethodField()

    username = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, max_length=128, required=False)
    remove_profilepicture = serializers.BooleanField(required=False, write_only=True, default=False)
    profilepicture = serializers.ImageField(required=False, allow_null=True)

    gender = serializers.ChoiceField(choices=GENDER_CHOICES, required=False, allow_null=True)
    device_access = serializers.ChoiceField(choices=DEVICE_ACCESS_CHOICES, required=False)

    designation = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    joining_date = serializers.DateField(required=False, allow_null=True)
    reporting_manager = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False, allow_null=True
    )
    user_status = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    must_reset_password = serializers.BooleanField(required=False)

    is_email_verified = serializers.BooleanField(read_only=True)
    is_phone_verified = serializers.BooleanField(read_only=True)

    # Write-only — list of { screen_code, can_view, can_add, can_edit, can_delete, can_export }
    screen_permissions_input = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        default=list,
    )

    class Meta:
        model = User
        read_only_fields = ['otp', 'username', 'is_email_verified', 'is_phone_verified']
        fields = [
            'id', 'username', 'fullname', 'first_name', 'last_name',
            'email', 'phone',
            'gender', 'gender_name',
            'device_access', 'device_access_name',
            'profilepicture', 'remove_profilepicture',
            'password',
            'designation', 'joining_date',
            'reporting_manager', 'reporting_manager_name',
            'team_count',
            'user_status', 'is_active',
            'must_reset_password',
            'receive_sms', 'receive_email', 'receive_notification',
            'is_email_verified', 'is_phone_verified',
            'otp',
            'lead_data_scope', 'followup_data_scope',
            'sitevisit_data_scope', 'booking_data_scope',
            'leads_assigned', 'site_visits', 'bookings', 'registrations',
            'screen_permissions', 'screen_permissions_input',
        ]

    # ------------------------------------------------------------------
    # Computed fields
    # ------------------------------------------------------------------

    def get_fullname(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username

    def get_gender_name(self, obj):
        return obj.get_gender_display() if hasattr(obj, 'get_gender_display') else None

    def get_device_access_name(self, obj):
        return obj.get_device_access_display() if hasattr(obj, 'get_device_access_display') else None

    def get_reporting_manager_name(self, obj):
        if obj.reporting_manager:
            return (
                f"{obj.reporting_manager.first_name} {obj.reporting_manager.last_name}".strip()
                or obj.reporting_manager.username
            )
        return None

    def get_team_count(self, obj):
        return obj.team_members.count()

    def get_screen_permissions(self, obj):
        from Users.models import UserPermission
        perms = UserPermission.objects.filter(user=obj).select_related('screen')
        return [
            {
                'screen_id': p.screen.id,
                'screen_code': p.screen.code,
                'screen_name': p.screen.name,
                'can_view': p.can_view,
                'can_add': p.can_add,
                'can_edit': p.can_edit,
                'can_delete': p.can_delete,
                'can_export': p.can_export,
                'is_view_only': p.is_view_only,
            }
            for p in perms
        ]

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_username(self, value):
        if not value:
            return value
        if not value.isalnum():
            raise serializers.ValidationError('Username must contain only alphanumeric characters.')
        q = User.objects.filter(is_active=True)
        if self.instance:
            q = q.exclude(pk=self.instance.pk)
        if q.filter(username=value).exists():
            raise serializers.ValidationError('This username is already in use.')
        return value

    def validate_email(self, value):
        try:
            value = validate_contact_email(value)
        except Exception as exc:
            raise serializers.ValidationError(str(exc))
        if value:
            q = User.objects.all()
            if self.instance:
                q = q.exclude(pk=self.instance.pk)
            if q.filter(email=value).exists():
                raise serializers.ValidationError('This email is already in use.')
        return value

    def validate_phone(self, value):
        try:
            return validate_contact_phone(value)
        except Exception as exc:
            raise serializers.ValidationError(str(exc))

    def validate_password(self, value):
        if value:
            try:
                django_validate_password(value)
            except Exception as exc:
                raise serializers.ValidationError(list(exc.messages))
        return value

    # ------------------------------------------------------------------
    # Username auto-generation
    # ------------------------------------------------------------------

    def _generate_username(self):
        last = User.objects.filter(username__startswith='EMP').order_by('-username').first()
        if last:
            try:
                num = int(last.username.replace('EMP', '')) + 1
            except ValueError:
                num = User.objects.filter(username__startswith='EMP').count() + 1
        else:
            num = 1
        return f'EMP{num:04d}'

    # ------------------------------------------------------------------
    # Save screen permissions
    # ------------------------------------------------------------------

    def _save_screen_permissions(self, user, permissions_input):
        """Upsert UserPermission rows from screen_permissions_input list."""
        from Users.models import Screen, UserPermission

        for item in permissions_input:
            screen_code = item.get('screen_code')
            if not screen_code:
                continue
            
            # Auto-create screen if it doesn't exist (using code as name if name not provided)
            screen, _ = Screen.objects.get_or_create(
                code=screen_code,
                defaults={'name': item.get('screen_name', screen_code), 'order': 0}
            )

            can_view   = bool(item.get('can_view', False))
            can_add    = bool(item.get('can_add', False))
            can_edit   = bool(item.get('can_edit', False))
            can_delete = bool(item.get('can_delete', False))
            can_export = bool(item.get('can_export', False))
            is_view_only = can_view and not any([can_add, can_edit, can_delete, can_export])

            UserPermission.objects.update_or_create(
                user=user,
                screen=screen,
                defaults={
                    'can_view':    can_view,
                    'can_add':     can_add,
                    'can_edit':    can_edit,
                    'can_delete':  can_delete,
                    'can_export':  can_export,
                    'is_view_only': is_view_only,
                },
            )

    # ------------------------------------------------------------------
    # Create / Update
    # ------------------------------------------------------------------

    def create(self, validated_data):
        permissions_input = validated_data.pop('screen_permissions_input', [])
        validated_data.pop('remove_profilepicture', None)

        if not validated_data.get('username'):
            validated_data['username'] = self._generate_username()

        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        user.set_password(password if password else user.username)
        user.save(update_fields=['password'])

        if permissions_input:
            self._save_screen_permissions(user, permissions_input)

        return user

    def update(self, instance, validated_data):
        permissions_input = validated_data.pop('screen_permissions_input', [])

        if 'email' in validated_data:
            validated_data['is_email_verified'] = False
        if 'phone' in validated_data:
            validated_data['is_phone_verified'] = False

        if validated_data.pop('remove_profilepicture', False):
            instance.profilepicture = None
            instance.save(update_fields=['profilepicture'])

        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save(update_fields=['password'])

        if permissions_input:
            self._save_screen_permissions(user, permissions_input)

        return user


# =============================================================================
# Register Serializer (OTP-gated public sign-up — not used in CRM admin flow)
# =============================================================================

class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(allow_blank=False)
    fullname = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, max_length=30)
    is_email_verified = serializers.CharField(read_only=True)
    is_phone_verified = serializers.CharField(read_only=True)
    gender = serializers.ChoiceField(choices=GENDER_CHOICES)
    gender_name = serializers.SerializerMethodField()
    email = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)
    phoneotp = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    emailotp = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def get_gender_name(self, obj):
        return obj.get_gender_display()

    def get_fullname(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def validate_email(self, value):
        try:
            value = validate_contact_email(value)
        except Exception as exc:
            raise serializers.ValidationError(str(exc))
        q = User.objects.all()
        if self.instance:
            q = q.exclude(pk=self.instance.pk)
        if q.filter(email=value).exists():
            raise serializers.ValidationError('This email is already in use.')
        return value

    def validate_phone(self, value):
        try:
            return validate_contact_phone(value)
        except Exception as exc:
            raise serializers.ValidationError(str(exc))

    def validate_username(self, value):
        if not value.isalnum():
            raise serializers.ValidationError('Username must contain only alphanumeric characters.')
        q = User.objects.all()
        if self.instance:
            q = q.exclude(pk=self.instance.pk)
        if q.filter(username=value, is_active=True).exists():
            raise serializers.ValidationError('This username is already in use.')
        return value

    def validate(self, attrs):
        from Core.System.models import TemporaryVerification
        phone    = attrs.get('phone', '')
        email    = attrs.get('email', '')
        phoneotp = attrs.pop('phoneotp', '')
        emailotp = attrs.pop('emailotp', '')

        if not (phoneotp or emailotp):
            raise serializers.ValidationError({'message': 'OTP is mandatory'})
        if phoneotp:
            if not TemporaryVerification.objects.filter(mobile=phone, otp=phoneotp, is_phone_verified=True, type=1).last():
                raise serializers.ValidationError({'message': 'Phone verification failed'})
        if emailotp:
            if not TemporaryVerification.objects.filter(email=email, otp=emailotp, is_email_verified=True, type=2).last():
                raise serializers.ValidationError({'message': 'Email verification failed'})
        return super().validate(attrs)

    class Meta:
        model = User
        read_only_fields = ['otp']
        fields = [
            'username', 'fullname', 'email', 'phone',
            'emailotp', 'phoneotp', 'password',
            'first_name', 'last_name', 'otp',
            'gender', 'gender_name',
            'is_email_verified', 'is_phone_verified', 'is_active',
        ]

    def create(self, validated_data):
        validated_data['otp'] = get_random_string(4, allowed_chars=string.digits)
        return User.objects.create_user(**validated_data)


# =============================================================================
# RRGMS Permission Serializers
# =============================================================================

from Users.models import Screen, UserPermission, PermissionTemplate, PermissionTemplateDetail, PermissionAuditLog


class ScreenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Screen
        fields = ['id', 'code', 'name', 'description', 'is_active', 'order']


class UserPermissionSerializer(serializers.ModelSerializer):
    screen_name = serializers.CharField(source='screen.name', read_only=True)
    screen_code = serializers.CharField(source='screen.code', read_only=True)

    class Meta:
        model = UserPermission
        fields = [
            'id', 'user', 'screen', 'screen_name', 'screen_code',
            'can_view', 'can_add', 'can_edit', 'can_delete', 'can_export',
            'is_view_only', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class UserWithPermissionsSerializer(serializers.ModelSerializer):
    screen_permissions = serializers.SerializerMethodField()
    reporting_manager_name = serializers.SerializerMethodField()
    team_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 'phone',
            'designation', 'joining_date',
            'reporting_manager', 'reporting_manager_name',
            'user_status', 'is_active',
            'lead_data_scope', 'followup_data_scope',
            'sitevisit_data_scope', 'booking_data_scope',
            'must_reset_password',
            'leads_assigned', 'site_visits', 'bookings', 'registrations',
            'screen_permissions', 'team_count', 'created_at',
        ]

    def get_screen_permissions(self, obj):
        perms = UserPermission.objects.filter(user=obj).select_related('screen')
        return [
            {
                'screen_id': p.screen.id,
                'screen_code': p.screen.code,
                'screen_name': p.screen.name,
                'can_view': p.can_view,
                'can_add': p.can_add,
                'can_edit': p.can_edit,
                'can_delete': p.can_delete,
                'can_export': p.can_export,
            }
            for p in perms
        ]

    def get_reporting_manager_name(self, obj):
        if obj.reporting_manager:
            return f"{obj.reporting_manager.first_name} {obj.reporting_manager.last_name}".strip() or obj.reporting_manager.username
        return None

    def get_team_count(self, obj):
        return obj.team_members.count()


class PermissionTemplateSerializer(serializers.ModelSerializer):
    details = serializers.SerializerMethodField()

    class Meta:
        model = PermissionTemplate
        fields = ['id', 'name', 'description', 'is_active', 'created_at', 'details']

    def get_details(self, obj):
        return [
            {
                'screen_id': d.screen_id,
                'screen_name': d.screen.name,
                'screen_code': d.screen.code,
                'can_view': d.can_view,
                'can_add': d.can_add,
                'can_edit': d.can_edit,
                'can_delete': d.can_delete,
                'can_export': d.can_export,
            }
            for d in obj.details.select_related('screen').all()
        ]


class PermissionAuditLogSerializer(serializers.ModelSerializer):
    changed_by_username = serializers.CharField(source='changed_by.username', read_only=True)
    target_user_username = serializers.CharField(source='target_user.username', read_only=True)

    class Meta:
        model = PermissionAuditLog
        fields = [
            'id', 'changed_by', 'changed_by_username',
            'target_user', 'target_user_username',
            'action', 'field_changed', 'old_value', 'new_value',
            'timestamp', 'ip_address',
        ]
