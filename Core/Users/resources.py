from import_export import resources
from import_export.widgets import ForeignKeyWidget, BooleanWidget
from import_export.fields import Field
from django.contrib.auth import get_user_model
User = get_user_model()
from Core.Core.imports_exports.widget import PermissionCodeWidget
from Core.Users.models import Device,DeviceLog, DjangoApp, ContentTypeDetail, PermissionDetail, DataPermissions, AuthorizationDefinition, Authorization, AuthorizationHistory
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from Core.Core.imports_exports.resources import ModelImportExportResource


from django.contrib.auth.models import Group, Permission 

import logging

logger = logging.getLogger(__name__)





class DeviceResource(resources.ModelResource):

    class Meta:
        model = Device
        fields = ( 'id', 'code', 'name','uuid','type','fcmtoken','apntoken','accesstoken','session', 'is_active', ) # 'created_by__username','modified_by__username'




class DeviceLogResource(resources.ModelResource):

    class Meta:
        model = DeviceLog
        fields = ( 'id', 'device__name','ip_address','login','logout') # , 'created_by__username','modified_by__username'



class DjangoAppResource(ModelImportExportResource):
    name = Field(column_name='Name', attribute='name', )
    app_label = Field(column_name='App_Label', attribute='app_label', )
    hide = Field(column_name='Hide', attribute='hide', widget=BooleanWidget())
    sequence = Field(column_name='sequence', attribute='sequence', )

    class Meta:
        model = DjangoApp
        fields = ( 'name','app_label','hide','sequence')
        export_order =('name','app_label','hide','sequence')
        import_id_fields = ('app_label',)


class ContentTypeDetailResource(ModelImportExportResource):
    name = Field(column_name='Name', attribute='name', )
    contenttype = Field(column_name='ContentType', attribute='contenttype', widget=ForeignKeyWidget(ContentType, field='model'))
    app = Field(column_name='App', attribute='app', widget=ForeignKeyWidget(DjangoApp, field='app_label'))
    hide = Field(column_name='Hide', attribute='hide', widget=BooleanWidget())


    class Meta:
        model = ContentTypeDetail
        fields = ( 'name', 'contenttype', 'app', 'hide')
        export_order =('name', 'contenttype', 'app', 'hide')
        import_id_fields = ('contenttype',)


class PermissionDetailResource(ModelImportExportResource):
    name = Field(column_name='Name', attribute='name', )
    permission = Field(column_name='Permission', attribute='permission', widget=PermissionCodeWidget(Permission, ))
    hide = Field(column_name='Hide', attribute='hide', widget=BooleanWidget())


    class Meta:
        model = PermissionDetail
        fields = ( 'name', 'permission', 'hide')
        export_order =('name', 'permission', 'hide')
        import_id_fields = ('permission',)


class GroupResource(ModelImportExportResource):
    name = Field(column_name='Name', attribute='name', )
    permission = Field(column_name='Permission', attribute='permission', widget=PermissionCodeWidget(Permission, ))
    locationtype = Field(column_name='Location Type', attribute='locationtype', )
    reporting_to_id = Field(column_name='reporting_to Id', attribute='reporting_to_id', )


    class Meta:
        model = Group
        fields = ('id', 'name', 'permission', 'permissions', 'locationtype', 'reporting_to_id')
        export_order = ('id', 'name', 'permission', 'permissions', 'locationtype', 'reporting_to_id')
 

class DataPermissionsResource(ModelImportExportResource):
    class Meta:
        model = DataPermissions
        fields = (
            'id', 'type',  'group__name', 'model_path', 'instance_id', 
            'exclusions', 'entry', 'view', 'report', 'is_deleted'
        ) #'user__username',
        export_order = fields
        skip_unchanged = True
        use_bulk = True



class AuthorizationDefinitionResource(ModelImportExportResource):
    class Meta:
        model = AuthorizationDefinition
        fields = ('id', 'screen', 'level')
        export_order = fields
        skip_unchanged = True
        use_bulk = True

class AuthorizationResource(ModelImportExportResource):
    class Meta:
        model = Authorization
        fields = ('id', 'type', 'group__name', 'screen', 'level')
        export_order = fields
        skip_unchanged = True
        use_bulk = True

class AuthorizationHistoryResource(ModelImportExportResource):
    class Meta:
        model = AuthorizationHistory
        fields = ('id', 'screen', 'instance_id', 'authorized_level', 'authorized_status', 'description',  'authorized_on')
        export_order = fields
        skip_unchanged = True
        use_bulk = True

