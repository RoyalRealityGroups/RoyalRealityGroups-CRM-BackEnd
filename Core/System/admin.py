
import os, zipfile, pathlib, shutil
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import redirect

from Core.Core.admin.CoreAdmin import CoreAdmin
from Core.Core.storage.storage_backends import DBBackupMediaStorage
from Core.Core.utils.utils import ac_filter
from .models import *
from django.utils.html import mark_safe
from django import forms
from django.contrib import messages
from import_export.admin import ImportMixin, ExportMixin, ImportExportMixin
from import_export.mixins import base_formats
from django.urls import path
from django.utils.html import format_html
from django.urls import reverse
from .views import global_preferences, BackupSerializer, management
from django.shortcuts import render

from Core.System.resources import AlertConfigResource, MenuResource,SubmenuResource,MenuitemResource,NotificationResource,BackupResource, FormulaResource, ActivityLogResource, NotificationUsersResource, TemplateResource
from Core.System.management.menudata import export_menu_data, import_menu_data
from Core.System.management.formuladata import export_formula_data, import_formula_data
from Core.System.views import CreateBackup

from Core.System.views import Maintenance_On, Maintenance_Off

from dynamic_preferences.registries import global_preferences_registry

# Import filter models for admin registration
from Core.System.filter_models import SavedFilter, FilterPreset 

# Register your models here.

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




class MenuAdmin(ImportExportMixin, admin.ModelAdmin):
    resource_class = MenuResource

    fields=('name',)
    list_display=('id','code','name',  'created_on', 'modified_on', )
    list_display_links=None
    list_filter=('created_on',)
    search_fields=('code',)
    list_per_page=5
    ordering=('-code',)
    list_editable= ['code']

    # date_hierarchy='created_on'
    # empty_value_display = 'unknown'

    def get_queryset(self, request):
        queryset= super(MenuAdmin,self).get_queryset(request)
        queryset=queryset.order_by('-code',)
        return queryset



    
    # def get_queryset(self,request):
    #     user = request.user
    #     if user.is_superuser:
    #         queryset = Menu.objects.filter(is_deleted=False, )
    #     else:
    #         queryset = Menu.objects.filter(created_by = user, is_deleted=False )
            
    #     return queryset.order_by('-id')

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for instance in instances:
            instance.user = request.user
            instance.save()
        formset.save_m2m()



    # def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
    #     extra_context = extra_context or {}
    #     extra_context['show_save_and_continue'] = False
    #     extra_context['show_save'] = False
    #     extra_context['show_delete']=False
        
    #     return super(MenuAdmin, self).changeform_view(request, object_id, extra_context=extra_context)




    def view(self,obj):
        url = f'/admin/Invoice/invoice/view/{obj.id}'
        open_srt = f"window.open({url},'Invoiceview','width=600,height=400')"
        return format_html('<a href="{url}" target="popup" onclick="{open_srt}">View</a>', open_srt=open_srt, url=url)




    # def get_urls(self):
    #     urls = super().get_urls()
    #     my_urls = [
    #         path(r'view/<int:id>', self.view),
    #     ]
    #     return my_urls + urls




    # change_list_template = "initialdata.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
                path('export_menu_data/', self.set_menu_Data),
                path('import_menu_data/', self.Import_menu_data),
                path('ResetDatabase/', self.set_ResetDatabase),
                ]
        return my_urls + urls


    def set_ResetDatabase(self,request):
        dataset={}
        models=[]
        obj=ContentType.objects.all()
        for model in obj:
            dataset[model.id]=model.model
        return render(request, 'checkboxes.html', {'dataset':dataset})
      
    def set_menu_Data(self, request):
        print("export menu data")
        export_menu_data()

        return HttpResponseRedirect("../")

    def Import_menu_data(self, request):
        print("import menu data")    
        import_menu_data()     
        return HttpResponseRedirect("../")

    
		
	



class SubmenuAdmin(ImportExportMixin, admin.ModelAdmin):
    resource_class = SubmenuResource

    fields=('code','name','sequence','menu', 'icon', 'click', 'submenu',)
    list_display=('code','name','sequence','menu', 'icon', 'click', 'submenu','created_on', 'modified_on', )
    # list_display_links=None
    list_filter=('created_on',)
    search_fields=('code',)
    list_per_page=5
    ordering=('-code',)
    # date_hierarchy='created_on'
    empty_value_display = 'unknown'
    autocomplete_fields = ['menu', 'submenu']

    def get_queryset(self, request):
        queryset= super(SubmenuAdmin,self).get_queryset(request)
        queryset=queryset.order_by('-code',)
        return queryset

    # def get_queryset(self,request):
    #     user = request.user
    #     if user.is_superuser:
    #         queryset = Submenu.objects.filter(is_deleted=False, )
    #     else:
    #         queryset = Submenu.objects.filter(created_by = user, is_deleted=False )
            
    #     return queryset.order_by('-id')

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for instance in instances:
            instance.user = request.user
            instance.save()
        formset.save_m2m()



    # def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
    #     extra_context = extra_context or {}
    #     extra_context['show_save_and_continue'] = False
    #     extra_context['show_save'] = False
    #     extra_context['show_delete']=False
        
    #     return super(SubmenuAdmin, self).changeform_view(request, object_id, extra_context=extra_context)

    




class MenuitemAdmin(ImportExportMixin, admin.ModelAdmin):
    resource_class = MenuitemResource

    fields=('code','name','icon','link','sequence','menu','submenu','click','permission','description')
    list_display=( 'code','name','icon','link','sequence','menu','submenu','click','permission','description' ,'created_on', 'modified_on', )
    list_editable= ['sequence']
    list_filter=('menu','submenu')
    search_fields=('code','name',)
    autocomplete_fields = ['menu', 'submenu', 'permission']
   

class NotificationAdmin(ImportExportMixin,  admin.ModelAdmin):
    resource_class = NotificationResource

    fields=('subject','body','type','message_priority','notification_type','ref',)
    list_display=('id','subject','body','type','message_priority','notification_type','ref', 'created_on', 'is_deleted')


class NotificationUsersAdmin(ImportExportMixin,  admin.ModelAdmin):
    resource_class = NotificationUsersResource

    fields=('user','notification','seen','seen_time',)
    list_display=('id','user_identifier','user_type','notification','seen','seen_time','is_deleted')



class BackupAdmin(admin.ModelAdmin):
    resource_class = BackupResource

    fields=('name',)
    list_display=('id','code','name', 'created_on', 'modified_on', 'RESTORE','DOWNLOAD')
    list_display_links=['RESTORE','DOWNLOAD']
    list_filter=('created_on',)
    search_fields=('code',)
    list_per_page=5
    ordering=('-code',)
    # date_hierarchy='created_on'
    empty_value_display = 'unknown'


    def get_queryset(self, request):
        queryset= super(BackupAdmin,self).get_queryset(request)
        queryset=queryset.order_by('-code',)
        return queryset

    def get_queryset(self,request):
        user = request.user
        if user.is_superuser:
            queryset = Backup.objects.filter(is_deleted=False, )
        else:
            queryset = Backup.objects.filter(created_by = user, is_deleted=False )
            
        return queryset.order_by('-id')

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for instance in instances:
            instance.user = request.user
            instance.save()
        formset.save_m2m()
    
    def save_model(self, request, obj, form, change):
        obj.save()


    # def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
    #     extra_context = extra_context or {}
    #     extra_context['show_save_and_continue'] = False
    #     extra_context['show_save'] = False
    #     extra_context['show_delete']=False
        
    #     return super(BackupAdmin, self).changeform_view(request, object_id, extra_context=extra_context)

    global_preferences = global_preferences_registry.manager()
        
    def set_Maintainence_On(self, request):
        global_preferences['DEVLOPER__MAINTENANCEMODE'] = True
        # maintenance_mode(True)
        # Otokens=OutstandingToken.objects.exclude(user__is_superuser = True)
        # for Otoken in Otokens:
        #     try:
        #         RefreshToken(Otoken.token).blacklist()
        #     # except:
        #     #     print("RefreshToken")
        #     except Exception as e:
        #         print("%s : %s " % (type(e).__name__, e, ))
        #         pass

        return HttpResponseRedirect("../")

    def set_Maintainence_Off(self, request):
        global_preferences['DEVLOPER__MAINTENANCEMODE'] = False 
        return HttpResponseRedirect("../")

    def set_Data_backup(self,request):
        CreateBackup(request.user)
        self.message_user(request, "Success")
        return HttpResponseRedirect("../")
    
    def RESTORE(self,queryset):
        url = f'/system/RestoreById/{queryset.id}'
        return format_html(f'<a href="{url}"> RESTORE</a>')
    
    def DOWNLOAD(self, queryset):
        url = f'/system/DownloadById/{queryset.id}'
        return format_html(f'<a href="{url}"> DOWNLOAD</a>')


    change_list_template = "backup.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('Upload_backup_file/', self.upload_backup_file, name='upload_backup_file'),
            path('Data_backup/', self.set_Data_backup),
            path('maintainence_on/', self.set_Maintainence_On),
            path('maintainence_off/', self.set_Maintainence_Off),
            path('upload_release_file/', self.upload_release_file, name='upload_release_file'),
            path('release/', self.release_built, name='release'),
            path('backupfile/',self.backup_file, name='backupfile'),
        ]
        return my_urls + urls

    def release_built(self, request):
        context = {'file_upload_form': self.FileUploadForm()} 
        return render(request, 'release.html', context)
    
    def backup_file(self, request):
        context = {'file_upload_form': self.FileUploadForm()}
        return render(request, 'backupfile.html', context)
    
    
    def upload_backup_file(self, request, obj=None, **kwargs):
        print("UploadBackupFile")
        file_obj = request.FILES.get('file',None)
        print(file_obj,type(file_obj),request.POST, kwargs)
        # do your validation here e.g. file size/type check
        if file_obj !=None:
            # organize a path for the file in bucket
            file_directory_within_bucket =  settings.AWS_DBBACKUP_MEDIA_LOCATION

            # synthesize a full file path; note that we included the filename
            file_path_within_bucket = os.path.join(
                file_directory_within_bucket,
                file_obj.name
            )

            media_storage = DBBackupMediaStorage()
            if not media_storage.exists(file_path_within_bucket): # avoid overwriting existing file
                media_storage.save(file_path_within_bucket, file_obj)
                file_url = media_storage.url(file_path_within_bucket)

                serializer = BackupSerializer(data={ "name": file_obj.name, })
                if serializer.is_valid(raise_exception=True):
                    serializer.save(created_by=request.user)

                messages.success(request, 'file uploaded successfully .')
                return HttpResponseRedirect("../")
            
            else:
                messages.error(request, 'Filename already exits, please change the filename and try again')
                return HttpResponseRedirect("../")
            
        else:
            messages.error(request, 'File not exits')
            return HttpResponseRedirect("../")

    class FileUploadForm(forms.Form):
        release_file = forms.FileField(required=False, label="Please select a Release file")

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['file_upload_form'] = self.FileUploadForm()  # Instantiate the form
        return super().changelist_view(request, extra_context=extra_context)

    def upload_release_file(self, request):
        file_obj = request.FILES.get('release_file',None)
        base_path = settings.BASE_DIR
        build_path = os.path.join(settings.BASE_DIR, 'build')
        # try:
        # pathlib.Path(build_path).rmdir()
        shutil.rmtree(build_path)
        os.mkdir(build_path)
        # except:
        #     pass
        
        print(file_obj,type(file_obj),request.POST)
        if file_obj !=None:
            #  and file_obj.extension == ".zip"
            zf_obj = zipfile.ZipFile(file_obj)
            for name in zf_obj.namelist():
                if name.endswith('/'):
                    try: # Don't try to create a directory if exists
                        os.mkdir(os.path.join(base_path, name))
                    except:
                        pass
                else:
                    outfile = open(os.path.join(base_path, name), 'wb')
                    outfile.write(zf_obj.read(name))
                    outfile.close()
            
            management.call_command('collectstatic', '--clear', '--noinput')
            messages.success(request, 'Release Unzipped Successfully.')
            return HttpResponseRedirect("../")
        else:
            messages.error(request, 'Zip File not exits')
            return HttpResponseRedirect("../")

class AttachmentAdmin(admin.ModelAdmin):
    fields=('file',)
    list_display=('id', 'file','created_on', )




class FormulaAdmin(ImportExportMixin, admin.ModelAdmin):
    resource_class = FormulaResource

    fields=('code','name','formula',)
    list_display=('id','code','name','formula','created_on', )


    change_list_template = "formuladata.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
                path('export_formula_data/', self.set_Formula_Data),
                path('import_formula_data/', self.Import_Formula_Data),
                ]
        return my_urls + urls
        
        
    def set_Formula_Data(self, request):
        print("export formula data")
        export_formula_data()        
        return HttpResponseRedirect("../")

    def Import_Formula_Data(self, request):
        print("import formula data")   
        import_formula_data()      
        return HttpResponseRedirect("../")




class ActivityLogAdmin(admin.ModelAdmin):
    resource_class = ActivityLogResource

    fields=( 'screen_name','screen', 'type', 'instance_id', 'instance_code','data' )
    list_display=('id','user_type', 'user_identifier', 'screen_name','screen',  'type', 'instance_id','instance_code','data', 'created_on')
    autocomplete_fields = ['screen',]
    search_fields=('id','screen_name','instance_code')
    list_filter=('created_on','screen_name','screen',)


class FormulaVariablesAdmin(admin.ModelAdmin):
  
    list_display=('id', 'name','description','active','formula',' ')
    fields=( 'name','description','active', )


class ErrorAdmin(ImportExportMixin,  admin.ModelAdmin):

    # fields=('errorcode', 'requestbody','error_url')
    list_display=('id', 'errorcode','error_url','created_on','requestbody')
    readonly_fields = ('RenderedResponse','responsecontent')

    def has_change_permission(self, request, obj=None):
        return False

    def RenderedResponse(self, obj):
        if not obj.responsecontent:
            return "(No Response Content)"
        try:
            content = obj.responsecontent
            if content.startswith("b'") or content.startswith('b\"'):
                content = content[2:-1]
                content = bytes(content, "utf-8").decode("unicode_escape")  
            return mark_safe(content) 
        except Exception as e:
            return f"<pre>Error rendering HTML: {e}</pre>"
 
    
class TemporaryVerificationAdmin(ImportExportMixin,  admin.ModelAdmin):

    # fields=('errorcode', 'requestbody','error_url')
    list_display=('id', 'type','mobile', 'email','otp', 'is_phone_verified', 'is_email_verified','created_on' )



class AnnouncementsAdmin(ImportExportMixin, admin.ModelAdmin):
 
    fields = ('subject','body',)
    list_display = ('subject','body','created_on','modified_on','is_deleted')
    
class TemplateAdmin(ImportExportMixin, admin.ModelAdmin):
    resource_class = TemplateResource
    list_display = ('id', 'code', 'name', 'message','screen', 'is_active', 'created_on')
    fields = ('name', 'message', 'is_active','screen')
    search_fields = ('code', 'name')


class AlertConfigAdmin(ImportExportMixin, admin.ModelAdmin):
    resource_class = AlertConfigResource
    list_display = ('id','screen', 'event_type', 'sender_type', 'type','last_run','attachment_variable','send_doc','is_scheduled','is_attachment', 'message_priority','notification_type', 'is_active')
    fields = ('screen', 'event_type', 'sender_type', 'type','gateway','repeat_interval','frequency','start_time','last_run','is_scheduled','send_to_groups','value','variable','template','subject_template', 'message_priority','notification_type','attachment_variable','send_doc','is_attachment', 'is_active')
    search_fields = ('screen', 'gateway', 'value', 'variable')
    list_filter = ('event_type', 'sender_type', 'type', 'is_active')
    filter_horizontal = ('send_to_groups',)
    autocomplete_fields = ['screen','template','subject_template',]
    ordering = ('screen',)

class AlertConfigUsersAdmin(CoreAdmin,ImportExportMixin, admin.ModelAdmin):
    list_display = ('id','alert','user','is_deleted',)
    fields = ('alert','user_identifier','user_type','is_deleted',)
    user_related_fields = ('user',)
    list_filter = [ac_filter('alert'),]

class RecentActivityAdmin(CoreAdmin,ImportExportMixin, admin.ModelAdmin):
 
    fields = ('user_identifier','user_type','menuitem',)
    user_related_fields = ('user',)
    list_display = ('user','menuitem','created_on','modified_on','is_deleted')
    list_filter=('created_on',)
    search_fields = ('menuitem__name',)


class SettingAdmin(ImportExportMixin, admin.ModelAdmin):
 
    fields = ('preferences_code','preferences',)
    list_display = ('preferences_code','preferences','created_on','modified_on','is_deleted')

class TaskSchedulerAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id','name', 'description', 'function_path', 'frequency','repeat_interval','custom_interval', 'start_time','next_run','max_execution_time','allow_parallel','last_run','is_active')
    fields = ('name', 'description', 'function_path', 'frequency','repeat_interval','custom_interval', 'start_time','next_run','max_execution_time','allow_parallel','last_run','is_active')
    search_fields = ('name',)

class TaskExecutionLogAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'task', 'start_time', 'end_time', 'status', 'detail')
    fields = ('task', 'start_time', 'end_time', 'status', 'detail')
    search_fields = ('task__name',)
    list_filter = ('status',)

admin.site.register(Menu,MenuAdmin)
admin.site.register(Submenu,SubmenuAdmin)
admin.site.register(Menuitem,MenuitemAdmin)
admin.site.register(NotificationUsers,NotificationUsersAdmin)
admin.site.register(Notification,NotificationAdmin)
admin.site.register(Backup,BackupAdmin)
admin.site.register(Attachment,AttachmentAdmin)
# admin.site.register(Formula,FormulaAdmin)
# admin.site.register(FormulaUpdate,)
admin.site.register(ActivityLog,ActivityLogAdmin)

# admin.site.register(FormulaVariables,FormulaVariablesAdmin)
admin.site.register(Error,ErrorAdmin)
admin.site.register(Restore)
admin.site.register(RecentActivity, RecentActivityAdmin)
admin.site.register(TemporaryVerification, TemporaryVerificationAdmin)
admin.site.register(Setting,SettingAdmin)
admin.site.register(Announcements, AnnouncementsAdmin)
admin.site.register(Template, TemplateAdmin)
admin.site.register(AlertConfig, AlertConfigAdmin)
admin.site.register(AlertConfigUsers, AlertConfigUsersAdmin)
admin.site.register(TaskScheduler, TaskSchedulerAdmin)
admin.site.register(TaskExecutionLog, TaskExecutionLogAdmin)


# Register Filter Models
@admin.register(SavedFilter)
class SavedFilterAdmin(admin.ModelAdmin):
    list_display = ['name', 'screen_name', 'is_public', 'is_default', 'usage_count', 'created_on']
    list_filter = ['screen_name', 'is_public', 'is_default', 'is_deleted']
    search_fields = ['name', 'description', 'screen_name']
    readonly_fields = ['usage_count', 'last_used', 'created_on', 'modified_on']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'screen_name')
        }),
        ('Filter Configuration', {
            'fields': ('filter_config',)
        }),
        ('Settings', {
            'fields': ('is_public', 'is_default')
        }),
        ('Usage Statistics', {
            'fields': ('usage_count', 'last_used')
        }),
        ('Metadata', {
            'fields': ('created_by_type', 'created_by_identifier', 'created_on', 'modified_on', 'is_deleted'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FilterPreset)
class FilterPresetAdmin(admin.ModelAdmin):
    list_display = ['name', 'screen_name', 'sort_order', 'is_active', 'created_on']
    list_filter = ['screen_name', 'is_active']
    search_fields = ['name', 'description', 'screen_name']
    readonly_fields = ['created_on', 'modified_on']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'icon', 'screen_name')
        }),
        ('Filter Configuration', {
            'fields': ('filter_config',)
        }),
        ('Display Settings', {
            'fields': ('sort_order', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_on', 'modified_on'),
            'classes': ('collapse',)
        }),
    )




@admin.register(SMTPConfig)
class SMTPConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'host', 'port', 'username', 'from_email', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'host', 'username']
