import string
from django.contrib.auth.models import Group
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password as django_validate_password
from django.utils.crypto import get_random_string
from rest_framework import serializers, status
from Core.Users.models import DEVICE_ACCESS_CHOICES, GENDER_CHOICES, Groupdetails
from Core.Users.serializers import GroupMiniSerializer
from Masters.validators import validate_contact_phone, validate_contact_email


class CompanyMiniSerializer(serializers.ModelSerializer):
    class Meta:
        from Masters.models import Company
        model = Company
        fields = ['id', 'code', 'name']


class LocationMiniSerializer(serializers.ModelSerializer):
    class Meta:
        from Masters.models import Location
        model = Location
        fields = ['id', 'code', 'name']
from Core.System.models import TemporaryVerification

User = get_user_model()


class UserMini3Serializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()

    def get_fullname(self, user):

        return  '{} {}'.format(user.first_name, user.last_name )
    
    class Meta:
        model = User
        fields = ('id','fullname', 'first_name',)

          
      
class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False, allow_blank=True)  # Allow blank for username
    fullname = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, max_length=30, required=False)
    is_email_verified = serializers.CharField(read_only=True)
    is_phone_verified = serializers.CharField(read_only=True)
    # location = LocationMiniSerializer(many=True, read_only=True)
    # location_ids = serializers.ListField(write_only=True, child=serializers.PrimaryKeyRelatedField(write_only=True, queryset=Location.objects.filter(is_deleted=False)), required=False)

    gender = serializers.ChoiceField(choices=GENDER_CHOICES, required=False, allow_null=True)
    gender_name = serializers.SerializerMethodField()

    device_access = serializers.ChoiceField(choices=DEVICE_ACCESS_CHOICES)
    device_access_name = serializers.SerializerMethodField()

    groups = GroupMiniSerializer(many=True, read_only=True)
    group_ids = serializers.ListField(
        write_only=True, 
        child=serializers.IntegerField(), 
        required=True,
        allow_empty=False,
        error_messages={
            'required': 'At least one group must be selected',
            'empty': 'At least one group must be selected'
        }
    )
    

    
    profilepicture = serializers.ImageField(required=False, allow_null=True)
    remove_profilepicture = serializers.BooleanField(required=False, write_only=True, default=False)

    designation = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    joining_date = serializers.DateField(required=False, allow_null=True)
    reporting_manager = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )
    reporting_manager_name = serializers.SerializerMethodField()
    user_status = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    must_reset_password = serializers.BooleanField(required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    
    def get_gender_name(self, obj):
        return obj.get_gender_display()
    

    def get_device_access_name(self, obj):
        return obj.get_device_access_display()
    
    def get_fullname(self, user):
        return '{} {}'.format(user.first_name, user.last_name)
    
    def get_reporting_manager_name(self, obj):
        if obj.reporting_manager:
            return '{} {}'.format(obj.reporting_manager.first_name, obj.reporting_manager.last_name).strip() or obj.reporting_manager.username
        return None

    team_count = serializers.SerializerMethodField()
    def get_team_count(self, obj):
        return obj.team_members.count()

    def validate_username(self, value):
        if value and not value.isalnum():
            raise serializers.ValidationError('The username should only contain alphanumeric characters')
        
        # If value is provided (which can be blank), validate uniqueness
        if value:
            q = User.objects.all()
            if self.instance:
                q = q.exclude(pk=self.instance.pk)
            if q.filter(username=value, is_active=True).exists():
                raise serializers.ValidationError("This username is already in use.")
        
        return value

    def validate_email(self, value):
        try:
            return validate_contact_email(value)
        except Exception as exc:
            raise serializers.ValidationError(str(exc))

    def validate_phone(self, value):
        try:
            return validate_contact_phone(value)
        except Exception as exc:
            raise serializers.ValidationError(str(exc))

    def validate_alternate_phone(self, value):
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
    
    def generate_username(self):
        last_user = User.objects.filter(username__startswith='EMP').order_by('-username').first()
        
        if last_user:
            last_number = int(last_user.username.replace('EMP', ''))
            new_number = last_number + 1
        else:
            new_number = 1
        return 'EMP{:04d}'.format(new_number)

    class Meta:
        model = User
        read_only_fields = ['otp', 'username']
        fields = ['id', 'username', 'fullname', 'email', 'phone', 'groups', 'group_ids', 'password', 'first_name', 'last_name', 'otp', 'gender', 'gender_name', 'is_email_verified', 'is_phone_verified','receive_sms','receive_email','receive_notification', 'is_active', 'device_access', 'device_access_name', 'profilepicture', 'remove_profilepicture', 'designation', 'joining_date', 'reporting_manager', 'reporting_manager_name', 'team_count', 'user_status', 'must_reset_password', 'leads_assigned', 'site_visits', 'bookings', 'registrations']


    def create(self, validated_data):
        group_ids = validated_data.pop('group_ids', [])

        # Generate username if not provided or blank
        if not validated_data.get('username'):
            validated_data['username'] = self.generate_username()

        # Pop custom fields that are not model fields
        password = validated_data.pop('password', None)
        validated_data.pop('remove_profilepicture', None)
        
        user = super().create(validated_data)

        # If no password provided, set username as the password
        if password:
            user.set_password(password)
        else:
            user.set_password(user.username)
        
        user.save()

        if group_ids:
            user.groups.set(group_ids)

        return user

    def update(self, instance, validated_data):
        if 'email' in validated_data:
            validated_data['is_email_verified'] = False
        if 'phone' in validated_data:
            validated_data['is_phone_verified'] = False

        if 'group_ids' in validated_data:
            group_ids = validated_data.pop('group_ids')
            instance.groups.set(group_ids)

        # Handle profile picture removal
        if validated_data.pop('remove_profilepicture', False):
            instance.profilepicture = None
            instance.save(update_fields=['profilepicture'])
        validated_data.pop('profilepicture', None) if 'profilepicture' not in validated_data else None

        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()

        return user

class RegisterSerializer(serializers.ModelSerializer):

    username = serializers.CharField( allow_blank=False )
    fullname = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, max_length=30)
    is_email_verified = serializers.CharField(read_only=True)
    is_phone_verified = serializers.CharField(read_only=True)
    gender = serializers.ChoiceField(choices=GENDER_CHOICES, )
    gender_name = serializers.SerializerMethodField()
    
    gender = serializers.ChoiceField(choices=GENDER_CHOICES, )
    email = serializers.CharField(required= True,)
    phone = serializers.CharField(required= True,)
    phoneotp = serializers.CharField(required= False, allow_blank=True, allow_null=True)
    emailotp = serializers.CharField(required= False, allow_blank=True, allow_null=True)
    
    def get_gender_name(self, obj):
        return obj.get_gender_display()  

  
    def get_fullname(self, user):

        return  '{} {}'.format(user.first_name, user.last_name )



    def validate_email(self, value):
        try:
            value = validate_contact_email(value)
        except Exception as exc:
            raise serializers.ValidationError(str(exc))

        q = User.objects.all()
        if self.instance:
            object_id = self.instance.id
            q = q.exclude(pk=object_id)
        if q.filter(email=value).exists():
            raise serializers.ValidationError({"email": "This email is already in use."})
        return value

    def validate_phone(self, value):
        try:
            return validate_contact_phone(value)
        except Exception as exc:
            raise serializers.ValidationError(str(exc))


    def validate_username(self, value):
    
        if not value.isalnum():
            raise serializers.ValidationError({ 'username': 'The username should only contain alphanumeric characters'})

        q = User.objects.all()
        if self.instance:
            object_id = self.instance.id
            q = q.exclude(pk=object_id)
        if q.filter(username=value,is_active=True).exists():
            raise serializers.ValidationError({"username": "This username is already in use."})
        return value


    # def get_group(self, group):
        
    #     group, grc = Group.objects.get_or_create(name='customers', defaults={'name': 'customers'})
    #     if group is not None:
    #         self.groups.add(group)
    #         self.save()
        

    def validate(self, attrs):

        phone =  attrs.get('phone', '')
        email =  attrs.get('email', '')
        phoneotp =  attrs.pop('phoneotp', '')
        emailotp =  attrs.pop('emailotp', '')

        if not (phoneotp or emailotp):
            raise serializers.ValidationError({'message': 'OTP is mandatory'})

        if phoneotp:
            tempver_obj = TemporaryVerification.objects.filter(mobile=phone, otp=phoneotp, is_phone_verified=True, type=1).last()
            if not tempver_obj:
                raise serializers.ValidationError({'message': 'Phone verification failed'}, code=status.HTTP_400_BAD_REQUEST)

        if emailotp:
            tempver_obj = TemporaryVerification.objects.filter(email=email, otp=emailotp, is_email_verified=True, type=2).last()
            if not tempver_obj:
                raise serializers.ValidationError({'message': 'Email verification failed'}, code=status.HTTP_400_BAD_REQUEST)
       
        return super().validate(attrs) 

    class Meta:
        model = User
        read_only_fields = ['otp']
        fields = ['username', 'fullname', 'email', 'phone', 'emailotp', 'phoneotp','password', 'first_name', 'last_name','otp', 'gender', 'is_email_verified', 'is_phone_verified', 'is_active','gender_name',]


    def create(self, validated_data):
        
        group, grc = Group.objects.get_or_create(name='users', defaults={'name': 'users'})
        if grc is True:
            groupdetails = Groupdetails.objects.create(group_id=group.id)
        else:
            pass

        #data, is_created = User.objects.update_or_create( phone= phone, defaults= validated_data)
        validated_data['otp'] =  get_random_string(4, allowed_chars= string.digits)
        object = User.objects.create_user(**validated_data)
        # token = RefreshToken.for_user(object).access_token
        
        object.groups.add(group)
        
        current_site = get_current_site(self.context['request']).domain
        # relativeLink = reverse('email-verify')
        # absurl = 'http://'+current_site+relativeLink+"?token="+str(token)
        # email_body = 'Hi '+object.username + \
            # ' Use the OTP below to verify your email \n' + validated_data['otp']
        # edata = {'email_body': email_body, 'to_email': object.email,
        #         'email_subject': 'Verify your email'}
        email = validated_data.pop('email', None)
        # ewords ={'username':object.username , 'otp':validated_data['otp']}
        # edata = {'to_email':email,'email_body':  Email.email_body.format(**ewords),'email_subject': 'Verify your email' }

        # Util.send_email(edata)

  
        
        phone = validated_data.pop('phone', None)
        # swords = {'to_phone':phone,'otp':validated_data['otp']  }
        # sdata = {'to_phone':phone,'message':  SMS.loginotp.format(**swords) }
        
        # Util.send_sms(sdata)    
        
        return object 


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


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
        fields = ['id', 'user', 'screen', 'screen_name', 'screen_code', 'can_view', 'can_add', 'can_edit', 'can_delete', 'can_export', 'is_view_only', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class UserPermissionBulkSerializer(serializers.Serializer):
    """Bulk update permissions for a user"""
    permissions = UserPermissionSerializer(many=True)


class UserWithPermissionsSerializer(serializers.ModelSerializer):
    """User serializer with permissions included"""
    permissions = UserPermissionSerializer(many=True, read_only=True)
    reporting_manager_name = serializers.SerializerMethodField()
    reporting_manager_fullname = serializers.SerializerMethodField()
    team_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'phone', 'designation', 'joining_date', 'reporting_manager', 'reporting_manager_name', 'reporting_manager_fullname', 'user_status', 'lead_data_scope', 'followup_data_scope', 'sitevisit_data_scope', 'booking_data_scope', 'must_reset_password', 'is_active', 'leads_assigned', 'site_visits', 'bookings', 'registrations', 'permissions', 'team_count', 'created_at']
    
    def get_reporting_manager_name(self, obj):
        return obj.reporting_manager.username if obj.reporting_manager else None
    
    def get_reporting_manager_fullname(self, obj):
        if obj.reporting_manager:
            return '{} {}'.format(obj.reporting_manager.first_name, obj.reporting_manager.last_name).strip() or obj.reporting_manager.username
        return None
    
    def get_team_count(self, obj):
        return obj.team_members.count()


class PermissionTemplateSerializer(serializers.ModelSerializer):
    screens = serializers.SerializerMethodField()
    
    class Meta:
        model = PermissionTemplate
        fields = ['id', 'name', 'description', 'screens', 'is_active', 'created_at']
    
    def get_screens(self, obj):
        details = obj.permissiontemplatedetail_set.all()
        return [{'screen_id': d.screen_id, 'screen_name': d.screen.name, 'can_view': d.can_view, 'can_add': d.can_add, 'can_edit': d.can_edit, 'can_delete': d.can_delete, 'can_export': d.can_export} for d in details]


class PermissionAuditLogSerializer(serializers.ModelSerializer):
    changed_by_username = serializers.CharField(source='changed_by.username', read_only=True)
    target_user_username = serializers.CharField(source='target_user.username', read_only=True)
    
    class Meta:
        model = PermissionAuditLog
        fields = ['id', 'changed_by', 'changed_by_username', 'target_user', 'target_user_username', 'action', 'field_changed', 'old_value', 'new_value', 'timestamp', 'ip_address'] 



