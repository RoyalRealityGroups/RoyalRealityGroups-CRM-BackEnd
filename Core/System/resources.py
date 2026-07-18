from import_export import resources
from import_export.widgets import ForeignKeyWidget, DateTimeWidget,BooleanWidget
from import_export.fields import Field

from Core.Core.imports_exports.widget import PermissionCodeWidget
from .models import Menu,Submenu,Menuitem,Notification,Backup,Formula, ActivityLog, NotificationUsers, Restore, FormulaVariables, FormulaUpdate, AlertConfig, Template
from django.contrib.auth import get_user_model
User = get_user_model()
from Core.Core.imports_exports.resources import ModelImportExportResource
from django.contrib.auth.models import Permission


class SafeFKWidget(ForeignKeyWidget):
    """ForeignKeyWidget that forces unfiltered queryset to bypass custom managers."""
    def get_queryset(self, value, row, *args, **kwargs):
        return self.model._default_manager.db_manager('default').all()
from django.contrib.auth import get_user_model
User = get_user_model()
from Core.Core.imports_exports.resources import ModelImportExportResource
from django.contrib.auth.models import Permission 
from django.contrib.contenttypes.models import ContentType



class MenuResource(ModelImportExportResource):
    code = Field(column_name='Code', attribute='code', )
    name = Field(column_name='Name', attribute='name', )
    created_on = Field(column_name='Created On', attribute='created_on',widget=DateTimeWidget())
    modified_on = Field(column_name='Modified On', attribute='modified_on',widget=DateTimeWidget())


    class Meta:
        model = Menu
        fields = ('code', 'name', 'created_on', 'modified_on')
        export_order =('code', 'name', 'created_on', 'modified_on')
        import_id_fields = ('code',)



class SubmenuResource(ModelImportExportResource):
    code = Field(column_name='Code', attribute='code', )
    name = Field(column_name='Name', attribute='name', )
    sequence = Field(column_name='Sequence', attribute='sequence', )
    icon = Field(column_name='Icon', attribute='icon', )
    click = Field(column_name='Click', attribute='click', )
    menu = Field(column_name='Menu', attribute='menu', widget=SafeFKWidget(Menu, field='code'))
    submenu = Field(column_name='Submenu', attribute='submenu', widget=SafeFKWidget(Submenu, field='code'))
    created_on = Field(column_name='Created On', attribute='created_on',widget=DateTimeWidget())
    modified_on = Field(column_name='Modified On', attribute='modified_on',widget=DateTimeWidget())
    

    class Meta:
        model = Submenu
        fields = ('code', 'name', 'sequence', 'icon', 'click', 'menu', 'submenu', 'created_on', 'modified_on')
        export_order =('code', 'name', 'sequence', 'icon', 'click', 'menu', 'submenu', 'created_on', 'modified_on')
        import_id_fields = ('code',)



class MenuitemResource(ModelImportExportResource):
    code = Field(column_name='Code', attribute='code', )
    name = Field(column_name='Name', attribute='name', )
    icon = Field(column_name='Icon', attribute='icon', )
    link = Field(column_name='Link', attribute='link', )
    sequence = Field(column_name='Sequence', attribute='sequence', )
    click = Field(column_name='Click', attribute='click', )
    menu = Field(column_name='Menu', attribute='menu', widget=SafeFKWidget(Menu, field='code'))
    submenu = Field(column_name='Submenu', attribute='submenu', widget=SafeFKWidget(Submenu, field='code'))
    permission = Field(column_name='Permission', attribute='permission', widget=PermissionCodeWidget(Permission,))
    # permission = Field(column_name='Permission', attribute='permission', widget=ForeignKeyWidget(Permission, field='codename'))
    description = Field(column_name='Description', attribute='description', )

    created_on = Field(column_name='Created On', attribute='created_on',widget=DateTimeWidget())
    modified_on = Field(column_name='Modified On', attribute='modified_on',widget=DateTimeWidget())
    # permission = Field()
    
    # def dehydrate_permission(self, Menuitem):
    #     # print("dehydrate......",Menuitem)
    #     if Menuitem.permission:
    #         return '%s.%s' % (Menuitem.permission.content_type.app_label, Menuitem.permission.codename)
    #     else:
    #         ''

    class Meta:
        model = Menuitem
        fields = ('code', 'name', 'icon', 'link', 'sequence', 'click', 'menu', 'submenu', 'permission', 'description', 'created_on', 'modified_on')
        export_order = ('code', 'name', 'icon', 'link', 'sequence', 'click', 'menu', 'submenu', 'permission', 'description', 'created_on', 'modified_on')
        import_id_fields = ('code',)





class NotificationResource(resources.ModelResource):

    class Meta:
        model = Notification
        fields = ('id', 'subject', 'body', 'type', 'message_priority','notification_type', 'ref',)

class NotificationUsersResource(resources.ModelResource):

    class Meta:
        model = NotificationUsers
        fields = ('id','user','body','notification','seen','seen_time','status')

class BackupResource(resources.ModelResource):

    class Meta:
        model = Backup
        fields = ( 'id', 'code', 'name') # ,'created_by__username','modified_by__username'



class RestoreResource(resources.ModelResource):

    class Meta:
        model = Restore
        fields = ( 'id', 'code', 'name') # ,'created_by__username','modified_by__username'



class FormulaResource(ModelImportExportResource):
    code = Field(column_name='Code', attribute='code', )
    name = Field(column_name='Name', attribute='name', )
    formula = Field(column_name='Formula', attribute='formula', )
    created_on = Field(column_name='Created On', attribute='created_on',widget=DateTimeWidget())
    modified_on = Field(column_name='Modified On', attribute='modified_on',widget=DateTimeWidget())
    # created_by = Field(column_name='Created By', attribute='created_by', widget=ForeignKeyWidget(User, field='username'))
    # modified_by = Field(column_name='Modified By', attribute='modified_by', widget=ForeignKeyWidget(User, field='username'))

    class Meta:
        model = Formula
        fields = ( 'id', 'code', 'name','formula', 'created_on', 'modified_on') # 'created_by', 'modified_by',
        export_order =('code', 'name','formula', 'created_on','modified_on') # 'created_by', 'modified_by',
        import_id_fields = ('code',)



class FormulaVariablesResource(ModelImportExportResource):
    id = Field(column_name='Id', attribute='id', )
    name = Field(column_name='Name', attribute='name', )
    description = Field(column_name='Description', attribute='description', )
    active = Field(column_name='Active', attribute='active',widget=BooleanWidget())
    formula = Field(column_name='Formula', attribute='formula', widget=ForeignKeyWidget(Formula, field='code') )

    class Meta:
        model = FormulaVariables
        fields = ( 'id', 'name','description', 'active','formula')
        export_order =( 'id', 'name','description', 'active','formula')
        import_id_fields = ('id',)


class FormulaUpdateResource(ModelImportExportResource):
    id = Field(column_name='Id', attribute='id', )
    formula_txt = Field(column_name='Formula Txt', attribute='formula_txt', )
    formula = Field(column_name='Formula', attribute='formula', widget=ForeignKeyWidget(Formula, field='code') )
    created_on = Field(column_name='Created On', attribute='created_on',widget=DateTimeWidget())
    # created_by = Field(column_name='Created By', attribute='created_by', widget=ForeignKeyWidget(User, field='username'))

    class Meta:
        model = FormulaUpdate
        fields = ( 'id', 'formula', 'formula_txt','created_on',) # 'created_by',
        export_order =( 'id', 'formula', 'formula_txt','created_on',) # 'created_by',
        import_id_fields = ('id',)
        

class ActivityLogResource(resources.ModelResource):

    class Meta:
        model = ActivityLog
        fields = ( 'id', 'type', 'screen_name', 'instance_code' ) 


class AlertConfigResource(resources.ModelResource):
    screen = Field(column_name='screen', attribute='screen')
    template = Field(column_name='template', attribute='template', widget=ForeignKeyWidget(Template, field='name'))
    subject_template = Field(column_name='subject_template', attribute='subject_template', widget=ForeignKeyWidget(Template, field='name'))
    web_navigation_url = Field(column_name='web_navigation_url', attribute='web_navigation_url', widget=ForeignKeyWidget(Template, field='name'))
    mobile_navigation_url = Field(column_name='mobile_navigation_url', attribute='mobile_navigation_url', widget=ForeignKeyWidget(Template, field='name'))
    
    class Meta:
        model = AlertConfig
        fields = (
            'id', 'screen', 'event_type', 'sender_type', 'type', 'gateway',
            'value', 'variable', 'template', 'subject_template', 'message_priority', 'notification_type', 'web_navigation_url',
            'mobile_navigation_url', 'is_active', 'is_scheduled', 'frequency',
            'repeat_interval', 'start_time', 'send_doc', 'is_attachment', 'attachment_variable'
        )
        export_order = fields
        import_id_fields = ('id',)
        skip_unchanged = True
        use_bulk = False
        
    def dehydrate_screen(self, alert_config):
        """Export ContentType as app_label.model"""
        if alert_config.screen:
            return f"{alert_config.screen.app_label}.{alert_config.screen.model}"
        return ''
    
    def before_import_row(self, row, **kwargs):
        """Process ContentType field before import"""
        super().before_import_row(row, **kwargs)
        
        # Handle screen field
        if 'screen' in row and row['screen'] != '':
            screen_value = row['screen']
            try:
                if '.' in str(screen_value):
                    app_label, model = str(screen_value).split('.', 1)
                    content_type = ContentType.objects.get_by_natural_key(app_label, model)
                    row['screen'] = content_type
                elif screen_value.isdigit():
                    row['screen'] = int(screen_value)
                else:
                    row['screen'] = None
            except (ContentType.DoesNotExist, ValueError, AttributeError):
                row['screen'] = None
        
class TemplateResource(resources.ModelResource):
    """Resource class for Template model import/export operations"""
    
    screen = Field(column_name='screen', attribute='screen')
    name = Field(column_name='name', attribute='name')
    message = Field(column_name='message', attribute='message')
    code = Field(column_name='code', attribute='code')
    is_active = Field(column_name='is_active', attribute='is_active', widget=BooleanWidget())
    
    class Meta:
        model = Template
        fields = ('code', 'name', 'message', 'screen', 'is_active')
        export_order = ('code', 'name', 'message', 'screen', 'is_active')
        import_id_fields = ('name',)
        skip_unchanged = True
        report_skipped = True
        
    def dehydrate_screen(self, template):
        """Export ContentType as app_label.model"""
        if template.screen:
            return f"{template.screen.app_label}.{template.screen.model}"
        return ''
    
    def before_import_row(self, row, **kwargs):
        """Process ContentType field before import"""
        super().before_import_row(row, **kwargs)
        
        # Handle screen field
        if 'screen' in row and row['screen'] != '':
            screen_value = row['screen']
            try:
                if '.' in str(screen_value):
                    app_label, model = str(screen_value).split('.', 1)
                    content_type = ContentType.objects.get_by_natural_key(app_label, model)
                    # Store the ID for the ForeignKey field
                    row['screen'] = content_type
                elif screen_value.isdigit():
                    # Already an ID, keep as is
                    row['screen'] = int(screen_value)
                else:
                    row['screen'] = None
            except (ContentType.DoesNotExist, ValueError, AttributeError):
                row['screen'] = None