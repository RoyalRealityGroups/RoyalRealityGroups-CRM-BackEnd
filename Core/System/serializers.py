
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from yaml import serialize

from Core.Core.utils.utils import get_model_path
from Core.Core.lexer.LexerBySly import formula_validator
from Core.Core.serializers.SerializerFields import UserRelatedField
from Core.Core.storage.storage_backends import DBBackupMediaStorage
from Core.Users.serializers import AllContentTypeSerializer, CoreUserMiniSerializer, PermissionJoinSerializer
from Core.System.services import send_alert_email, send_alert_sms, send_push_notification
User = get_user_model()
from django.utils import timezone
from django.db.models import Q

import string
from rest_framework.response import Response
from rest_framework.exceptions import NotAcceptable
from django.utils.crypto import get_random_string

from rest_framework import serializers
from Users.models import User
from django.contrib.auth.models import Group

from Users.serializers import  GroupMiniSerializer
from .models import AlertConfigUsers, Menu, RecentActivity, Submenu, Menuitem, Notification, NotificationUsers, Backup, Restore, Attachment,Formula, FormulaUpdate, ActivityLog, FormulaVariables, TaskScheduler, TemporaryVerification, ACTION_TYPES_CHOICES, SEEN_CHOICES, Error, Download, AlertConfig, Announcements, Template


media_storage = DBBackupMediaStorage()


from rest_framework import status


class FilteredListSerializer(serializers.ListSerializer):
 
    def to_representation(self, data):
        data = data.filter(is_deleted=False)
        return super(FilteredListSerializer, self).to_representation(data)
    
        
class SubmenuSerializer(serializers.ModelSerializer):

    class Meta:
        model = Submenu
        fields = ('id', 'code', 'name', 'sequence', 'icon', 'click', 'submenu' )

class MenuSerializer(serializers.ModelSerializer):

    class Meta:
        model = Menu
        # fields = ('id', 'code', 'name', 'submenus', 'menuitems')
        fields = '__all__'

class MenuitemSerializer(serializers.ModelSerializer):
    permission = PermissionJoinSerializer(many=False,  read_only=True)
    menu = MenuSerializer(many=False,  read_only=True)
    submenu = SubmenuSerializer(many=False,  read_only=True)
    menu_id = serializers.PrimaryKeyRelatedField(write_only=True, source='menu', queryset=Menu.objects.all())
    submenu_id = serializers.PrimaryKeyRelatedField(write_only=True, source='submenu',  queryset=Submenu.objects.all(), required=False,)


    class Meta:
        model = Menuitem
        fields = '__all__'
        
class MenuitemSerializer2(serializers.ModelSerializer):
    # permission = PermissionJoinSerializer(many=False,  read_only=True)
    menu = MenuSerializer(many=False,  read_only=True)
    submenu = SubmenuSerializer(many=False,  read_only=True)


    class Meta:
        model = Menuitem
        fields = '__all__'
        
class UserMenuitemSerializer(serializers.ModelSerializer):
    path = serializers.CharField(source='link', read_only=True)  # Map 'link' to 'path' for frontend
    permissions = serializers.SerializerMethodField()
    
    def get_permissions(self, obj):
        if obj.permission:
            return [f"{obj.permission.content_type.app_label}.{obj.permission.codename}"]
        return []
    
    class Meta:
        model = Menuitem
        fields = ('id', 'code', 'name', 'icon', 'path', 'link', 'sequence', 'click', 'description', 'permissions')

class RecursiveField(serializers.ModelSerializer): 
    def to_representation(self, value):
        serializer_data = UserSubmenuSerializer(value, context=self.context).data
        return serializer_data
    class Meta:
            model = Submenu
            fields = '__all__'


class UserSubmenuSerializer(serializers.ModelSerializer):
    menuitems = serializers.SerializerMethodField('get_menuitems')
    submenus = serializers.SerializerMethodField()


    def get_menuitems(self, submenu):
        queryset = Menuitem.objects.filter(submenu=submenu, is_deleted=False)
        serializer = UserMenuitemSerializer(instance=queryset.order_by('sequence'), many=True, context=self.context)
        return serializer.data
    
    def get_submenus(self, obj):
        visited_submenu_ids = set(self.context.get('visited_submenu_ids', set()))
        if obj.id in visited_submenu_ids:
            return []

        visited_submenu_ids.add(obj.id)
        queryset = Submenu.objects.filter(submenu=obj.id).exclude(id__in=visited_submenu_ids).order_by('sequence')
        child_context = dict(self.context)
        child_context['visited_submenu_ids'] = visited_submenu_ids
        return RecursiveField(queryset, many=True, read_only=True, context=child_context).data
        
    class Meta:
        model = Submenu
        fields = ('id', 'code', 'name', 'menuitems', 'sequence', 'icon', 'click', 'submenus')

class UserMenuSerializer(serializers.ModelSerializer):
    submenus = serializers.PrimaryKeyRelatedField(many=True,  read_only=True)
    submenus = UserSubmenuSerializer(many=True,  read_only=True)
    menuitems = serializers.SerializerMethodField('get_menuitems')

    def get_menuitems(self, menu):
        user = self.context['request'].user
        queryset = Menuitem.objects.filter(submenu__isnull=True, menu=menu, is_deleted=False)
        
        # Show all menuitems for non-superusers (fallback when no permissions)
        if not user.is_superuser:
            user_permissions = user.get_all_permissions()
            if not user_permissions:
                # User has no permissions - show all menuitems
                pass
            else:
                # Filter by permissions
                filtered_items = []
                for item in queryset:
                    if item.permission is None:
                        filtered_items.append(item.id)
                    else:
                        perm_str = f"{item.permission.content_type.app_label}.{item.permission.codename}"
                        if perm_str in user_permissions:
                            filtered_items.append(item.id)
                queryset = Menuitem.objects.filter(id__in=filtered_items)
            
        serializer = UserMenuitemSerializer(instance=queryset.order_by('sequence'), many=True)
        return serializer.data

    class Meta:
        model = Menu
        fields = '__all__'



class NotificationSerializer(serializers.ModelSerializer):
    created_on=serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S",input_formats=['%Y-%m-%d',], required = False)
    class Meta:
        model = Notification
        readonly = ['subject', 'body', 'type', 'ref', 'message_priority', 'notification_type', 'created_on']
        fields = ('id', 'subject', 'body', 'type', 'ref', 'message_priority', 'notification_type', 'created_on')

    def create(self, validated_data): 
        obj = super().create(validated_data)

        return obj
    

class NotificationUsersSerializer(serializers.ModelSerializer):
    # user = CoreUserMiniSerializer(many = False,  read_only=True)
    # user_id = serializers.PrimaryKeyRelatedField(write_only=True, source='user', queryset= User.objects.filter(is_active=True,))
    notification = NotificationSerializer(many=False, read_only=True)
    notification_id = serializers.PrimaryKeyRelatedField(write_only=True, source='notification', required=False, queryset=Notification.objects.filter(is_deleted=False,))
    seen = serializers.ChoiceField(choices=SEEN_CHOICES, )
    seen_name =  serializers.SerializerMethodField()

    def get_seen_name(self, obj):
        return obj.get_seen_display()

    class Meta:
        model = NotificationUsers
        fields = ( 'user_identifier', 'user_type', 'notification', 'notification_id', 'seen', 'seen_name', 'seen_time',)


    def create(self, validated_data):
        # user = self.context['request'].user
        # validated_data['user'] = user
        notification = validated_data.get('notification',None)

        obj = super().create(validated_data)

        return obj



class BackupSerializer(serializers.ModelSerializer):
    created_by_user = CoreUserMiniSerializer(many=False, read_only=True)
    created_by = UserRelatedField(user_field= 'created_by', read_only=True)



    class Meta:
        model = Backup
        read_only_fields = ['code', 'created_on', 'created_by_user']
        fields = ('id', 'code', 'name', 'created_on', 'created_by', 'created_by_user')

class RestoreSerializer(serializers.ModelSerializer):
    created_by_user = CoreUserMiniSerializer(many=False, read_only=True)
    file_url = serializers.SerializerMethodField()
    created_by = UserRelatedField(user_field= 'created_by', read_only=True)



    def get_file_url(self, obj):
        try:
            return media_storage.url(obj.name)
        except:
            return obj.name

    class Meta:
        model = Restore
        read_only_fields = ['code', 'created_on', 'created_by_user']
        fields = ('id', 'code', 'name', 'file_url', 'created_on', 'created_by', 'created_by_user')


class DownloadSerializer(serializers.ModelSerializer):
    created_by_user = CoreUserMiniSerializer(many=False, read_only=True)
    file_url = serializers.SerializerMethodField()
    created_by = UserRelatedField(user_field= 'created_by', read_only=True)



    def get_file_url(self, obj):
        try:
            return media_storage.url(obj.name)
        except:
            return obj.name

    class Meta:
        model = Download
        read_only_fields = ['code', 'created_on', 'created_by_user']
        fields = ('id', 'code', 'name', 'file_url', 'created_on', 'created_by', 'created_by_user')

        
class ResetDatabaseSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=100, required=True, allow_blank=False, write_only=True, )
    contenttype_ids = serializers.ListField(write_only=True, child=serializers.PrimaryKeyRelatedField(write_only=True, queryset=ContentType.objects.all()), required=False)

    
    def validate(self, attrs):
        password = attrs.get('password', '')
        user = self.context['request'].user

        if password != '':
            
            if not user.is_superuser:
                raise serializers.ValidationError("You are not allowed to reset the database")

            if not user.check_password(password):
                raise serializers.ValidationError({"password": "Password check failed, try again."})

        return super().validate(attrs)


    class Meta:
        read_only_fields = []
        fields = ( 'password', 'contenttype_ids', )

class BackupValidationserializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=100, required=True, allow_blank=False, write_only=True, )
    file_url = serializers.SerializerMethodField()


    def get_file_url(self, obj):
        try:
            return media_storage.url(obj.name)
        except:
            return obj.name

    
    def validate(self, attrs):
        password = attrs.get('password', '')
        user = self.context['request'].user

        if password != '':
            
            if not user.check_password(password):
                raise serializers.ValidationError({"password": "Password check failed, try again."})

        return super().validate(attrs)
    


    class Meta:
        model= Backup
        read_only_fields = []
        fields = ( 'password', 'file_url' )

    

        
class AttachmentSerializer(serializers.ModelSerializer):
    created_by_user = CoreUserMiniSerializer(many=False, read_only=True)
    file_thumbnail_url = serializers.SerializerMethodField()
    created_by = UserRelatedField(user_field= 'created_by', read_only=True)

    
    def get_file_thumbnail_url(self, obj):
        
        try:
            url = obj.file_thumbnail.url
        except Exception as e:
            # print('=====================================================',e,)
            url = "static/images/thumbnail/default_no_file.png"

        res =self.context['request'].build_absolute_uri(url)
        
        return res

    class Meta:
        model = Attachment
        read_only_fields = ['created_on', 'created_by_user']
        fields = ('id', 'file', 'created_on','file_thumbnail_url', 'created_by', 'created_by_user')

        
class AttachmentMiniSerializer(serializers.ModelSerializer):

    file_thumbnail = serializers.SerializerMethodField()
    
    def get_file_thumbnail(self, obj):
        
        try:
            url = obj.file_thumbnail.url
        except Exception as e:
            # print('=====================================================',e,)
            url = "static/images/thumbnail/default_no_file.png"

        res =self.context['request'].build_absolute_uri(url)
        
        return res

    class Meta:
        model = Attachment
        read_only_fields = ['created_on', 'created_by_user',]
        fields = ('id','file', 'created_on','file_thumbnail',)



class FormulaSerializer(serializers.ModelSerializer):
    variables = serializers.ListField(child = serializers.CharField(), write_only=True, required=True )
    
    def validate_formula(self, value):
        res = formula_validator( value, )
        if res['error']:
            raise serializers.ValidationError(res)
        return value
        

    class Meta:
        model = Formula
        read_only_fields = ['created_on', 'created_by_user']
        fields = ('id', 'code','name','formula','variables')


    def create(self, validated_data):
        user = self.context['request'].user

        variables = validated_data.pop('variables',)

        instance = super().create(validated_data)

        FormulaUpdate.objects.create(formula=instance, formula_txt = instance.formula,  )

        for variable in variables:
            FormulaVariables.objects.create(formula=instance,   name = variable  )

 
        return instance



    def update(self, instance, validated_data):
        user = self.context['request'].user
        
        variables = validated_data.pop('variables',)
        if validated_data['formula'] != instance.formula:
            FormulaUpdate.objects.create(formula=instance, formula_txt = validated_data['formula'],)

        
        FormulaVariables.objects.filter(formula=instance).delete() 
        
        for variable in variables:
            FormulaVariables.objects.create(formula=instance,   name = variable  )

       
        formula = super().update(instance, validated_data,) 
        
        return formula




class FormulaValidationSerializer(serializers.Serializer):
    formula = serializers.CharField(required = True)

    class Meta:
        read_only_fields = []
        fields = ('formula',)


        

class FormulaValidation2Serializer(serializers.Serializer):
    code = serializers.CharField(required = True)
    variables = serializers.JSONField(required = True)

    def validate_code(self, value):
        count = Formula.objects.filter(code= value ).count()
        if count == 0:
            raise serializers.ValidationError({"code": "This code is not alowed."})
        return value

    class Meta:
        read_only_fields = []
        fields = ('code','variables')



class FormulaVariablesSerializer(serializers.ModelSerializer):
    formula = FormulaSerializer(many=False, read_only=True)
    formula_id = serializers.PrimaryKeyRelatedField(write_only=True, source='formulas', queryset=Formula.objects.filter(is_deleted=False,))
    
    def validate_new_formula(self, value):
        res = formula_validator( value, )
        if res['error']:
            raise serializers.ValidationError(res)
        return value

    class Meta:
        model = FormulaVariables
        read_only_fields = []
        fields = ('name','description','active','formula','formula_id')



class FormulaUpdateSerializer(serializers.ModelSerializer):
    formula = FormulaSerializer(many=False, read_only=True)
    formula_id = serializers.PrimaryKeyRelatedField(write_only=True, source='formulas', queryset=Formula.objects.filter(is_deleted=False,))
    
    def validate_new_formula(self, value):
        res = formula_validator( value, )
        if res['error']:
            raise serializers.ValidationError(res)
        return value

    class Meta:
        model = FormulaUpdate
        read_only_fields = ['created_on', 'created_by_user']
        fields = ( 'formula_txt','formula','formula_id')



class ActivityLogSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    type = serializers.ChoiceField(choices=ACTION_TYPES_CHOICES, )
    type_name =  serializers.SerializerMethodField()

    def get_type_name(self, obj):
        return obj.get_type_display()
 
    def get_user(self, obj):
        if obj.user_type and obj.user_identifier:
            model_path = get_model_path(obj.user_type)
            if model_path is None:
                return None

            try:
                user_model = apps.get_model(model_path)
                user = user_model.objects.filter(id=obj.user_identifier).first()
                if user:
                    return CoreUserMiniSerializer(user).data
            except Exception:
                return None
        return None

    
    class Meta:
        model = ActivityLog
        read_only_fields = [ 'created_on',]
 
        fields = ( 'id', 'user', 'type', 'type_name', 'screen_name', 'instance_code', 'created_on',  ) 


class ActivityLogMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLog
        fields = ('id', 'screen_name')


class AuditLogSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    type_name = serializers.SerializerMethodField()

    class Meta:
        model = ActivityLog
        fields = ('id','type', 'type_name', 'screen_name', 'instance_code', 'created_on', 'data', 'user')
        read_only_fields = ('id', 'created_on')

    def get_type_name(self, obj):
        return obj.get_type_display()

    def get_user(self, obj):
        if obj.user_type and obj.user_identifier:
            model_path = get_model_path(obj.user_type)
            if model_path is None:
                return None

            try:
                user_model = apps.get_model(model_path)
                user = user_model.objects.filter(id=obj.user_identifier).first()
                if user:
                    return CoreUserMiniSerializer(user).data
            except Exception:
                return None
        return None

    


class SmsSerializer(serializers.Serializer):
    to_phone = serializers.CharField( max_length=10)
    message = serializers.CharField(max_length=255)

    class Meta:
        fields = ( 'to_phone','message',)



class ErrorSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = Error
        fields = ( 'id',   'errorcode', 'requestbody','error_url'   )


class TemporaryOTPRequestSerializer(serializers.ModelSerializer):
    mobile = serializers.CharField(max_length=255, min_length=10)

    class Meta:
        model = TemporaryVerification
        fields = ['mobile',]

    
    def create(self, validated_data):
        
        otp = get_random_string(4, allowed_chars= string.digits)
        instance, is_created = TemporaryVerification.objects.update_or_create( mobile = validated_data['mobile'], defaults= { 'otp': otp, 'type':1})
        
        message = Template.objects.get(name='OTP Verification').message
        send_alert_sms([{'phone': validated_data['mobile'],'otp':otp}],message)
        
        return instance

class TemporaryVerifyOTPSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = TemporaryVerification
        fields = ['mobile', 'otp',]

    def validate(self, attrs):

        otp = attrs.get('otp', '')
        mobile = attrs.get('mobile', '')

        instance =  TemporaryVerification.objects.get(mobile = mobile)

        if instance.otp == otp:
           
            instance.is_phone_verified = True
            instance.save()

        else:
            raise NotAcceptable('Invalid OTP, try again')       

        return Response({'message':'phone number verified successfully'},status=status.HTTP_200_OK )  
    

class EmailTemporaryOTPRequestSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255, min_length=10)

    class Meta:
        model = TemporaryVerification
        fields = ['email',]

    
    def create(self, validated_data):
        
        otp = get_random_string(4, allowed_chars= string.digits)
        instance, is_created = TemporaryVerification.objects.update_or_create( email = validated_data['email'], defaults= { 'otp': otp, 'type':2})

        email_body = Template.objects.get(name='Email OTP Verification').message
        send_alert_email([{'email': validated_data['email'],'otp':otp}],email_body)

        return instance

class EmailTemporaryVerifyOTPSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = TemporaryVerification
        fields = ['email', 'otp',]

    def validate(self, attrs):

        otp = attrs.get('otp', '')
        email = attrs.get('email', '')
        now = timezone.now()

        instance =  TemporaryVerification.objects.get(email = email, type=2)
        user = User.objects.filter(email=email, is_email_verified=True).first()

        if user:
            return Response({'message':'user already verified successfully'},status=status.HTTP_200_OK )   
        else:
            if instance.otp == otp:
                instance.is_email_verified = True
                instance.save()
            else:
                raise NotAcceptable('Invalid OTP, try again')       

        return Response({'message':'phone number verified successfully'},status=status.HTTP_200_OK )   

class RecentActivitySerializer(serializers.ModelSerializer):
    # user = CoreUserMiniSerializer(many = False, read_only=True)
    user = serializers.SerializerMethodField()

    menuitem = UserMenuitemSerializer(many=False, read_only=True) # can add submenu and menu if need 
    menuitem_id = serializers.PrimaryKeyRelatedField(write_only=True, source='menuitem', queryset=Menuitem.objects.filter(is_deleted=False,))

    def get_user(self, obj):
        if obj.user_type and obj.user_identifier:
            model_path = get_model_path(obj.user_type)
            if model_path is None:
                return None

            try:
                user_model = apps.get_model(model_path)
                user = user_model.objects.filter(id=obj.user_identifier).first()
                if user:
                    return CoreUserMiniSerializer(user).data
            except Exception:
                return None
        return None

    class Meta:
        model = RecentActivity
        read_only_fields = [ 'created_on','menuitem']
        fields = ( 'id', 'user','menuitem','menuitem_id','created_on')

    def create(self, validated_data):
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context is missing.")
        user = request.user
        menuitem = validated_data.get('menuitem')
        recent_activity, created = RecentActivity.objects.update_or_create(user_identifier=user.id,user_type = type(user).__name__,menuitem=menuitem,defaults={'created_on': timezone.now()})
        return recent_activity


class TemplateSerializer(serializers.ModelSerializer):
    
    screen = AllContentTypeSerializer(many=False, read_only=True)
    screen_id = serializers.PrimaryKeyRelatedField(write_only=True, source='screen', queryset=ContentType.objects.all(), required=False)
    created_by = UserRelatedField(user_field= 'created_by', read_only=True)
    modified_by = UserRelatedField(user_field= 'modified_by', read_only=True)
    
    class Meta:
        model = Template
        read_only_fields = ['code','screen','created_on','created_by']
        fields = ('id', 'code', 'name', 'message','screen','screen_id', 'is_active', 'created_on','created_by','modified_by')
        
    def validate_message(self, value):
        """
        Validate that the message field contains valid template syntax.
        """
        if value:
            # Check for unmatched double parentheses
            open_count = value.count('((')
            close_count = value.count('))')
            
            if open_count != close_count:
                raise serializers.ValidationError(
                    "Unmatched parentheses in message template. "
                    "Each variable must be enclosed in double parentheses (())."
                )
        return value
    
    def create(self, validated_data):
        """
        Custom create method to ensure proper formatting and storage of data.
        """
        # Create the Template instance
        template = Template.objects.create(**validated_data)
        return template
    
    def update(self, instance, validated_data):
        """
        Custom update method.
        """
        # Update all fields
        instance.name = validated_data.get('name', instance.name)
        instance.message = validated_data.get('message', instance.message)
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.save()
        
        return instance
    
class TemplateMiniSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Template
        fields = ('id', 'code', 'name', 'message', 'is_active')

class AlertConfigUserSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required = False)
    dodelete = serializers.BooleanField(write_only=True, required=False)

    class Meta:
        model = AlertConfigUsers
        list_serializer_class = FilteredListSerializer
        fields = ('id','user_type','user_identifier','dodelete')

class AlertConfigSerializer(serializers.ModelSerializer):

    send_to_groups = GroupMiniSerializer(many=True, read_only=True)
    send_to_group_ids = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(), many=True, write_only=True, required=False
    )

    # send_to_users = CoreUserMiniSerializer(many=True, read_only=True)
    # send_to_user_ids = serializers.PrimaryKeyRelatedField(
    #     queryset=User.objects.filter(is_active=True, is_superuser=False),
    #     many=True, write_only=True, required=False
    # )
    alert_users = AlertConfigUserSerializer(many = True , required = False)

    event_type = serializers.ChoiceField(choices=AlertConfig.EVENT_CHOICES, required=False)
    event_type_name = serializers.SerializerMethodField()
    
    frequency = serializers.ChoiceField(choices=AlertConfig.REPEAT_CHOICES, required=False)
    frequency_name = serializers.SerializerMethodField()

    sender_type = serializers.ChoiceField(choices=AlertConfig.SENDER_TYPE_CHOICES, required=False)
    sender_type_name = serializers.SerializerMethodField()

    type = serializers.ChoiceField(choices=AlertConfig.TYPE_CHOICES, required=False)
    type_name = serializers.SerializerMethodField()
    
    message_priority = serializers.ChoiceField(choices=AlertConfig.MESSAGE_PRIORITY_CHOICES, required=False)
    message_priority_name = serializers.SerializerMethodField()
    
    notification_type = serializers.ChoiceField(choices=AlertConfig.NOTIFICATION_TYPE_CHOICES, required=False)
    notification_type_name = serializers.SerializerMethodField()
    
    template = TemplateMiniSerializer(many=False, read_only=True)
    template_id = serializers.PrimaryKeyRelatedField(write_only=True, source='template', queryset=Template.objects.filter(is_deleted=False), required=False)
    
    subject_template = TemplateMiniSerializer(many=False, read_only=True)
    subject_template_id = serializers.PrimaryKeyRelatedField(write_only=True, source='subject_template', queryset=Template.objects.filter(is_deleted=False), required=False)
    
    screen = AllContentTypeSerializer(many=False, read_only=True)
    screen_id = serializers.PrimaryKeyRelatedField(write_only=True, source='screen', queryset=ContentType.objects.all(), required=False)
    
    start_time = serializers.DateTimeField(format="%d-%m-%Y %H:%M:%S",input_formats=['%d-%m-%Y %H:%M:%S',], required = False)

    def get_event_type_name(self, obj):
        return obj.get_event_type_display()
    
    def get_sender_type_name(self, obj):
        return obj.get_sender_type_display()
    
    def get_frequency_name(self, obj):
        return obj.get_frequency_display()

    def get_type_name(self, obj):  # Fixed method name
        return obj.get_type_display()
    
    def get_message_priority_name(self, obj):  
        return obj.get_message_priority_display()
    
    def get_notification_type_name(self, obj):  
        return obj.get_notification_type_display()
    
   

    def validate(self, attrs):
        alert_users = attrs.get('alert_users',[])
        sender_type = attrs.get('sender_type')
        send_to_group_ids = attrs.get('send_to_group_ids')
        variable = attrs.get('variable')
        # send_to_users = attrs.get('send_to_users')
        value = attrs.get('value')

        if sender_type == AlertConfig.GROUP and not send_to_group_ids:
            raise serializers.ValidationError({"send_to_group_ids": "send_to_group_ids is required when sender_type is GROUP."})

        if sender_type == AlertConfig.USER and alert_users == []:
            raise serializers.ValidationError({"alert_users": "alert_users is required when sender_type is USER."})

        if sender_type == AlertConfig.VARIABLE and not variable:
            raise serializers.ValidationError({"variable": "variable is required when sender_type is VARIABLE."})

        if sender_type == AlertConfig.VALUE and not value:
            raise serializers.ValidationError({"value": "value is required when sender_type is VALUE."})

        return super().validate(attrs)

    class Meta:
        model = AlertConfig

        fields = ["id", "screen","screen_id", "event_type", "event_type_name", "sender_type", "sender_type_name", "type", "type_name","message_priority","message_priority_name","notification_type","notification_type_name","frequency","frequency_name", "gateway", "send_to_groups", "send_to_group_ids","alert_users", "value", "variable", "template","template_id", "subject_template","subject_template_id",'repeat_interval','start_time','attachment_variable','send_doc','is_scheduled', "is_active","is_attachment"]

    def create(self, validated_data):
        send_to_groups = validated_data.pop("send_to_group_ids", [])
        # send_to_users = validated_data.pop("send_to_user_ids", [])
        alert_users = validated_data.pop("alert_users",[])

        alert_config = AlertConfig.objects.create(**validated_data)
        
        if alert_config.sender_type == AlertConfig.USER:
            for alert_user in alert_users:
                dodelete = alert_user.get('dodelete', False)
                if not dodelete:
                    del alert_user['dodelete']
                    alert_user['alert']= alert_config
                    AlertConfigUsers.objects.create(**alert_user)

        alert_config.send_to_groups.set(send_to_groups)
        # alert_config.send_to_users.set(send_to_users)

        return alert_config

    def update(self, instance, validated_data):
        send_to_groups = validated_data.pop("send_to_group_ids", None)
        # send_to_users = validated_data.pop("send_to_user_ids", None)
        alert_users = validated_data.pop("alert_users",[])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        
        if instance.sender_type == AlertConfig.USER:
            for alert_user in alert_users:
                alert_user_id = alert_user.get('id',None)
                if alert_user_id:
                    alert_user_obj = AlertConfigUsers.objects.filter(id = alert_user_id)
                    dodelete = alert_user.get('dodelete', False)
                    if dodelete:
                        alert_user_obj.update(is_deleted = True)
                    else:
                        alert_user_obj.update(user_type = alert_user.get('user_type'),user_identifier = alert_user.get('user_identifier') )
                else:
                    dodelete = alert_user.get('dodelete', False)
                    if not dodelete:
                        del alert_user['dodelete']
                        alert_user['alert']= instance
                        AlertConfigUsers.objects.create(**alert_user)

        if send_to_groups is not None:
            instance.send_to_groups.set(send_to_groups)
        # if send_to_users is not None:
        #     instance.send_to_users.set(send_to_users)

        return instance
    

class AnnouncementSerializer(serializers.ModelSerializer):

    class Meta:
        model = Announcements
        read_only_fields = ['code', 'id']
        fields = ('id', 'code', 'subject', 'body')

    def create(self, validated_data):
        user = self.context['request'].user
        obj = super().create(validated_data)

        try:
            # Notification details
            type = 'Announcement Created'
            user_type = "User"
            user_identifier = user.id

            # Create Notification
            notification = Notification.objects.create(
                subject=obj.subject,
                body=obj.body,
                type=type,
                ref=obj.code
            )

            # Create NotificationUser record
            NotificationUsers.objects.create(
                user_identifier=user_identifier,
                user_type=user_type,
                notification=notification
            )

            # Send push notification
            send_push_notification(
                id=notification.id,
                user_identifier=user_identifier,
                user_type=user_type,
                message=obj.body,
                type=type,
                ref_id=obj.code,
                modified_on=obj.created_on
            )
        except Exception as e:
            pass

        return obj
    

class TaskSchedulerSerializer(serializers.ModelSerializer):

    frequency = serializers.ChoiceField(choices=AlertConfig.REPEAT_CHOICES, required=False)
    frequency_name = serializers.SerializerMethodField()
    
    start_time = serializers.DateTimeField(format="%d-%m-%Y %H:%M:%S",input_formats=['%d-%m-%Y %H:%M:%S',], required = False)
    last_run = serializers.DateTimeField(format="%d-%m-%Y %H:%M:%S", required = False)
    next_run = serializers.DateTimeField(format="%d-%m-%Y %H:%M:%S", required = False)
    created_by = UserRelatedField(user_field= 'created_by', read_only=True)
    modified_by = UserRelatedField(user_field= 'modified_by', read_only=True)
    

    def get_frequency_name(self, obj):
        return obj.get_frequency_display()


    def validate(self, attrs):
        if attrs.get('frequency') == TaskScheduler.CUSTOM and not attrs.get('custom_interval'):
            raise serializers.ValidationError({"custom_interval": "Custom interval is required when frequency is set to CUSTOM."})

        return super().validate(attrs)

    class Meta:
        model = TaskScheduler
        read_only_fields = ["frequency_name","next_run","last_run","created_by", "modified_by",]
        fields = ["id", "name", "description", "function_path", "frequency", "frequency_name", "repeat_interval", "custom_interval", "start_time", "next_run", "max_execution_time", "allow_parallel", "last_run", "is_active","created_by", "modified_by",]

    def create(self, validated_data):
        validated_data["next_run"] = validated_data.get("start_time")
        task_scheduler = TaskScheduler.objects.create(**validated_data)
        return task_scheduler

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

    
