from import_export.fields import Field
from django.contrib.auth import get_user_model

from Core.Core.imports_exports.resources import ModelImportExportResource
User = get_user_model()


import logging

logger = logging.getLogger(__name__)






class UserResource(ModelImportExportResource):
    username = Field(column_name='User Name', attribute='username',)
    email = Field(column_name='Email', attribute='email', )
    phone = Field(column_name='Phone', attribute='phone', )
    # otp = Field(column_name='Otp', attribute='otp', )
    first_name = Field(column_name='First Name', attribute='first_name', )
    last_name = Field(column_name='Last Name', attribute='last_name', )
    # location =  Field(column_name='Location', attribute='location',widget=ForeignKeyWidget(Location, field='name'))
    # area =  Field(column_name='Area', attribute='area',widget=ForeignKeyWidget(Area, field='name'))
    # city =  Field(column_name='City', attribute='city',widget=ForeignKeyWidget(City, field='name'))
    # zone =  Field(column_name='Zone', attribute='zone',widget=ForeignKeyWidget(Zone, field='name'))
    # state =  Field(column_name='State', attribute='state',widget=ForeignKeyWidget(State, field='name'))
    # pricebook = Field(column_name='PriceBook', attribute='pricebook', widget=ForeignKeyWidget(PriceBook, 'name'))

    class Meta:
        model = User
        fields = ('username','email','phone','first_name','last_name',)
        import_fields = ( 'username','email','phone','first_name','last_name',)
        export_order = ( 'username','email','phone','first_name','last_name',)
        import_id_fields = ('username', )
