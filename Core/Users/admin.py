from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin as AuthGroupAdmin
from import_export.widgets import ForeignKeyWidget
from import_export.admin import ImportMixin, ExportMixin, ImportExportMixin
from import_export import resources, fields
from import_export.mixins import base_formats
from import_export.fields import Field
from Core.Core.utils.utils import ac_filter, get_model_fields
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from django.contrib.auth.hashers import make_password
from django.conf import settings

from Core.Users.models import Assignee, AssigneeDefnition, Authorization, AuthorizationDefinition, AuthorizationHistory, CodeTemplate, ContentTypeDetail, DataPermissions, Device, DeviceLog, DjangoApp, Groupdetails, JwtToken, PermissionDetail, UserType
from Core.Users.resources import ContentTypeDetailResource, DjangoAppResource, GroupResource, PermissionDetailResource
from Users.models import  User


from django.apps import apps
from django.urls import path
from django.utils.html import format_html
from django.shortcuts import render, get_object_or_404


class ExportMixinAdmin(ExportMixin):

    def get_export_formats(self):
        formats = (
            base_formats.CSV,
          )

        return [f for f in formats if f().can_export()]

    class Meta:
        abstract = True

class ImportMixinAdmin(ImportMixin):

    def get_import_formats(self):
        formats = (
            base_formats.CSV,
          )

        return [f for f in formats if f().can_export()]

    class Meta:
        abstract = True
      
      
class DeviceResource(resources.ModelResource):
    user = Field(column_name='user', attribute='user', widget=ForeignKeyWidget(User, field='username'))
    type = fields.Field(
        attribute='get_type_display',
        column_name=('TYPE')
    )

    class Meta:
        model = Device
        fields=('id','code','user','uuid', 'type','fcmtoken','apntoken','accesstoken','session', 'is_active','created_on','modified_on','status')#
        

class DeviceAdmin( ImportExportMixin, ImportMixinAdmin, admin.ModelAdmin):
    resource_class = DeviceResource
    fields=('name','uuid', 'type','fcmtoken','apntoken','accesstoken','session', 'is_active','socket',) # 'user',
    list_display=('code','name','uuid', 'type','fcmtoken','apntoken', 'is_active','socket','user_identifier','user_type','created_on','modified_on', ) # 'user',
    search_fields=('id','code','name','uuid', 'type','user_identifier','user_type',) # 'user__username',
    ordering=('code',)
    list_per_page=25


class DeviceLogAdmin( admin.ModelAdmin):
    fields=('device', 'ip_address','login','logout') # 'user',
    list_display=('id', 'device', 'ip_address','login','logout','user_identifier','user_type','created_on','modified_on', ) # 'user',
    search_fields=('id','device__code','ip_address', 'user_identifier','user_type',) # 'user__username',
    # ordering=('id',)





class GroupdetailsAdmin(admin.ModelAdmin):
    list_display = ('group','reporting_to', 'static',)
    fields = ('group','reporting_to', 'static',)
    ordering=('id',)



class UserAddressVersionAdmin(admin.ModelAdmin):
    list_display = ('code','user','address', 'area','city','district','state','pincode','created_on','modified_on',)#
    fields = ('code','user','address', 'area','city','district','state','pincode',)
    ordering=('id',)


class PermissionAdmin(admin.ModelAdmin):
    list_display = ('name','content_type','codename',)
    fields = ('name','content_type','codename',)
    search_fields= ('id','name',"content_type__app_label", "content_type__model",'codename',)
    ordering=("content_type__app_label", "content_type__model", "codename",)

class PermissionDetailAdmin(ImportExportMixin, admin.ModelAdmin):
    resource_class = PermissionDetailResource

    list_display = ('name','permission','hide','release')
    fields = ('name','permission','hide','release')
    search_fields=('id','name','permission__content_type__app_label','permission__content_type__model','hide',)
    ordering=('id',)
    list_per_page = 800


class ContentTypeAdmin(admin.ModelAdmin):
    list_display = ('app_label', 'model', 'view_fields_link')
    fields = ('app_label', 'model')
    ordering = ('app_label',)
    search_fields = ('app_label', 'model')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:contenttype_id>/fields/',
                self.admin_site.admin_view(self.view_model_fields),
                name='view_model_fields',
            ),
        ]
        return custom_urls + urls

    def view_fields_link(self, obj):
        url = f'/admin/contenttypes/contenttype/{obj.id}/fields/'
        return format_html('<a href="{}" title="View Fields"><span style="font-size: 18px;">👁️</span></a>', url)
    view_fields_link.short_description = 'Fields'

    def view_model_fields(self, request, contenttype_id):
        content_type = get_object_or_404(ContentType, id=contenttype_id)
        model_class = content_type.model_class()

        if model_class is None:
            return render(request, 'model_not_found.html', {
                'content_type': content_type,
            })

        fields = get_model_fields(model_class, current_depth=1, max_depth=4,flatten=True)

        return render(request, 'model_fields.html', {
            'content_type': content_type,
            'model_class': model_class,
            'fields': fields,
        })

 
 

class ContentTypeDetailAdmin(ImportExportMixin, admin.ModelAdmin):
    resource_class = ContentTypeDetailResource
 
    list_display = ('name','contenttype', 'app', 'hide','release','show_in_data_permissions','show_in_authorization','show_in_assignee')
    fields = ('name','contenttype','app', 'hide','release','show_in_data_permissions','show_in_authorization','show_in_assignee')
    search_fields=('id','name','hide',)
    list_editable = ('show_in_data_permissions','show_in_authorization')
    list_per_page = 150
    ordering=('id',)
    list_filter = [(ac_filter('contenttype',)),
                   (ac_filter('app',)),
                  ]
    autocomplete_fields = ['contenttype', 'app']


class DjangoAppAdmin(ImportExportMixin, admin.ModelAdmin):
    resource_class = DjangoAppResource

    list_display = ('name','app_label', 'sequence', 'hide',)
    fields = ('name','app_label', 'sequence', 'hide',)
    readonly_fields =('app_label',)
    list_editable = ('sequence',)
    ordering=('sequence', 'name')
    search_fields=('name', 'app_label')
 
 

class GroupAdmin(ImportExportMixin, AuthGroupAdmin):
    resource_class = GroupResource

    # list_display = ('id', 'name',)
    # fields = ( 'name', 'permissions', )
    # ordering=('id',)
    

class DataPermissionsAdmin(ImportExportMixin, admin.ModelAdmin):
 
    list_display = ('type','group','user_type', 'user_identifier', 'model_path', 'instance_id', 'exclusions','entry','view','report')
    fields = ('type','group','user_type', 'user_identifier', 'model_path', 'instance_id', 'exclusions','entry','view','report')



class JwtTokenAdmin(ImportExportMixin, admin.ModelAdmin):
 
    list_display = ('user_identifier','user_type','refresh_token','access_token', 'session_data', 'access_expiring_on','refresh_expiring_on',)
    fields = ('user_identifier','user_type','refresh_token','access_token', 'session_data', 'access_expiring_on','refresh_expiring_on',)



class AuthorizationDefinitionAdmin(ImportExportMixin, admin.ModelAdmin):
 
    fields = ('screen','level')
    list_display = ('code','screen','level',)
    list_filter =[(ac_filter('screen',)),
                 ]
    search_fields = ('code',)
    autocomplete_fields = ['screen']
 

class AuthorizationAdmin(ImportExportMixin, admin.ModelAdmin):
 
    fields = ('type','user_type', 'user_identifier', 'group','screen','level','is_deleted')
    list_display = ('code','type','user_type', 'user_identifier', 'group','screen','level','created_on','modified_on','is_deleted')#

    list_filter = [(ac_filter('screen',)),
                   (ac_filter('group',)),
                  ]
    search_fields =('code',)
    autocomplete_fields = ['screen']



class AuthorizationHistoryAdmin(ImportExportMixin, admin.ModelAdmin):
 
    fields = ('screen','instance_id','authorized_level','authorized_status','description','authorized_by_identifier', 'authorized_by_type')
    list_display = ('code','screen','instance','instance_id','authorized_level','authorized_status','description','authorized_by_identifier', 'authorized_by_type', 'authorized_on','created_on','modified_on','is_deleted')#

    list_filter = [(ac_filter('screen',)),
                  ]
    search_fields =('code',)
    autocomplete_fields = ['screen',]

    def instance(self, obj):
        try:
            if obj.screen and obj.instance_id:
               
                app_label, model_name = obj.screen.app_label, obj.screen.model
                model_class = apps.get_model(app_label, model_name)    
               
                instance = model_class.objects.filter(id=obj.instance_id).first()
               
                if instance:
                    code = getattr(instance, 'code', None)
                    name = getattr(instance, 'name', '')
                   
                    return f"{code} - {name}"
        except Exception:
            return ''
        return obj.instance_id
     
 

class UserPreferencesAdmin(ImportExportMixin, admin.ModelAdmin):
 
    fields = ('user','preferences',)
    list_display = ('user','preferences','created_on','modified_on','is_deleted')


class AssigneeAdmin(ImportExportMixin, admin.ModelAdmin):
 
    fields = ('user_type','user_identifier','screen','instance_id','description')
    list_display = ('user_type', 'user_identifier', 'screen','instance','instance_id','description','modified_on','is_deleted', 'created_on',)#

    list_filter =[(ac_filter('screen',)),
                 ]
    autocomplete_fields= ['screen']

    def instance(self, obj):
        try:
            if obj.screen and obj.instance_id:
               
                app_label, model_name = obj.screen.app_label, obj.screen.model
                model_class = apps.get_model(app_label, model_name)     
               
                instance = model_class.objects.filter(id=obj.instance_id).first()
               
                if instance:
                    code = getattr(instance, 'code', None)
                    name = getattr(instance, 'name', '')
                    
                    return f"{code} - {name}"
        except Exception:
            return ''
        return obj.instance_id 



    
class AssigneeDefnitionAdminForm(forms.ModelForm):
    USER_TYPE_CHOICES = [(model['type'], model['name']) for model in settings.USER_MODELS]

    user_types = forms.MultipleChoiceField(
        choices=USER_TYPE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="User Types"
    )

    class Meta:
        model = AssigneeDefnition
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.user_types:
            self.initial['user_types'] = self.instance.user_types

    def clean_user_types(self):
        return self.cleaned_data.get('user_types', [])


class AssigneeDefnitionAdmin(ImportExportMixin, admin.ModelAdmin):
 
    form = AssigneeDefnitionAdminForm
    fields = ('user_types','screen','apply_type','required_authorization')
    list_display = ('screen','apply_type','required_authorization','created_on', 'modified_on','is_deleted')#
    list_filter =[(ac_filter('screen',)),
                 ]
    autocomplete_fields = ['screen']
 
class UserTypeAdminForm(forms.ModelForm):
    class Meta:
        model = UserType
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        user_type_choices = [
            (entry["type"], entry["name"]) for entry in getattr(settings, 'USER_MODELS', [])
        ]

        self.fields['user_types'] = forms.MultipleChoiceField(
            choices=user_type_choices,
            widget=forms.CheckboxSelectMultiple,
            required=False
        )

        # Prepopulate selected values if editing
        if self.instance.pk and self.instance.user_types:
            self.fields['user_types'].initial = self.instance.user_types

class AssigneeByPassAdmin(ImportExportMixin, admin.ModelAdmin):
 
    fields = ('type','user','group','screen')
    list_display = ('type','user','group','screen','created_on','modified_on','is_deleted') #

class UserTypeAdmin(admin.ModelAdmin):
    form = UserTypeAdminForm
    list_display = ('id','screen','user_types',)
    fields = ('screen','user_types',)
    list_per_page = 25
    

admin.site.register(Device, DeviceAdmin)
admin.site.register(DeviceLog, DeviceLogAdmin)
admin.site.register(Groupdetails, GroupdetailsAdmin)
admin.site.register(Permission, PermissionAdmin)
admin.site.register(PermissionDetail, PermissionDetailAdmin)
admin.site.register(ContentType, ContentTypeAdmin)
admin.site.register(ContentTypeDetail, ContentTypeDetailAdmin)
admin.site.register(DjangoApp, DjangoAppAdmin)
admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)

admin.site.register(DataPermissions, DataPermissionsAdmin)
admin.site.register(JwtToken, JwtTokenAdmin)

admin.site.register(AuthorizationDefinition, AuthorizationDefinitionAdmin)
admin.site.register(Authorization, AuthorizationAdmin)
admin.site.register(AuthorizationHistory,AuthorizationHistoryAdmin)
admin.site.register(Assignee, AssigneeAdmin)
admin.site.register(AssigneeDefnition, AssigneeDefnitionAdmin)
# admin.site.register(AssigneeByPass, AssigneeByPassAdmin)
admin.site.register(CodeTemplate)
admin.site.register(UserType,UserTypeAdmin)
