from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from import_export.admin import ImportMixin, ExportMixin, ImportExportMixin
from import_export.mixins import base_formats

from django.contrib.auth.hashers import make_password

from Users.models import  User

from Users.resources import UserResource



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

class UserAdmin(ImportExportMixin,  admin.ModelAdmin):
    resource_class = UserResource
    list_display = (
        'id', 'username', 'email', 'phone', 'first_name', 'last_name', 
        'is_active', 'is_staff', 'designation', 'user_status', 'created_at'
    )
    list_select_related = []  # Disable automatic select_related
    fields=(
        'username','email','phone','alternate_phone','password','first_name','last_name','gender',
        'profilepicture','address','pincode','device_access','is_email_verified','is_phone_verified',
        'is_active','is_staff','is_guest','groups','companies','has_all_companies','locations','has_all_locations',
        'designation','reporting_manager','user_status','must_reset_password',
        'lead_data_scope','followup_data_scope','sitevisit_data_scope','booking_data_scope',
        'receive_email','receive_sms','receive_notification','erp_id','erp_code',
        'created_by_type','created_by_identifier','modified_by_type','modified_by_identifier'
    )
    ordering=('username','created_at')
    list_per_page=25
    search_fields = ['id','first_name','username','phone','email','alternate_phone']
    # Removed filter_horizontal to prevent large query issues
    # Use raw_id_fields or autocomplete_fields instead for large datasets
    raw_id_fields = ['reporting_manager']
    autocomplete_fields = []  # Add if you have autocomplete configured for groups
    
    def get_queryset(self, request):
        # Optimize queryset to prevent complex joins
        qs = super().get_queryset(request)
        # Only select what's needed for list display
        return qs.only(
            'id', 'username', 'email', 'phone', 'first_name', 'last_name',
            'is_active', 'is_staff', 'channel_partner_type', 'created_at'
        )
    
    # def get_queryset(self, request):
    #     return self.model.objects.filter(groups__name ='employee')

    def save_model(self, request, obj, form, change):

        if not change:
            obj.password = make_password(obj.password)
            # obj.save()
        else:
            # try:
            old_password = User.objects.get(pk=obj.pk).password
            new_password= obj.password
            if old_password != new_password:
                obj.password = make_password(obj.password)
                # obj.save()
            # except:
            #     pass
            
        super().save_model(request, obj, form, change)
        
    def has_delete_permission(self, request, obj=None):                   
        return True
    
 

class UserPreferencesAdmin(ImportExportMixin, admin.ModelAdmin):
 
    fields = ('user','preferences',)
    list_display = ('user','preferences','created_on','modified_on','is_deleted')


admin.site.register(User, UserAdmin)

