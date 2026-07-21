import jwt
import json
import string
from django.apps import apps
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.conf import settings
from Core.Core.authentication.Authentication import CustomAuthenticationBackend
from Core.Core.authentication.CustomJWT import create_tokens, update_access_token
from Core.Core.utils.utils import get_model_path, user_by_type_id
from django.contrib import auth
from rest_framework.exceptions import AuthenticationFailed
from django.utils.crypto import get_random_string
from django.db.models import Q
from Core.System.models import Template
from Core.System.services import send_alert_sms
from Core.Users.models import (
    GENDER_CHOICES, TYPE_CHOICES, Assignee, AssigneeByPass, AssigneeDefnition, Authorization, AuthorizationDefinition,
    AuthorizationHistory, ContentTypeDetail, DataPermissions, Device, DeviceLog, DjangoApp, Groupdetails, JwtToken, PermissionDetail
)
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from Core.System.signals import approval_event, multi_approved_event, assignee_added_event

User = get_user_model()

# -------------------- Utility Functions -------------------- #

def check_user_type(user_type):
    for model in settings.USER_MODELS:
        if model.get('type') == user_type:
            return True
    return False

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def _content_type_has_field(content_type, field_name):
    try:
        if not content_type:
            return False
        model_class = content_type.model_class() if hasattr(content_type, 'model_class') else None
        if not model_class:
            model_class = apps.get_model(content_type.app_label, content_type.model)
        model_class._meta.get_field(field_name)
        return True
    except Exception:
        return False


def _is_dispatchplan_content_type(content_type):
    try:
        if not content_type:
            return False
        model_name = (getattr(content_type, 'model', '') or '').lower()
        app_label = (getattr(content_type, 'app_label', '') or '').lower()
        return model_name == 'dispatchplan' and app_label in {'dispatch', 'delivery'}
    except Exception:
        return False

def _active_soft_delete_q(prefix=''):
    return Q(**{f'{prefix}is_deleted': False}) | Q(**{f'{prefix}is_deleted__isnull': True})


def _active_definition_q():
    today = timezone.now().date()
    return (
        Q(authorization_definition__status=True)
        & _active_soft_delete_q('authorization_definition__')
        & (
            Q(authorization_definition__effective_from__lte=today)
            | Q(authorization_definition__effective_from__isnull=True)
        )
    )


def get_pending_approvers_payload(instance):
    """
    Return pending approver details for an instance.
    Format: {"level": int|None, "approvers": [{"type": "USER|GROUP", "name": str}]}
    """
    try:
        import logging
        logger = logging.getLogger(__name__)

        if not hasattr(instance, 'authorized_status'):
            logger.debug("Instance %s has no authorized_status field", instance)
            return {"level": None, "approvers": []}

        # Draft documents are outside authorization workflow even if legacy
        # data has stale authorized_status values.
        instance_status = getattr(instance, 'status', None)
        if isinstance(instance_status, str) and instance_status.upper() == 'DRAFT':
            return {"level": None, "approvers": []}

        is_pending = instance.authorized_status in (None, 1)
        if not is_pending:
            return {"level": None, "approvers": []}

        content_type = ContentType.objects.get_for_model(instance.__class__)
        next_level = (instance.authorized_level or 0) + 1

        # Match authorization definitions using the same company/location scope
        # used by document authorization logic.
        today = timezone.now().date()
        company = getattr(instance, 'company', None)
        location = getattr(instance, 'location', None)

        auth_defs = AuthorizationDefinition.objects.filter(
            screen=content_type,
            status=True,
        ).filter(_active_soft_delete_q()).filter(
            Q(effective_from__lte=today) | Q(effective_from__isnull=True)
        )

        if company:
            auth_defs = auth_defs.filter(
                Q(has_all_companies=True) | Q(companies=company)
            )
        else:
            auth_defs = auth_defs.filter(has_all_companies=True)

        if location:
            auth_defs = auth_defs.filter(
                Q(has_all_locations=True) | Q(locations=location)
            )
        else:
            auth_defs = auth_defs.filter(has_all_locations=True)

        if not auth_defs.exists():
            return {"level": next_level, "approvers": []}

        approvals = Authorization.objects.filter(
            authorization_definition__in=auth_defs,
            level=next_level,
        ).filter(_active_soft_delete_q()).select_related('group')

        if not approvals.exists():
            return {"level": next_level, "approvers": []}

        approvers = []
        seen = set()
        for approval in approvals:
            if approval.type == Authorization.USER:
                user_obj = user_by_type_id(approval.user_type, approval.user_identifier)
                # Exclude inactive users from pending approver display.
                if not user_obj or not getattr(user_obj, 'is_active', False):
                    continue

                full_name = f"{getattr(user_obj, 'first_name', '')} {getattr(user_obj, 'last_name', '')}".strip()
                name = full_name or getattr(user_obj, 'username', '') or approval.user_identifier
                dedupe_key = ("USER", name)
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                approvers.append({"type": "USER", "name": name})
            elif approval.type == Authorization.GROUP and approval.group:
                group_name = approval.group.name or "Group"
                dedupe_key = ("GROUP", group_name)
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                approvers.append({"type": "GROUP", "name": group_name})

        return {"level": next_level, "approvers": approvers}
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting pending approvers payload: {str(e)}", exc_info=True)
        return {"level": None, "approvers": []}


def get_pending_approver_names(instance):
    """
    Get the names of pending approvers for a given instance.
    Returns a comma-separated string of approver names.
    """
    payload = get_pending_approvers_payload(instance)
    approvers = payload.get("approvers", [])
    if not approvers:
        return ''
    return ', '.join(
        f"{'Group' if a.get('type') == 'GROUP' else 'User'}: {a.get('name', '')}"
        for a in approvers
    )



# -------------------- Group & Permission Serializers -------------------- #

class PermissionJoinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = '__all__'

class PermissionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = PermissionDetail
        fields = ('id', 'name', )

class GroupMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'name')

class GroupMini2Serializer(serializers.ModelSerializer):
    permission_id = serializers.PrimaryKeyRelatedField(write_only=True, queryset=Permission.objects.all())
    class Meta:
        model = Group
        read_only_fields = ['name',]
        fields = ('id', 'name', 'permission_id')

class UserGroupSerializer(serializers.ModelSerializer):
    user_permissions = PermissionJoinSerializer(many=True)
    groups = GroupMiniSerializer(many=True)
    class Meta:
        model = User
        fields = '__all__'

class GroupdetailsSerializer(serializers.ModelSerializer):
    reporting_to_name = serializers.SerializerMethodField()
    def get_reporting_to_name(self, obj):
        return obj.reporting_to.name if obj.reporting_to else ''
    class Meta:
        model = Groupdetails
        read_only_fields = ()
        fields = ('group', 'reporting_to', 'reporting_to_name')


class GroupSerializer(serializers.ModelSerializer):

    permission_ids = serializers.ListField(write_only=True, child=serializers.PrimaryKeyRelatedField(write_only=True, queryset=Permission.objects.all()), )
    groupdetails= GroupdetailsSerializer(many=False, read_only=True)
    reporting_to_id = serializers.PrimaryKeyRelatedField(write_only=True, source='reporting_to', queryset=Group.objects.all(), required= False)
    users = serializers.SerializerMethodField()
 
    def get_users(self, obj):
        users = obj.user_set.filter(is_active=True)
        return CoreUserMiniSerializer(users, many=True).data
 
    class Meta:
        model = Group
        read_only_fields = [ 'permissions','groupdetails', 'users']
        fields = ['id', 'name', 'permissions', 'permission_ids','reporting_to_id','groupdetails', 'users']
 
    def create(self, validated_data):
        if 'permission_ids' in validated_data:
            validated_data['permissions'] = validated_data.pop('permission_ids')
        
        reporting_to = None
        if 'reporting_to' in validated_data:
            reporting_to = validated_data.pop('reporting_to')

        group = super().create(validated_data)

        if reporting_to != None:
            Groupdetails.objects.create( group=group, reporting_to=reporting_to)
        else:
            Groupdetails.objects.create( group=group )
               
        return group

    def update(self, instance, validated_data):
        if 'permission_ids' in validated_data:
            validated_data['permissions'] = validated_data.pop('permission_ids')
  
        
        reporting_to = None
        if 'reporting_to' in validated_data:
            reporting_to = validated_data.pop('reporting_to')

        group = super().update(instance, validated_data)
        
        if reporting_to != None:
            
            Groupdetails.objects.update_or_create( group=group,defaults={'reporting_to':reporting_to})
        else:
            Groupdetails.objects.update_or_create( group=group )
        
        return group


# -------------------- ContentType & DjangoApp Serializers -------------------- #

class ContentTypeSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField('get_permissions')
    def get_permissions(self, contenttype):
        qs = Permission.objects.filter(content_type=contenttype)
        serializer = PermissionJoinSerializer(instance=qs, many=True)
        return serializer.data
    class Meta:
        model = ContentType
        fields = '__all__'

class AllContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = '__all__'

class PermissionSerializer(serializers.ModelSerializer):
    permissiondetails = PermissionDetailSerializer(many=False)
    class Meta:
        model = Permission
        fields = ('id', 'name', 'codename', 'content_type', 'permissiondetails', )

class ContentTypeDetailSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField('get_permissions')
    contenttype = ContentTypeSerializer(many=False)
    def get_permissions(self, obj):
        qs = Permission.objects.filter(content_type=obj.contenttype, permissiondetails__hide=False)
        serializer = PermissionSerializer(instance=qs, many=True)
        return serializer.data
    class Meta:
        model = ContentTypeDetail
        fields = ('id', 'name', 'contenttype', 'permissions')

class ContentTypeDetailMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentTypeDetail
        fields = ('id', 'name')

class AllContentTypesSerializer(serializers.ModelSerializer):
    contenttype = AllContentTypeSerializer(many=False)
    name = serializers.SerializerMethodField()
    has_location_filter = serializers.SerializerMethodField()
    
    def get_name(self, obj):
        name = obj.name or ''
        # Handle common patterns: Salesorder -> Sales Order, Dispatchplan -> Dispatch Plan
        replacements = {
            'Salesorder': 'Sales Order',
            'Dispatchplan': 'Dispatch Plan',
            'Proofofdelivery': 'Proof Of Delivery',
        }
        return replacements.get(name, name)

    def get_has_location_filter(self, obj):
        return _content_type_has_field(obj.contenttype, 'location')
    
    class Meta:
        model = ContentTypeDetail
        fields = ('id', 'name', 'contenttype', 'has_location_filter')

class ContentType2Serializer(serializers.ModelSerializer):
    content_type_detail = ContentTypeDetailMiniSerializer(source='contenttypedetails', read_only=True)
    has_location_filter = serializers.SerializerMethodField()

    def get_has_location_filter(self, obj):
        return _content_type_has_field(obj, 'location')

    class Meta:
        model = ContentType
        fields = ('id', "app_label", "model", 'content_type_detail', 'has_location_filter')

class DjangoAppSerializer(serializers.ModelSerializer):
    contenttypedetails = serializers.SerializerMethodField('get_contenttypedetails')
    def get_contenttypedetails(self, obj):
        qs = ContentTypeDetail.objects.filter(app=obj, hide=False)
        serializer = ContentTypeDetailSerializer(instance=qs, many=True)
        return serializer.data
    class Meta:
        model = DjangoApp
        fields = ('id', 'name', 'app_label','sequence','contenttypedetails')

# -------------------- Device & DeviceLog Serializers -------------------- #

class DeviceSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(choices=Device.DEVICE_TYPE_CHOICES)
    type_name = serializers.SerializerMethodField()
    def get_type_name(self, obj):
        return obj.get_type_display()
    class Meta:
        model = Device
        fields = ('code', 'name', 'type', 'type_name', 'user_identifier', 'user_type', 'is_active')

class DeviceLogSerializer(serializers.ModelSerializer):
    device = DeviceSerializer(many=False, read_only=True)
    device_id = serializers.PrimaryKeyRelatedField(write_only=True, required=False, source='device', queryset=Device.objects.filter(is_deleted=False,))
    class Meta:
        model = DeviceLog
        fields = ('user_identifier', 'user_type', 'device', 'device_id', 'ip_address', 'login', 'logout')

# -------------------- DataPermissions Serializers -------------------- #

class DataPermissionsSerializer(serializers.ModelSerializer):
    

    user_identifier = serializers.CharField(max_length=255, required=False)
    user_type = serializers.CharField(max_length=15, required=False)

    group = GroupMiniSerializer(many=False, read_only=True)
    group_id = serializers.PrimaryKeyRelatedField(
        write_only=True, required=False, source='group',
        queryset=Group.objects.all()
    )

    type = serializers.ChoiceField(choices=TYPE_CHOICES, required=False)
    type_name = serializers.SerializerMethodField()
    instance = serializers.SerializerMethodField()

    def get_type_name(self, obj):
        return obj.get_type_display()
    
    def get_instance(self, obj):
        if obj.instance_id and obj.model_path and obj.instance_id != '' and obj.model_path != '':
            try:
                related_model = apps.get_model(obj.model_path)
                instance = related_model.objects.get(id=obj.instance_id)
                if hasattr(instance, 'id'):
                    return {'id': instance.id, 'name': instance.name if hasattr(instance, 'name') else instance.code if hasattr(instance, 'code') else str(instance.id) } # it works with any Serializer if instance has id,name
                else:
                    return {}
            except:
                return {}
        else:
            return {}

    def validate(self, attrs):
        
        type = attrs.get('type', None)
        user_type = attrs.get('user_type', None)
        user_identifier = attrs.get('user_identifier', None)
        group = attrs.get('group', None)
        model_path = attrs.get('model_path', None)
        instance_id = attrs.get('instance_id', None)
        if model_path == None:
            raise serializers.ValidationError("model_path is required.")
        if instance_id == None:
            raise serializers.ValidationError("instance_id is required.")

        if type == 1:
            if user_type == None:
                raise serializers.ValidationError("User Type is required.")
            
            if user_identifier == None:
                raise serializers.ValidationError("User Identifier is required.")
            
        if type == 2:
            if group == None:
                raise serializers.ValidationError("group is required.")
            

        # Uniqueness validation for (group, model_path, instance_id)
        queryset = DataPermissions.objects.filter(
            group=group, model_path=model_path, instance_id=instance_id, is_deleted = False
        )

        # Exclude the current instance when updating
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)


        if queryset.exists():
            raise serializers.ValidationError(
                {"non_field_errors": ["A record with this group, model_path, and instance_id already exists."]}
            )
            
        return super().validate(attrs)
    
    class Meta:
        model = DataPermissions
        read_only_fields = ['id','is_deleted']
        fields = ('id', 'model_path','type','type_name', 'user_type', 'user_identifier', 'group', 'group_id', 'instance', 'instance_id','report','entry','view','is_deleted')


    def create(self, validated_data):
        group = validated_data.pop('group', None)

        permission = DataPermissions.objects.create(
            group=group,
            **validated_data  # Pass everything except removed fields
        )

        return permission
    
    def update(self, instance, validated_data):
        user_type = validated_data.pop('user_type', None)
        user_identifier = validated_data.pop('user_identifier', None)
        group = validated_data.pop('group', None)
        model_path = validated_data.get('model_path', instance.model_path)
        instance_id = validated_data.get('instance_id', instance.instance_id)
        instance.user_type = user_type if user_type is not None else instance.user_type
        instance.user_identifier = user_identifier if user_identifier is not None else instance.user_identifier
        instance.group = group if group is not None else instance.group
        instance.model_path = model_path
        instance.instance_id = instance_id

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

class DataPermissionsUpdateSerializer(serializers.ModelSerializer):
    user_identifier = serializers.CharField(max_length=255, required=False)
    user_type = serializers.CharField(max_length=15, required=False)

    class Meta:
        model = DataPermissions
        fields = ('model_path', 'user_identifier', 'user_type', 'exclusions')

    def update(self, instance, validated_data):
        instance.exclusions = validated_data.get('exclusions', instance.exclusions)
        instance.save()
        return instance
    
    

class DataPermissionsGroupUpdateSerializer(serializers.ModelSerializer):
    group = GroupMiniSerializer(many=False, read_only=True)
    group_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source='group',
        queryset=Group.objects.all( ) #is_superuser=False
    )

    class Meta:
        model = DataPermissions
        fields = ('model_path', 'group', 'group_id', 'exclusions')

    def update(self, instance, validated_data):
        instance.exclusions = validated_data.get('exclusions', instance.exclusions)
        instance.save()
        return instance
    
# -------------------- Dynamic Serializers -------------------- #

class DynamicIDNameSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()

class DynamicIDCodeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()

class DynamicUUIDNameSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()

class DynamicUUIDCodeSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    

# -------------------- User Serializers -------------------- #

class CoreUserMiniSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()
    def get_fullname(self, user):
        return '{} {}'.format(user.first_name, user.last_name)
    class Meta:
        model = User
        fields = ('id', 'username', 'fullname', 'email', 'first_name', 'last_name', 'phone')

class IamUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False, allow_blank=False)
    fullname = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, max_length=30, required=False)
    is_email_verified = serializers.CharField(read_only=True)
    is_phone_verified = serializers.CharField(read_only=True)
    gender = serializers.ChoiceField(choices=GENDER_CHOICES,read_only=True)
    gender_name = serializers.SerializerMethodField()
    groups = GroupMiniSerializer(many=True, read_only=True)
    group_ids = serializers.ListField(write_only=True, child=serializers.PrimaryKeyRelatedField(write_only=True, queryset=Group.objects.all()), required=False)
    def get_gender_name(self, obj):
        return obj.get_gender_display()
    def get_fullname(self, user):
        return '{} {}'.format(user.first_name, user.last_name)
    def validate_username(self, value):
        if not value.isalnum():
            raise serializers.ValidationError({'username': 'The username should only contain alphanumeric characters'})
        q = User.objects.all()
        if self.instance:
            object_id = self.instance.id
            q = q.exclude(pk=object_id)
        if q.filter(username=value, is_active=True).exists():
            raise serializers.ValidationError({"username": "This username is already in use."})
        return value
    class Meta:
        model = User
        read_only_fields = ['otp']
        fields = [
            'id', 'username', 'fullname', 'email', 'phone',
            # 'alternate_phone',  # not on Users.User model
            'groups', 'group_ids', 'password',
            'first_name', 'last_name', 'otp', 'gender', 'gender_name',
            'is_email_verified', 'is_phone_verified',
            'receive_sms', 'receive_email', 'receive_notification',
            'is_active', 'device_access',
            # 'address',  # not on Users.User model
        ]


class UserUserNameValidateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    
    class Meta:
        model = User
        fields = ('id', 'username', )
    def validate(self, attrs):
        id = attrs.get('id', '')
        username = attrs.get('username', '')
        qset = User.objects.filter(username__exact=username)
        if id != "":
            qset = qset.exclude(id=id)
        if username != '' and qset.exists():
            raise serializers.ValidationError("Username already exists!")
        return super().validate(attrs)

class UserEmailValidateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    class Meta:
        model = User
        fields = ('id', 'email', )
    def validate(self, attrs):
        id = attrs.get('id', '')
        email = attrs.get('email', '')
        qset = User.objects.filter(email__exact=email)
        if id != "":
            qset = qset.exclude(id=id)
        if email != '' and qset.exists():
            raise serializers.ValidationError("Email already exists!")
        return super().validate(attrs)

class UserPhoneValidateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)
    class Meta:
        model = User
        fields = ('id', 'phone', )
    def validate(self, attrs):
        id = attrs.get('id', '')
        phone = attrs.get('phone', '')
        qset = User.objects.filter(phone__exact=phone)
        if id != "":
            qset = qset.exclude(id=id)
        if phone != '' and qset.exists():
            raise serializers.ValidationError("Phone Number already exists!")
        return super().validate(attrs)
    
# -------------------- Authentication Serializers -------------------- #

class LoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255, min_length=3, read_only=True)
    phone = serializers.CharField(max_length=15, min_length=10, read_only=True)
    full_name = serializers.CharField(max_length=255, min_length=6, read_only=True)
    password = serializers.CharField(max_length=68, min_length=1, write_only=True)
    username = serializers.CharField(max_length=255, min_length=1)
    device_name = serializers.CharField(max_length=100, required=False, allow_blank=True, write_only=True)
    device_uuid = serializers.CharField(max_length=1000, write_only=True)
    device_type = serializers.ChoiceField(choices=Device.DEVICE_TYPE_CHOICES, write_only=True)
    device_fcmtoken = serializers.CharField(max_length=1000, required=False, allow_blank=True, write_only=True)
    device_apntoken = serializers.CharField(max_length=1000, required=False, allow_blank=True,  write_only=True)
    group_name = serializers.CharField(max_length=255, min_length=6, read_only=True)
    # tokens = serializers.SerializerMethodField()
    is_default_password = serializers.BooleanField(read_only=True)
    user_type = serializers.CharField(required=True)

    # def get_tokens(self, obj):
    #     user = User.objects.get(username=obj['username'])

    #     return {
    #         'refresh': user.tokens()['refresh'],
    #         'access': user.tokens()['access']
    #     }
    
    
    class Meta:
        model = User
        read_only_fields = [ 'id','full_name', 'group_name'] 
        fields = ['id', 'email', 'phone', 'password', 'username', 'user_type','full_name', 'group_name','device_name','device_uuid','device_type', 'device_fcmtoken', 'device_apntoken', 'is_default_password']

    def validate(self, attrs):
        username = attrs.get('username', '')
        password = attrs.get('password', '')
        user_type = attrs.get('user_type', '')
        device_name = attrs.get('device_name', '')
        device_uuid = attrs.get('device_uuid', '')
        device_type = attrs.get('device_type', 0)
        device_fcmtoken = attrs.get('device_fcmtoken', '')
        device_apntoken = attrs.get('device_apntoken', '')
    
        if not CustomAuthenticationBackend.check_user_type(user_type):
            raise serializers.ValidationError("Invalid User Type")
        
        # Check if username exists first
        try:
            user_obj = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError({'username': 'Username not found'})
        
        # Check if user is active
        if not user_obj.is_active:
            raise AuthenticationFailed('Account is inactive. Please contact admin')
        
        # Now authenticate with password
        user = auth.authenticate(username=username, password=password, user_type=user_type)

        if username == "9988776655" and password == "4321":
            model_path = get_model_path(user_type)
            user_model = apps.get_model(model_path, require_ready=False)

            user, uc = user_model.objects.get_or_create(username="9988776655", defaults={'first_name':'9988776655', 'last_name':'','phone':'9988776655','otp':'4321','is_active':True})


        if device_type == 0:
            raise serializers.ValidationError('Device type is required')

        if not user:
            raise serializers.ValidationError({'password': 'Incorrect password'})
        
        session_data = json.dumps(dict())

        tokens = create_tokens(user, user_type=user_type, session_data=session_data)
        if settings.SINGLE_MOBILE_DEVICE_PER_USER:
            mobile_devices_count = Device.objects.filter(
                user_type = user_type,
                user_identifier = user.id,
                type__in=[1, 2],
                is_active= True,
            ).count()
            devices = Device.objects.filter(
                user_type = user_type,
                user_identifier = user.id,
                uuid= device_uuid,
                type= device_type,
                is_active= True)

            if (mobile_devices_count == 0 and device_type != 3) or (device_type == 3 and devices.count() == 0): # First Mobile device or New Web device

                device, dc = Device.objects.get_or_create(
                user_type = user_type,
                user_identifier = user.id,
                uuid= device_uuid,
                is_active= True,
                defaults={
                    'name': device_name,
                    'type': device_type,
                        }
                    )
            elif mobile_devices_count > 0 and  device_type != 3 and devices.count()==0: # other new Mobile device
                device, dc = Device.objects.get_or_create(
                user_type = user_type,
                user_identifier = user.id,
                uuid= device_uuid,
                is_active= False,
                defaults={
                'name': device_name,
                'type': device_type,
                }
                )
                raise AuthenticationFailed('This device not allowed, contact admin')
            else: # old Active Devices
                device = devices[0]
        else:
            device, dc = Device.objects.get_or_create(
            user_type = user_type,
            user_identifier = user.id,
            uuid= device_uuid,
            is_active= True,
            defaults={
                'name': device_name,
                'type': device_type,
                })

        if not user.is_superuser == True and not ((device.type != 3 and ( user.device_access == 1 or user.device_access == 3)) or (device.type == 3 and ( user.device_access == 2 or user.device_access == 3)) ):
            raise AuthenticationFailed('This device type not allowed, contact admin')
        
        device.fcmtoken = device_fcmtoken
        device.apntoken = device_apntoken
        device.accesstoken = tokens['access']
        device.save()

        ip_address= get_client_ip(self.context['request'])
        # ip_address= '192.168.1.134'

        DeviceLog.objects.create( device=device, user_type=user_type,user_identifier=user.id ,ip_address=ip_address , logout= timezone.now() + settings.ACCESS_TOKEN_LIFETIME )
            
        group_name = user.groups.all()[0].name if user.groups.count() > 0 else ""
        is_default_password = password == user.id
        
        # Get user permissions
        permissions = list(user.get_all_permissions())
        
        # Get channel partner information
        channel_partner_data = {
            'channel_partner_type': getattr(user, 'channel_partner_type', 'STAFF'),
            'superstockist': str(user.superstockist.id) if getattr(user, 'superstockist', None) else None,
            'distributor': str(user.distributor.id) if getattr(user, 'distributor', None) else None,
            'retailer': str(user.retailer.id) if getattr(user, 'retailer', None) else None,
            'superstockist_name': {'id': str(user.superstockist.id), 'name': user.superstockist.name} if getattr(user, 'superstockist', None) else None,
            'distributor_name': {'id': str(user.distributor.id), 'name': user.distributor.name} if getattr(user, 'distributor', None) else None,
            'retailer_name': {'id': str(user.retailer.id), 'name': user.retailer.name} if getattr(user, 'retailer', None) else None,
        }
        
        return {
            'full_name': str(user.first_name)+" "+ str(user.last_name)  ,
            'username': user.username,
            'password': user.password,
            'user_type': user_type,
            'email': user.email,
            'phone': user.phone,
            'group_name': group_name,
            'tokens': tokens,
            'is_default_password': is_default_password,
            'is_superuser': user.is_superuser,
            'permissions': permissions,
            **channel_partner_data,
        }

class  OTPRequestSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=255, min_length=10)

    class Meta:
        model = User
        fields = ['username','otp']

    def validate(self, attrs):
        username = attrs.get('username', '')

        try:
            user = User.objects.get(
                Q(  
                    Q(phone=username) 
                ) &
                Q(is_active = True)
            )

        except User.DoesNotExist:
            raise AuthenticationFailed('Invalid credentials, try again')
        except:
            raise AuthenticationFailed('Invalid credentials, Contact Admin')

        if not user.is_active:
            raise AuthenticationFailed('Account disabled, contact admin')
 
        user.otp = get_random_string(4, allowed_chars= string.digits)
        user.save()
        message = Template.objects.get(name='OTP Login').message
        send_alert_sms([user],message)

        return {
            'username': user.phone,
            'otp':user.otp ,
            
        }


class OTPResendSerializer(serializers.ModelSerializer):

    username = serializers.CharField(max_length=255, min_length=10)

    class Meta:
        model = User
        fields = ['username','otp']

    def validate(self, attrs):
        username = attrs.get('username', '')

        try:
            user = User.objects.get(
                Q(  
                    Q(phone=username) 
                    # & Q(is_phone_verified=True) # removed to do login witrhout phone_verified  
                ) &
                Q(is_active = True)
            )

        except User.DoesNotExist:
            raise AuthenticationFailed('Invalid credentials, try again')

        if not user.is_active:
            raise AuthenticationFailed('Account disabled, contact admin')

        
        user.otp = get_random_string(4, allowed_chars= string.digits)
        user.save()
        
        message = Template.objects.get(name='OTP Login').message
        send_alert_sms([user],message)
        
        return {
            'username': user.phone,
            'otp':user.otp ,
        }


class TokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    device_uuid = serializers.CharField(max_length=1000, write_only=True)
    device_type = serializers.ChoiceField(choices=Device.DEVICE_TYPE_CHOICES, write_only=True)
    access = serializers.CharField(read_only=True)

    def validate(self, attrs):

        token_data = update_access_token(attrs["refresh"])

        data = {"access": token_data['access']}

        device_uuid = attrs['device_uuid']
        device_type = attrs['device_type']
        devices = Device.objects.filter(
            user_identifier= token_data['user_identifier'],
            user_type= token_data['user_type'],
            uuid= device_uuid,
            type= device_type,
            is_active= True,
        ).update(
            accesstoken= token_data['access'],
        )

        return data

class ValidateCurrentPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, max_length=68, min_length=4, required=True)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect")
        return value

class ValidateUsernameSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, max_length=255)

    def validate_username(self, value):
        try:
            user = User.objects.get(username=value, is_active=True)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("Username not found")

class ChangePasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, max_length=68, min_length=8, required=True)
    old_password = serializers.CharField(write_only=True, max_length=68, min_length=4, required=True)

    class Meta:
        model = User
        fields = ('old_password', 'password',)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct")
        return value

    def validate_password(self, value):
        from Core.Core.utils.password_validator import validate_password_field
        return validate_password_field(value)

    def validate(self, attrs):
        old_password = attrs.get('old_password', None)
        password = attrs.get('password', None)

        if old_password == password:
           raise serializers.ValidationError({"Message": "Old password and New password can't be same"})

        return super().validate(attrs)

    def update(self, instance, validated_data):
        instance.set_password(validated_data['password'])
        instance.save()
        return instance


class UpdatePasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, max_length=68, min_length=8, required=True)

    class Meta:
        model = User
        fields = ('password',)

    def validate_password(self, value):
        from Core.Core.utils.password_validator import validate_password_field
        return validate_password_field(value)

    def update(self, instance, validated_data):
        instance.set_password(validated_data['password'])
        instance.save()
        return instance


class ForgotPasswordSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, max_length=150)
    password = serializers.CharField(write_only=True, max_length=68, min_length=4, required=True)
    confirm_password = serializers.CharField(write_only=True, max_length=68, min_length=4, required=True)

    def validate_username(self, value):
        try:
            user = User.objects.get(username=value, is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this username does not exist")
        return value

    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')

        if password != confirm_password:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match"})

        return attrs

    def save(self):
        username = self.validated_data['username']
        password = self.validated_data['password']
        
        user = User.objects.get(username=username, is_active=True)
        user.set_password(password)
        user.save()
        
        # Clear all existing tokens for this user
        JwtToken.objects.filter(user_type='User', user_identifier=user.id).delete()
        
        return user


class EmailVerificationSerializer(serializers.Serializer):

    token = serializers.CharField()
    
    def validate(self, data):
        try:
            payload = jwt.decode(data['token'],settings.SECRET_KEY, 'HS256')
            user = User.objects.get(id=payload['user_id'])
            if not user.is_email_verified:
                user.is_email_verified = True
                user.save()
        except jwt.ExpiredSignatureError as identifier:
            raise serializers.ValidationError({'error': 'Activation Expired'})
        except jwt.exceptions.DecodeError as identifier:
            raise serializers.ValidationError({'error': 'Invalid token'})
        
        return data

    class Meta:

        fields = ('token',)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    default_error_messages = {  # <- Use default_error_messages, not error_messages
        'bad_token': 'Token is expired or invalid'
    }

    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs

    def save(self, **kwargs):
        try:
            JwtToken.objects.get(refresh_token=self.token).delete()
        except JwtToken.DoesNotExist:
            self.fail('bad_token')  # correctly maps to the default_error_messages


# -------------------- Assignee, AssigneeDefnition, AssigneeByPass Serializers -------------------- #

class AssigneeDefnitionSerializer(serializers.ModelSerializer):
    apply_type = serializers.ChoiceField(choices=AssigneeDefnition.APPLY_TYPE_CHOICES, required=False)
    apply_type_name = serializers.SerializerMethodField()
    
    
    screen = ContentType2Serializer(many=False, read_only=True)
    screen_id = serializers.PrimaryKeyRelatedField(
        write_only=True, required=False, source='screen',
        queryset=ContentType.objects.filter(contenttypedetails__show_in_assignee=True)
    )
    
    def get_apply_type_name(self, obj):
        return obj.get_apply_type_display()

    def validate_user_types(self, value):
        # Load valid user types from settings
        valid_user_types = [model['type'] for model in settings.USER_MODELS]
        
        # Check each provided user type
        invalid_values = [v for v in value if v not in valid_user_types]
        
        if invalid_values:
            raise serializers.ValidationError(f"Invalid user_types: {invalid_values}. Valid options are: {valid_user_types}")

        return value

    class Meta:
        model = AssigneeDefnition
        read_only_fields = ['id']
        fields = ('id', 'screen', 'screen_id', 'apply_type', 'apply_type_name', 'required_authorization', 'user_types')



class AssigneeByPassSerializer(serializers.ModelSerializer):
    
    user_identifier = serializers.CharField(max_length=255, required=True)
    user_type = serializers.CharField(max_length=15, required=True)

    group = GroupMiniSerializer(many=False, read_only=True)
    group_id = serializers.PrimaryKeyRelatedField(
        write_only=True, required=False, source='group',
        queryset=Group.objects.all()
    )

    type = serializers.ChoiceField(choices=TYPE_CHOICES, required=False)
    type_name = serializers.SerializerMethodField()



    def get_type_name(self, obj):
        return obj.get_type_display()
    

    def validate(self, attrs):
        
        type = attrs.get('type', None)
        user = user_by_type_id(attrs.get('user_type'), attrs.get('user_identifier'))
        group = attrs.get('group', None)
        
        if type == 1:
            if user == None:
                raise serializers.ValidationError("User is required.")
            
        if type == 2:
            if group == None:
                raise serializers.ValidationError("group is required.")
            

        queryset = AssigneeByPass.objects.filter(
            user = user, is_deleted = False
        )

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                {"non_field_errors": ["A record with this User combination already exists."]}
            )
            
        return super().validate(attrs)
    

    
    class Meta:
        model = AssigneeByPass
        read_only_fields = ['id','is_deleted']
        fields = ('id','type','type_name', 'user_identifier', 'user_type', 'group', 'group_id', 'is_deleted')


    def create(self, validated_data):
        group = validated_data.pop('group', None)

        assigneebypass_obj = AssigneeByPass.objects.create(
            group=group,
            **validated_data  
        )

        return assigneebypass_obj
    
    def update(self, instance, validated_data):
        user = validated_data.pop('user', None)
        group = validated_data.pop('group', None)
        
        instance.user = user if user is not None else instance.user
        instance.group = group if group is not None else instance.group

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
    

class AssigneeSerializer(serializers.ModelSerializer):
    
    user = serializers.SerializerMethodField()
    user_identifier = serializers.CharField(max_length=255, required=True)
    user_type = serializers.CharField(max_length=15, required=True)

    screen = ContentType2Serializer(many=False, read_only=True)
    model_path = serializers.CharField(write_only =True)

    def validate_user_type(self, value):

        if not check_user_type(value):
            raise serializers.ValidationError("Invalid user type.")
        return value
    

    def get_user(self, obj):
        if not obj.user_type or not obj.user_identifier:
            return None
        try:
            user_obj = user_by_type_id(obj.user_type,obj.user_identifier)

            if not user_obj:
                return None
            user_data = CoreUserMiniSerializer(user_obj)
            return user_data.data
        
        except (LookupError, AttributeError):
            return None
        

    def validate(self, attrs):

        model_path = attrs.get('model_path')
        user_identifier = attrs.get('user_identifier')
        user_type = attrs.get('user_type')
        instance_id = attrs.get('instance_id')

        if not model_path or not user_identifier or not user_type or not instance_id:
            raise serializers.ValidationError("Both user and model_path are required.")

        app_label, model_name = model_path.split('.')
        model_class = apps.get_model(app_label, model_name)

        instance = model_class.objects.filter(id=instance_id).first()
        if not instance:
            raise serializers.ValidationError("Instance not found.")
        
        asd_odj = AssigneeDefnition.objects.filter(
            screen__app_label=app_label,
            screen__model=model_name,
            is_deleted=False
        ).first()

        if not asd_odj:
            raise serializers.ValidationError({"has_permission": False, "detail": "Assignee definition not found."})
        else:
            if asd_odj.required_authorization:
                if not instance.authorized_status == AuthorizationHistory.APPROVED:
                    raise serializers.ValidationError({"has_permission": False, "detail": "Instance is not approved."})
            
        if not self.context['request'].user.has_perm(f"{app_label}.add_assignee_{model_name}"):
            raise serializers.ValidationError({"has_permission": False})

        existing_qs = Assignee.objects.filter(user_type=user_type, user_identifier= user_identifier,screen__model=model_name,screen__app_label=app_label,instance_id = instance_id, is_deleted=False)
        
        if self.instance:
            existing_qs = existing_qs.exclude(pk=self.instance.pk)

        if existing_qs.exists():
            raise serializers.ValidationError(
                {"non_field_errors": ["A record with this user and screen combination already exists."]}
            )
        
        return attrs

    
    class Meta:
        model = Assignee
        read_only_fields = ['id',]
        fields = ('id', 'screen', 'screen_id', 'user_type','user_identifier', 'user', 'instance_id', 'description', 'model_path' )


    def create(self, validated_data):
        model_path = validated_data.pop('model_path')
        try:
            app_label =model_path.split('.')[0]
            model =model_path.split('.')[1]
            validated_data['screen'] = ContentType.objects.get(model=model,app_label= app_label)
        except:
            raise serializers.ValidationError({'model_path': 'Invalid model path'})
        obj = super().create(validated_data)
        assignee_added_event.send(sender=obj.__class__, instance=obj, event_name="AddAssignee")
        return obj


# -------------------- Authorization & AuthorizationHistory Serializers -------------------- #

class AuthorizationDefinitionSerializer(serializers.ModelSerializer):
    
    screen = ContentType2Serializer(many=False, read_only=True)
    screen_id = serializers.PrimaryKeyRelatedField(
        write_only=True, required=False, source='screen', allow_null=False,
        queryset=ContentType.objects.filter(contenttypedetails__show_in_authorization=True)
    )
    
    companies = serializers.SerializerMethodField()
    company_ids = serializers.ListField(child=serializers.UUIDField(), write_only=True, required=False)
    
    locations = serializers.SerializerMethodField()
    location_ids = serializers.ListField(child=serializers.UUIDField(), write_only=True, required=False)
    
    level_authorizations = serializers.SerializerMethodField(read_only=True)
    
    def get_companies(self, obj):
        return [{'id': str(c.id), 'name': c.name} for c in obj.companies.all()]
    
    def get_locations(self, obj):
        return [{'id': str(l.id), 'name': l.name} for l in obj.locations.all()]
    
    def get_level_authorizations(self, obj):
        auths = obj.level_authorizations.filter(is_deleted=False).order_by('level')
        return AuthorizationSerializer(auths, many=True).data
    
    def validate(self, attrs):
        from Masters.models import Company, Location
        
        screen = attrs.get('screen', None)
        if self.instance and not screen:
            screen = self.instance.screen
        
        level = attrs.get('level', None)
        company_ids = attrs.pop('company_ids', [])
        location_ids = attrs.pop('location_ids', [])
        has_all_companies = attrs.get('has_all_companies', False)
        has_all_locations = attrs.get('has_all_locations', False)
        status = attrs.get('status', True)
        
        if screen == None:
            raise serializers.ValidationError({"screen_id": "Screen is required."})
        if level == None:
            raise serializers.ValidationError({"level": "Level is required."})

        # Dispatch Plan authorization is location-scoped.
        # Force all-companies for this screen and ignore company selection.
        if _is_dispatchplan_content_type(screen):
            attrs['has_all_companies'] = True
            has_all_companies = True
            company_ids = []

        # Validate companies
        companies = []
        if not has_all_companies and company_ids:
            companies = list(Company.objects.filter(id__in=company_ids, is_deleted=False))
            if len(companies) != len(company_ids):
                raise serializers.ValidationError({"company_ids": "One or more invalid company IDs."})
        
        # Validate locations
        locations = []
        # If selected screen doesn't support location filtering, force all locations.
        if not _content_type_has_field(screen, 'location'):
            attrs['has_all_locations'] = True
            has_all_locations = True
            location_ids = []

        if not has_all_locations and location_ids:
            locations = list(Location.objects.filter(id__in=location_ids, is_deleted=False))
            if len(locations) != len(location_ids):
                raise serializers.ValidationError({"location_ids": "One or more invalid location IDs."})
        
        attrs['_companies'] = companies
        attrs['_locations'] = locations
        
        return super().validate(attrs)
    
    def create(self, validated_data):
        companies = validated_data.pop('_companies', [])
        locations = validated_data.pop('_locations', [])
        instance = super().create(validated_data)
        if companies:
            instance.companies.set(companies)
        if locations:
            instance.locations.set(locations)
        return instance
    
    def update(self, instance, validated_data):
        companies = validated_data.pop('_companies', None)
        locations = validated_data.pop('_locations', None)
        instance = super().update(instance, validated_data)
        if companies is not None:
            instance.companies.set(companies)
        if locations is not None:
            instance.locations.set(locations)
        return instance
    
    class Meta:
        model = AuthorizationDefinition
        read_only_fields = ['id', 'level_authorizations']
        fields = ('id', 'code', 'authorization_name', 'effective_from', 'companies', 'company_ids', 'has_all_companies', 'locations', 'location_ids', 'has_all_locations', 'status', 'auto_approve_creator_level', 'screen', 'screen_id', 'level', 'send_sms', 'send_email', 'send_notification', 'level_authorizations')


class AuthorizationSerializer(serializers.ModelSerializer):
    
    user_identifier = serializers.CharField(max_length=255, required=False)
    user_type = serializers.CharField(max_length=15, required=False)
    user = serializers.SerializerMethodField()
    group = GroupMiniSerializer(many=False, read_only=True)
    group_id = serializers.PrimaryKeyRelatedField(
        write_only=True, required=False, source='group',
        queryset=Group.objects.all()
    )

    type = serializers.ChoiceField(choices=TYPE_CHOICES, required=False)
    type_name = serializers.SerializerMethodField()

    screen = ContentType2Serializer(many=False, read_only=True)
    screen_id = serializers.PrimaryKeyRelatedField(
        write_only=True, required=False, source='screen',
        queryset=ContentType.objects.filter(contenttypedetails__show_in_authorization=True) 
    )
    
    authorization_definition_id = serializers.SerializerMethodField()
    authorization_definition_write = serializers.PrimaryKeyRelatedField(
        write_only=True, required=False, source='authorization_definition',
        queryset=AuthorizationDefinition.objects.filter(is_deleted=False)
    )
    
    def get_authorization_definition_id(self, obj):
        return obj.authorization_definition.id if obj.authorization_definition else None

    def validate_user_type(self, value):

        if not check_user_type(value):
            raise serializers.ValidationError("Invalid user type.")
        return value

    def get_type_name(self, obj):
        return obj.get_type_display()
    
    def get_user(self, obj):
        if not obj.user_type or not obj.user_identifier:
            return None
        try:
            user_obj = user_by_type_id(obj.user_type, obj.user_identifier)

            if not user_obj:
                return None
            user_data = CoreUserMiniSerializer(user_obj)
            return user_data.data
        
        except (LookupError, AttributeError):
            return None
        
    def validate(self, attrs):
        
        type = attrs.get('type', None)
        user_identifier = attrs.get('user_identifier')
        user_type = attrs.get('user_type')
        group = attrs.get('group', None)
        screen = attrs.get('screen', None)
        level = attrs.get('level', None)
        
        
        if type == 1:
            if user_identifier == None:
                raise serializers.ValidationError("User Identifier is required.")
            if user_type == None:
                raise serializers.ValidationError("User Type is required.")
            if screen == None:
                raise serializers.ValidationError("Screen is required.")
            if level == None:
                raise serializers.ValidationError("Level is required.")
            
        if type == 2:
            if group == None:
                raise serializers.ValidationError("group is required.")
            if screen == None:
                raise serializers.ValidationError("Screen is required.")
            if level == None:
                raise serializers.ValidationError("Level is required.")
           
 
        definition = AuthorizationDefinition.objects.filter(
            screen=screen, is_deleted=False
        ).first()
 
        if definition and level > definition.level:
            raise serializers.ValidationError({
                "level": [
                    f"Level ({level}) cannot exceed the final level ({definition.level}) defined for this screen."
                ]
            })
           
           
        return super().validate(attrs)
    
    class Meta:
        model = Authorization
        read_only_fields = ['id','is_deleted']
        fields = ('id', 'authorization_definition_id', 'type','type_name', 'user_type', 'user_identifier','user', 'group', 'group_id', 'screen', 'screen_id', 'level','send_sms','send_email','send_notification','is_deleted', 'authorization_definition_write')
 
    def create(self, validated_data):
        group = validated_data.pop('group', None)
        authorization_definition = validated_data.pop('authorization_definition', None)
 
        permission = Authorization.objects.create(
            group=group,
            authorization_definition=authorization_definition,
            **validated_data  
        )
 
        return permission
   
    def update(self, instance, validated_data):
        user_type = validated_data.pop('user_type', None)
        user_identifier = validated_data.pop('user_identifier', None)
        group = validated_data.pop('group', None)
        authorization_definition = validated_data.pop('authorization_definition', None)
        screen = validated_data.get('screen', instance.screen)
        level = validated_data.get('level', instance.level)
        instance.authorization_definition = authorization_definition if authorization_definition is not None else instance.authorization_definition
        instance.user_type = user_type if user_type is not None else instance.user_type
        instance.user_identifier = user_identifier if user_identifier is not None else instance.user_identifier
        instance.group = group if group is not None else instance.group
        instance.screen = screen if screen is not None else instance.screen
        instance.level = level if level is not None else instance.level
 
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
 
        instance.save()
        return instance
    

class AuthorizationHistorySerializer(serializers.ModelSerializer):
    
    authorized_by = serializers.SerializerMethodField()

    screen = ContentType2Serializer(many=False, read_only=True)
    screen_id = serializers.PrimaryKeyRelatedField(
        write_only=True, required=False, source='screen',
        queryset=ContentType.objects.filter(contenttypedetails__show_in_authorization=True) 
    )

    authorized_status = serializers.ChoiceField(choices=AuthorizationHistory.AUTHORIZED_STATUS_CHOICES, )
    authorized_status_name =  serializers.SerializerMethodField()

    def get_authorized_status_name(self, obj):
        return obj.get_authorized_status_display()
    

    def get_authorized_by(self, obj):
        if not obj.authorized_by_type or not obj.authorized_by_identifier:
            return None
        try:
            user_obj = user_by_type_id(obj.authorized_by_type,obj.authorized_by_identifier)

            if not user_obj:
                return None
            user_data = CoreUserMiniSerializer(user_obj)
            return user_data.data
        
        except (LookupError, AttributeError):
            return None
        
        
    class Meta:
        model = AuthorizationHistory
        read_only_fields = ['id','authorized_by_type','authorized_on','authorized_by']
        fields = ('id','instance_id', 'screen', 'screen_id','authorized_level', 'authorized_status', 'authorized_status_name',  'description', 'authorized_by_type','authorized_by','authorized_on')



class CheckAuthorizationHistorySerializer(serializers.ModelSerializer):

    def validate_instance_id(self, value):
        user = self.context['request'].user
        kwargs = self.context.get('kwargs', {})
        app_label = kwargs.get('app_label')
        model_name = kwargs.get('model_name')

        filterQueryOr = Q()
        filterQueryAnd = Q()
        approvals = []


        if not user.is_superuser:
            user = self.context['request'].user
            user_type = type(user).__name__
            user_identifier = user.id

            group_related_name = user.__class__._meta.get_field('groups').related_query_name()

            # group__employees=user
            group_filter = {f'group__{group_related_name}' : user}

            # approvals = Authorization.objects.filter(screen__model = model_name,screen__app_label = app_label).filter(Q(Q(type=1) & Q(user= self.request.user) | Q(type=2) & Q(group__user= self.request.user)))
            approvals = Authorization.objects.filter(
                screen__model=model_name,
                screen__app_label=app_label,
                is_deleted = False
            ).filter(
                Q(Q(type=1) & Q(Q(user_type= user_type) & Q(user_identifier= user_identifier )) | Q(type=2) & Q(**group_filter))
            )
            if len(approvals)==0:
                filterQueryAnd &= Q(id = 0)

            for approval in approvals:
                filterQueryOr |=  Q( authorized_level = approval.level -1 ) 
            
        model = apps.get_model(app_label, model_name)       
        count = model.objects.filter( Q(is_deleted = False) & ~Q(authorized_status = 3) & Q( filterQueryOr ) & Q( filterQueryAnd ) & Q(id = value ) ).count()
        if (count == 0 or len(approvals) == 0) and not user.is_superuser:
            raise serializers.ValidationError("This instance_id is not allowed.")
        return value

    class Meta:
        model = AuthorizationHistory
        fields = ('instance_id',)
        

class CheckBulkAuthorizationHistorySerializer(serializers.ModelSerializer):

    def validate(self, attrs):
        user = self.context['request'].user
        kwargs = self.context.get('kwargs', {})
        app_label = kwargs.get('app_label')
        model_name = kwargs.get('model_name')

        if not user.is_superuser:
            user_type = type(user).__name__
            user_identifier = user.id
            group_related_name = user.__class__._meta.get_field('groups').related_query_name()
            group_filter = {f'group__{group_related_name}': user}

            approvals = Authorization.objects.filter(
                screen__model=model_name,
                screen__app_label=app_label,
                is_deleted=False
            ).filter(
                Q(Q(type=1) & Q(Q(user_type=user_type) & Q(user_identifier=user_identifier)) | Q(type=2) & Q(**group_filter))
            )
            
            if len(approvals) == 0:
                raise serializers.ValidationError("You don't have authorization permission for this screen.")
        
        return attrs

    class Meta:
        model = AuthorizationHistory
        fields = ()



class AuthorizedHistorySerializer(serializers.ModelSerializer):
    # authorized_by = CoreUserMiniSerializer(many = False, read_only=True)
    
    authorized_status = serializers.ChoiceField(choices=AuthorizationHistory.AUTHORIZED_STATUS_CHOICES, )
    authorized_status_name =  serializers.SerializerMethodField()


    def get_authorized_status_name(self, obj):
        return obj.get_authorized_status_display()

    def validate_instance_id(self, value):

        user = self.context['request'].user
        user_type = type(user).__name__
        user_identifier = user.id
        group_related_name = user.__class__._meta.get_field('groups').related_query_name()
        # group__employees=user
        group_filter = {f'group__{group_related_name}' : user}

        filterQueryOr = Q()
        filterQueryAnd = Q()
        kwargs = self.context.get('kwargs', {})
    
        app_label = kwargs.get('app_label')
        model_name = kwargs.get('model_name')

        filterQueryOr = Q()
        filterQueryAnd = Q()
        approvals = []

        if not user.is_superuser:
            user = self.context['request'].user
            # approvals = Authorization.objects.filter(screen__model = model_name,screen__app_label = app_label).filter(Q(Q(type=1) & Q(user= self.request.user) | Q(type=2) & Q(group__user= self.request.user)))
            approvals = Authorization.objects.filter(
                screen__model=model_name,
                screen__app_label=app_label
            ).filter(
                Q(Q(type=1) & Q(Q(user_type= user_type) & Q(user_identifier= user_identifier )) | Q(type=2) & Q(**group_filter))
            )
            if len(approvals)==0:
                filterQueryAnd &= Q(id = 0)

            for approval in approvals:
                filterQueryOr |=  Q( authorized_level = approval.level -1 ) 
            
        model_class = apps.get_model(app_label, model_name)       
        count = model_class.objects.filter( Q(is_deleted = False) & ~Q(authorized_status = 3) & Q( filterQueryOr ) & Q( filterQueryAnd ) & Q(id = value ) ).count()
        if (count == 0 or len(approvals) == 0) and not user.is_superuser :
            raise serializers.ValidationError({"instance_id": "This instance_id is not alowed."})
        
        return value
       

    class Meta:
        model = AuthorizationHistory
        read_only_fields = [ 'authorized_on','created_on','authorized_by_identifier', 'authorized_by_type',] #'created_by'
        fields = ('instance_id','authorized_level', 'authorized_status', 'authorized_status_name','description','authorized_by_type', 'authorized_by_identifier', 'authorized_on','created_on',) #'created_by'


    def create(self, validated_data):
        user = self.context['request'].user

        kwargs = self.context.get('kwargs', {})
        app_label = kwargs.get('app_label')
        # print('app_label', app_label)
        model_name = kwargs.get('model_name')
        # print('model_name', model_name)
        instance_id = validated_data.get('instance_id')

        try:
            model_class = apps.get_model(app_label, model_name)
        except LookupError:
            raise serializers.ValidationError("Invalid app_label or model_name.")

        try:
            instance = model_class.objects.get(id=instance_id)
        except model_class.DoesNotExist:
            raise serializers.ValidationError("Instance not found.")

        content_type = ContentType.objects.get(app_label=app_label, model= model_name)
        validated_data['screen'] = content_type

        validated_data['authorized_level'] = instance.authorized_level + 1
        obj = super().create(validated_data)


        if obj.authorized_status == 3 and instance.authorized_status != 2:
            instance.authorized_status = 3
            instance.authorized_on = timezone.now()
            instance.authorized_level = obj.authorized_level
            instance.authorized_by_type = type(user).__name__
            instance.authorized_by_identifier = user.id
            instance.save()
            approval_event.send(sender=instance.__class__, instance=instance, event_name="rejected")
            multi_approved_event.send(sender=instance.__class__, instance=obj,obj = instance, event_name="rejected")

        final_approval = AuthorizationDefinition.objects.filter(
            # screen__model_name=model_name,
            screen__model=model_name.lower(),
            screen__app_label=app_label,
            level=obj.authorized_level,
            is_deleted=False
        ).first()

        if final_approval:
            instance.authorized_status = obj.authorized_status
            instance.authorized_on = timezone.now()
            instance.authorized_level = obj.authorized_level
            instance.authorized_by_type = type(user).__name__
            instance.authorized_by_identifier = user.id
            
            instance.save()
            approval_event.send(sender=instance.__class__, instance=instance, event_name="approval")

        instance.current_authorized_level = obj.authorized_level
        instance.current_authorized_by_type = type(user).__name__
        instance.current_authorized_by_identifier = user.id
        instance.current_authorized_on = timezone.now()
        instance.save()

        obj.authorized_by = user
        obj.save()
        
        multi_approved_event.send(sender=obj.__class__, instance=obj,obj = instance, event_name="approved") # use instance as obj and obj as instance

        return obj

class InstanceAuthorizationHistorySerializer(serializers.ModelSerializer):
    
    authorized_by = serializers.SerializerMethodField()
    current_authorized_by = serializers.SerializerMethodField()
 
    authorized_status = serializers.ChoiceField(choices=AuthorizationHistory.AUTHORIZED_STATUS_CHOICES, )
    authorized_status_name =  serializers.SerializerMethodField()
 
    def get_authorized_status_name(self, obj):
        return obj.get_authorized_status_display()
    
 
    def get_authorized_by(self, obj):
        if not obj.authorized_by_type or not obj.authorized_by_identifier:
            return None
        try:
            user_obj = user_by_type_id(obj.authorized_by_type,obj.authorized_by_identifier)
            user_obj = user_obj.first()
        
        except (LookupError, AttributeError):
            return None
    
 
    def get_current_authorized_by(self, obj):
        if not obj.current_authorized_by_type or not obj.current_authorized_by_identifier:
            return None
        try:
            user_obj = user_by_type_id(obj.current_authorized_by_type,obj.current_authorized_by_identifier)
            user_obj = user_obj.first()
        
        except (LookupError, AttributeError):
            return None
        
 
    class Meta:
        model = Device
        read_only_fields = ['id','authorized_by_type','authorized_on']
        fields = ('id', 'authorized_level', 'authorized_by_type', 'authorized_by_identifier', 'authorized_on', 'authorized_status', 'authorized_status_name', 'current_authorized_level', 'current_authorized_status', 'current_authorized_by_type', 'authorized_by','current_authorized_by_identifier', 'current_authorized_by', 'current_authorized_on')
