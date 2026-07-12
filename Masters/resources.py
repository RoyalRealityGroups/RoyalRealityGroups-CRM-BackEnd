from import_export import resources
from import_export.widgets import ForeignKeyWidget, DateTimeWidget, IntegerWidget, Widget, ManyToManyWidget
from import_export.fields import Field

from Core.Core.imports_exports.widget import ChoicesWidget
from .models import *
from import_export.widgets import ForeignKeyWidget, DateTimeWidget

from Masters.models import Country, State, District, Mandal, City, Area, Location, WareHouse, Route, RouteCoverage, Company, Category, Brand, Tax, Item, ItemTaxComposition, Agent, Project
from django.contrib.auth import get_user_model
User = get_user_model()


# ==================== Master Resources ====================

class HeaderValidationMixin:
    """Validates CSV headers and defaults empty boolean fields."""
    def before_import(self, dataset, using_transactions=None, dry_run=None, **kwargs):
        self._csv_headers = list(dataset.headers)
        expected = {f.column_name for f in self.get_fields()}
        if not expected.intersection(self._csv_headers):
            raise Exception(
                f'CSV headers do not match. Expected at least one of: {", ".join(sorted(expected))}. '
                f'Got: {", ".join(self._csv_headers)}'
            )
        return super().before_import(dataset, **kwargs)

    def before_import_row(self, row, **kwargs):
        # Default empty boolean fields to their model default
        model = self.Meta.model
        for field in self.get_fields():
            col = field.column_name
            if col in row and row[col] in (None, '', 'None'):
                try:
                    model_field = model._meta.get_field(field.attribute)
                    if hasattr(model_field, 'get_internal_type') and model_field.get_internal_type() == 'BooleanField':
                        row[col] = model_field.default if model_field.has_default() else True
                except Exception:
                    pass
        # Auto-match existing record by name when code is not provided
        if 'code' in [f.attribute for f in self.get_fields()]:
            code_col = next((f.column_name for f in self.get_fields() if f.attribute == 'code'), None)
            name_col = next((f.column_name for f in self.get_fields() if f.attribute == 'name'), None)
            if code_col and name_col and not row.get(code_col) and row.get(name_col):
                existing = model.objects.filter(name=row[name_col], is_deleted=False).first()
                if existing:
                    row[code_col] = existing.code
        # Validate mandatory fields from get_field_info
        if hasattr(self, 'get_field_info'):
            field_col_map = {f.attribute: f.column_name for f in self.get_fields()}
            missing = []
            for info in self.get_field_info():
                if info.get('is_mandatory'):
                    col = field_col_map.get(info['field_name'], info.get('display_name', ''))
                    val = row.get(col)
                    if val is None or str(val).strip() in ('', 'None'):
                        missing.append(info['display_name'])
            if missing:
                from django.core.exceptions import ValidationError
                raise ValidationError(f"Missing mandatory fields: {', '.join(missing)}")
        return super().before_import_row(row, **kwargs)


class CountryResource(HeaderValidationMixin, resources.ModelResource):
    """Resource for Country import/export with code-based identification."""
    code = Field(column_name='Code', attribute='code')
    name = Field(column_name='Country Name', attribute='name')

    class Meta:
        model = Country
        fields = ('code', 'name')
        export_order = ('code', 'name')
        import_id_fields = ('code',)  # Use code for matching existing records
        skip_unchanged = True
        report_skipped = True

    def get_field_info(self):
        """Return field metadata for frontend field selection."""
        return [
            {'field_name': 'code', 'display_name': 'Code', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Optional. Leave blank to auto-generate (e.g., IND, US, UK)'},
            {'field_name': 'name', 'display_name': 'Country Name', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Full country name'},
        ]


class StateResource(HeaderValidationMixin, resources.ModelResource):
    """Resource for State import/export with code-based foreign key lookup."""
    code = Field(column_name='Code', attribute='code')
    name = Field(column_name='State Name', attribute='name')
    gst_code = Field(column_name='GST Code', attribute='gst_code')
    country = Field(
        column_name='Country Code',
        attribute='country',
        widget=ForeignKeyWidget(Country, field='code')  # Use code instead of ID
    )

    class Meta:
        model = State
        fields = ('code', 'name', 'gst_code', 'country')
        export_order = ('code', 'name', 'gst_code', 'country')
        import_id_fields = ('code',)
        skip_unchanged = True
        report_skipped = True

    def get_field_info(self):
        """Return field metadata for frontend field selection."""
        return [
            {'field_name': 'code', 'display_name': 'Code', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Optional. Leave blank to auto-generate (e.g., AP, TS, KA)'},
            {'field_name': 'name', 'display_name': 'State Name', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Full state name'},
            {'field_name': 'gst_code', 'display_name': 'GST Code', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': '2-digit GST state code (e.g., 01, 33)'},
            {'field_name': 'country', 'display_name': 'Country Code', 'is_mandatory': True, 'field_type': 'FOREIGN_KEY', 'help_text': 'Country code (e.g., IND, US)', 'foreign_model': 'Country', 'foreign_field': 'code'},
        ]


class CityResource(HeaderValidationMixin, resources.ModelResource):
    """Resource for City import/export with code-based foreign key lookups."""
    code = Field(column_name='Code', attribute='code')
    name = Field(column_name='City_Name', attribute='name')
    state = Field(
        column_name='State_Code',
        attribute='state',
        widget=ForeignKeyWidget(State, field='code')
    )
    district = Field(
        column_name='District_Code',
        attribute='district',
        widget=ForeignKeyWidget(District, field='code')
    )
    mandal = Field(
        column_name='Mandal_Code',
        attribute='mandal',
        widget=ForeignKeyWidget(Mandal, field='code')
    )
    pincode = Field(column_name='Pincode', attribute='pincode')

    class Meta:
        model = City
        fields = ('code', 'name', 'state', 'district', 'mandal', 'pincode')
        export_order = ('code', 'name', 'state', 'district', 'mandal', 'pincode')
        import_id_fields = ('code',)
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        super().before_import_row(row, **kwargs)
        district_code = (row.get('District_Code') or '').strip()
        mandal_code = (row.get('Mandal_Code') or '').strip()
        state_code = (row.get('State_Code') or '').strip()
        
        if district_code and state_code:
            district = District.objects.filter(code=district_code, is_deleted=False).select_related('state').first()
            if district and district.state.code != state_code:
                from django.core.exceptions import ValidationError
                raise ValidationError(
                    f'District "{district.name}" ({district_code}) belongs to state "{district.state.name}" ({district.state.code}), '
                    f'not "{state_code}".'
                )
        
        if mandal_code and district_code:
            mandal = Mandal.objects.filter(code=mandal_code, is_deleted=False).select_related('district').first()
            if mandal and mandal.district.code != district_code:
                from django.core.exceptions import ValidationError
                raise ValidationError(
                    f'Mandal "{mandal.name}" ({mandal_code}) belongs to district "{mandal.district.name}" ({mandal.district.code}), '
                    f'not "{district_code}".'
                )

    def get_field_info(self):
        """Return field metadata for frontend field selection."""
        return [
            {'field_name': 'code', 'display_name': 'Code', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Optional. Leave blank to auto-generate (e.g., HYD, BLR)'},
            {'field_name': 'name', 'display_name': 'City_Name', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Full city name'},
            {'field_name': 'state', 'display_name': 'State_Code', 'is_mandatory': True, 'field_type': 'FOREIGN_KEY', 'help_text': 'State code (e.g., AP, TS)', 'foreign_model': 'State', 'foreign_field': 'code'},
            {'field_name': 'district', 'display_name': 'District_Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'District code (optional)', 'foreign_model': 'District', 'foreign_field': 'code'},
            {'field_name': 'mandal', 'display_name': 'Mandal_Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Mandal code (optional)', 'foreign_model': 'Mandal', 'foreign_field': 'code'},
            {'field_name': 'pincode', 'display_name': 'Pincode', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'PIN code (optional)'},
        ]


class AreaResource(HeaderValidationMixin, resources.ModelResource):
    """Resource for Area import/export with code-based foreign key lookups."""
    code = Field(column_name='Code', attribute='code')
    name = Field(column_name='Area_Name', attribute='name')
    city = Field(
        column_name='City_Code',
        attribute='city',
        widget=ForeignKeyWidget(City, field='code')
    )
    state = Field(
        column_name='State_Code',
        attribute='state',
        widget=ForeignKeyWidget(State, field='code')
    )
    city_name = Field(
        column_name='City_Name',
        attribute='city',
        widget=ForeignKeyWidget(City, field='name')
    )
    state_name = Field(
        column_name='State_Name',
        attribute='state',
        widget=ForeignKeyWidget(State, field='name')
    )
    pincode = Field(column_name='Pincode', attribute='pincode')

    class Meta:
        model = Area
        fields = ('code', 'name', 'city', 'state', 'city_name', 'state_name', 'pincode')
        export_order = ('code', 'name', 'city', 'state', 'city_name', 'state_name', 'pincode')
        import_id_fields = ('code',)
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        super().before_import_row(row, **kwargs)
        city_code = (row.get('City_Code') or '').strip()
        state_code = (row.get('State_Code') or '').strip()
        if city_code and state_code:
            city = City.objects.filter(code=city_code, is_deleted=False).select_related('state').first()
            if city and city.state.code != state_code:
                from django.core.exceptions import ValidationError
                raise ValidationError(
                    f'City "{city.name}" ({city_code}) belongs to state "{city.state.name}" ({city.state.code}), '
                    f'not "{state_code}".'
                )

    def get_field_info(self):
        """Return field metadata for frontend field selection."""
        return [
            {'field_name': 'code', 'display_name': 'Code', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Optional. Leave blank to auto-generate (e.g., HYD01, BLR02)'},
            {'field_name': 'name', 'display_name': 'Area_Name', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Full area name'},
            {'field_name': 'city', 'display_name': 'City_Code', 'is_mandatory': True, 'field_type': 'FOREIGN_KEY', 'help_text': 'City code (e.g., HYD, BLR)', 'foreign_model': 'City', 'foreign_field': 'code'},
            {'field_name': 'state', 'display_name': 'State_Code', 'is_mandatory': True, 'field_type': 'FOREIGN_KEY', 'help_text': 'State code (e.g., AP, TS)', 'foreign_model': 'State', 'foreign_field': 'code'},
            {'field_name': 'pincode', 'display_name': 'Pincode', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'PIN code (optional)'},
        ]


class DistrictResource(HeaderValidationMixin, resources.ModelResource):
    """Resource for District import/export with code-based foreign key lookups."""
    code = Field(column_name='Code', attribute='code')
    name = Field(column_name='District_Name', attribute='name')
    state = Field(
        column_name='State_Code',
        attribute='state',
        widget=ForeignKeyWidget(State, field='code')
    )

    class Meta:
        model = District
        fields = ('code', 'name', 'state')
        export_order = ('code', 'name', 'state')
        import_id_fields = ('code',)
        skip_unchanged = True
        report_skipped = True

    def get_field_info(self):
        """Return field metadata for frontend field selection."""
        return [
            {'field_name': 'code', 'display_name': 'Code', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Optional. Leave blank to auto-generate'},
            {'field_name': 'name', 'display_name': 'District_Name', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Full district name'},
            {'field_name': 'state', 'display_name': 'State_Code', 'is_mandatory': True, 'field_type': 'FOREIGN_KEY', 'help_text': 'State code (e.g., AP, TS)', 'foreign_model': 'State', 'foreign_field': 'code'},
        ]


class MandalResource(HeaderValidationMixin, resources.ModelResource):
    """Resource for Mandal import/export with code-based foreign key lookups."""
    code = Field(column_name='Code', attribute='code')
    name = Field(column_name='Mandal_Name', attribute='name')
    district = Field(
        column_name='District_Code',
        attribute='district',
        widget=ForeignKeyWidget(District, field='code')
    )
    state = Field(
        column_name='State_Code',
        attribute='state',
        widget=ForeignKeyWidget(State, field='code')
    )

    class Meta:
        model = Mandal
        fields = ('code', 'name', 'district', 'state')
        export_order = ('code', 'name', 'district', 'state')
        import_id_fields = ('code',)
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        super().before_import_row(row, **kwargs)
        district_code = (row.get('District_Code') or '').strip()
        state_code = (row.get('State_Code') or '').strip()
        if district_code and state_code:
            district = District.objects.filter(code=district_code, is_deleted=False).select_related('state').first()
            if district and district.state.code != state_code:
                from django.core.exceptions import ValidationError
                raise ValidationError(
                    f'District "{district.name}" ({district_code}) belongs to state "{district.state.name}" ({district.state.code}), '
                    f'not "{state_code}".'
                )

    def get_field_info(self):
        """Return field metadata for frontend field selection."""
        return [
            {'field_name': 'code', 'display_name': 'Code', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Optional. Leave blank to auto-generate'},
            {'field_name': 'name', 'display_name': 'Mandal_Name', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Full mandal name'},
            {'field_name': 'district', 'display_name': 'District_Code', 'is_mandatory': True, 'field_type': 'FOREIGN_KEY', 'help_text': 'District code', 'foreign_model': 'District', 'foreign_field': 'code'},
            {'field_name': 'state', 'display_name': 'State_Code', 'is_mandatory': True, 'field_type': 'FOREIGN_KEY', 'help_text': 'State code (e.g., AP, TS)', 'foreign_model': 'State', 'foreign_field': 'code'},
        ]




class RouteCodeWidget(ForeignKeyWidget):
    """Resolve Route by code and create/update it from the same import row when needed."""

    @staticmethod
    def _parse_bool(value):
        if isinstance(value, bool):
            return value
        if value in [None, '']:
            return None
        return str(value).strip().upper() in ['TRUE', '1', 'YES', 'Y']

    def clean(self, value, row=None, **kwargs):
        route_code = (value or '').strip() if isinstance(value, str) else value
        if not route_code:
            raise ValueError('Route Code is required')

        route_name = ''
        if row:
            route_name = str(row.get('Route Name') or '').strip()
        is_active = self._parse_bool(row.get('Is Active') if row else None)

        route = Route.objects.filter(code__iexact=route_code, is_deleted=False).first()
        if route is None:
            if not route_name:
                raise ValueError('Route Name is required')
            route = Route(
                code=route_code,
                name=route_name,
                is_active=True if is_active is None else is_active,
            )
            route.save()
            return route

        updated = False
        if route_name and route.name != route_name:
            route.name = route_name
            updated = True
        if is_active is not None and route.is_active != is_active:
            route.is_active = is_active
            updated = True
        if updated:
            route.save()
        return route


class RouteResource(HeaderValidationMixin, resources.ModelResource):
    """Resource for Route import/export with area-level coverage rows."""
    route = Field(
        column_name='Route Code',
        attribute='route',
        widget=RouteCodeWidget(Route, field='code')
    )
    route_name = Field(column_name='Route Name', attribute='route_name')
    is_active = Field(column_name='Is Active', attribute='is_active')
    state = Field(
        column_name='State',
        attribute='state',
        widget=ForeignKeyWidget(State, field='code')
    )
    city = Field(
        column_name='City',
        attribute='city',
        widget=ForeignKeyWidget(City, field='code')
    )
    area = Field(
        column_name='Area',
        attribute='area',
        widget=ForeignKeyWidget(Area, field='code')
    )

    class Meta:
        model = RouteCoverage
        fields = ('route', 'route_name', 'is_active', 'state', 'city', 'area')
        export_order = ('route', 'route_name', 'is_active', 'state', 'city', 'area')
        import_id_fields = ('route', 'state', 'city', 'area')
        skip_unchanged = True
        report_skipped = True

    def dehydrate_route_name(self, obj):
        if not getattr(obj, 'route_id', None):
            return ''
        return obj.route.name

    def dehydrate_is_active(self, obj):
        if not getattr(obj, 'route_id', None):
            return True
        return obj.route.is_active

    def before_import_row(self, row, **kwargs):
        # Normalize booleans and trim row values.
        if 'Is Active' in row and row.get('Is Active') is not None:
            row['Is Active'] = str(row['Is Active']).strip().upper() in ['TRUE', '1', 'YES', 'Y']

        for key in ['Route Code', 'Route Name', 'State', 'City', 'Area']:
            if key in row and isinstance(row[key], str):
                row[key] = row[key].strip()

    def get_field_info(self):
        return [
            {'field_name': 'route', 'display_name': 'Route Code', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Route code (e.g., RTE-001). Required for import matching.'},
            {'field_name': 'route_name', 'display_name': 'Route Name', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Route name.'},
            {'field_name': 'is_active', 'display_name': 'Is Active', 'is_mandatory': False, 'field_type': 'BOOLEAN', 'help_text': 'TRUE/FALSE. Defaults to TRUE.'},
            {'field_name': 'state', 'display_name': 'State', 'is_mandatory': True, 'field_type': 'FOREIGN_KEY', 'help_text': 'State code (e.g., TS, KA).', 'foreign_model': 'State', 'foreign_field': 'code'},
            {'field_name': 'city', 'display_name': 'City', 'is_mandatory': True, 'field_type': 'FOREIGN_KEY', 'help_text': 'City code.', 'foreign_model': 'City', 'foreign_field': 'code'},
            {'field_name': 'area', 'display_name': 'Area', 'is_mandatory': True, 'field_type': 'FOREIGN_KEY', 'help_text': 'Area code.', 'foreign_model': 'Area', 'foreign_field': 'code'},
        ]


class LocationResource(HeaderValidationMixin, resources.ModelResource):
    """Resource for Location import/export."""
    code = Field(column_name='Code', attribute='code')
    name = Field(column_name='Location Name', attribute='name')
    companies = Field(
        column_name='Company Codes',
        attribute='companies',
        widget=ManyToManyWidget(Company, field='code', separator=',')
    )
    city = Field(
        column_name='City Code',
        attribute='city',
        widget=ForeignKeyWidget(City, field='code')
    )
    state = Field(
        column_name='State Code',
        attribute='state',
        widget=ForeignKeyWidget(State, field='code')
    )
    country = Field(
        column_name='Country Code',
        attribute='country',
        widget=ForeignKeyWidget(Country, field='code')
    )
    city_name = Field(
        column_name='City Name',
        attribute='city',
        widget=ForeignKeyWidget(City, field='name')
    )
    state_name = Field(
        column_name='State Name',
        attribute='state',
        widget=ForeignKeyWidget(State, field='name')
    )
    country_name = Field(
        column_name='Country Name',
        attribute='country',
        widget=ForeignKeyWidget(Country, field='name')
    )
    address = Field(column_name='Address', attribute='address')
    pincode = Field(column_name='Pincode', attribute='pincode')
    contact_person = Field(column_name='Contact Person', attribute='contact_person')
    phone = Field(column_name='Phone', attribute='phone')
    email = Field(column_name='Email', attribute='email')
    erp_code = Field(column_name='ERP Code', attribute='erp_code')
    erp_id = Field(column_name='ERP ID', attribute='erp_id')

    class Meta:
        model = Location
        fields = ('code', 'name', 'companies', 'city', 'city_name', 'state', 'state_name', 'country', 'country_name', 'address', 'pincode', 'contact_person', 'phone', 'email', 'erp_code', 'erp_id')
        export_order = ('code', 'name', 'companies', 'city', 'city_name', 'state', 'state_name', 'country', 'country_name', 'address', 'pincode', 'contact_person', 'phone', 'email', 'erp_code', 'erp_id')
        import_id_fields = ('code',)
        skip_unchanged = True
        report_skipped = True

    def get_field_info(self):
        """Return field metadata for frontend field selection."""
        return [
            {'field_name': 'code', 'display_name': 'Code', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Optional. Leave blank to auto-generate'},
            {'field_name': 'name', 'display_name': 'Location Name', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Full location name'},
            {'field_name': 'companies', 'display_name': 'Company Codes', 'is_mandatory': True, 'field_type': 'MANY_TO_MANY', 'help_text': 'Comma separated company codes', 'foreign_model': 'Company', 'foreign_field': 'code'},
            {'field_name': 'city', 'display_name': 'City Code', 'is_mandatory': True, 'field_type': 'FOREIGN_KEY', 'help_text': 'City code', 'foreign_model': 'City', 'foreign_field': 'code'},
            {'field_name': 'state', 'display_name': 'State Code', 'is_mandatory': True, 'field_type': 'FOREIGN_KEY', 'help_text': 'State code', 'foreign_model': 'State', 'foreign_field': 'code'},
            {'field_name': 'country', 'display_name': 'Country Code', 'is_mandatory': True, 'field_type': 'FOREIGN_KEY', 'help_text': 'Country code', 'foreign_model': 'Country', 'foreign_field': 'code'},
            {'field_name': 'address', 'display_name': 'Address', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Full address'},
            {'field_name': 'pincode', 'display_name': 'Pincode', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Postal code'},
            {'field_name': 'contact_person', 'display_name': 'Contact Person', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Contact person name'},
            {'field_name': 'phone', 'display_name': 'Phone', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Contact phone'},
            {'field_name': 'email', 'display_name': 'Email', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Contact email'},
            {'field_name': 'erp_code', 'display_name': 'ERP Code', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'ERP system code'},
            {'field_name': 'agent', 'display_name': 'Agent Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Agent code', 'foreign_model': 'Agent', 'foreign_field': 'code'},
            {'field_name': 'agent_name', 'display_name': 'Agent Name', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Agent name'},
            {'field_name': 'erp_id', 'display_name': 'ERP ID', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'ERP system ID'},
        ]


class WareHouseResource(HeaderValidationMixin, resources.ModelResource):
    """Resource for WareHouse import/export."""
    code = Field(column_name='Code', attribute='code')
    name = Field(column_name='Warehouse Name', attribute='name')
    location = Field(
        column_name='Location Code',
        attribute='location',
        widget=ForeignKeyWidget(Location, field='code')
    )
    erp_code = Field(column_name='ERP Code', attribute='erp_code')
    erp_id = Field(column_name='ERP ID', attribute='erp_id')

    class Meta:
        model = WareHouse
        fields = ('code', 'name', 'location', 'erp_code', 'erp_id')
        export_order = ('code', 'name', 'location', 'erp_code', 'erp_id')
        import_id_fields = ('code',)
        skip_unchanged = True
        report_skipped = True

    def get_field_info(self):
        """Return field metadata for frontend field selection."""
        return [
            {'field_name': 'code', 'display_name': 'Code', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Optional. Leave blank to auto-generate'},
            {'field_name': 'name', 'display_name': 'Warehouse Name', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Full warehouse name'},
            {'field_name': 'location', 'display_name': 'Location Code', 'is_mandatory': True, 'field_type': 'FOREIGN_KEY', 'help_text': 'Location code', 'foreign_model': 'Location', 'foreign_field': 'code'},
            {'field_name': 'erp_code', 'display_name': 'ERP Code', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'ERP system code'},
            {'field_name': 'agent', 'display_name': 'Agent Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Agent code', 'foreign_model': 'Agent', 'foreign_field': 'code'},
            {'field_name': 'agent_name', 'display_name': 'Agent Name', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Agent name'},
            {'field_name': 'erp_id', 'display_name': 'ERP ID', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'ERP system ID'},
        ]

class CompanyResource(HeaderValidationMixin, resources.ModelResource):
    """Resource for Company import/export."""
    code = Field(column_name='Code', attribute='code')
    name = Field(column_name='Company Name', attribute='name')
    city = Field(
        column_name='City Code',
        attribute='city',
        widget=ForeignKeyWidget(City, field='code')
    )
    state = Field(
        column_name='State Code',
        attribute='state',
        widget=ForeignKeyWidget(State, field='code')
    )
    email = Field(column_name='Email', attribute='email')
    phone = Field(column_name='Phone', attribute='phone')
    pan_number = Field(column_name='PAN Number', attribute='pan_number')
    gst_number = Field(column_name='GST Number', attribute='gst_number')

    class Meta:
        model = Company
        fields = ('code', 'name', 'city', 'state', 'email', 'phone', 'pan_number', 'gst_number')
        export_order = ('code', 'name', 'city', 'state', 'email', 'phone', 'pan_number', 'gst_number')
        import_id_fields = ('code',)
        skip_unchanged = True
        report_skipped = True

    def get_field_info(self):
        """Return field metadata for frontend field selection."""
        return [
            {'field_name': 'code', 'display_name': 'Code', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Optional. Leave blank to auto-generate'},
            {'field_name': 'name', 'display_name': 'Company Name', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Full company name'},
            {'field_name': 'city', 'display_name': 'City Code', 'is_mandatory': True, 'field_type': 'FOREIGN_KEY', 'help_text': 'City code', 'foreign_model': 'City', 'foreign_field': 'code'},
            {'field_name': 'state', 'display_name': 'State Code', 'is_mandatory': True, 'field_type': 'FOREIGN_KEY', 'help_text': 'State code', 'foreign_model': 'State', 'foreign_field': 'code'},
            {'field_name': 'email', 'display_name': 'Email', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Email address'},
            {'field_name': 'phone', 'display_name': 'Phone', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Phone number'},
            {'field_name': 'pan_number', 'display_name': 'PAN Number', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'PAN number'},
            {'field_name': 'gst_number', 'display_name': 'GST Number', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'GST number'},
        ]


class UOMResource(HeaderValidationMixin, resources.ModelResource):
    """Resource for UOM (Unit of Measurement) import/export with code-based identification."""
    code = Field(column_name='Code', attribute='code')
    name = Field(column_name='UOM Name', attribute='name')
    remarks = Field(column_name='Remarks', attribute='remarks')
    erp_code = Field(column_name='ERP Code', attribute='erp_code')
    erp_id = Field(column_name='ERP ID', attribute='erp_id')

    class Meta:
        model = UOM
        fields = ('code', 'name', 'remarks', 'erp_code', 'erp_id')
        export_order = ('code', 'name', 'remarks', 'erp_code', 'erp_id')
        import_id_fields = ('code',)
        skip_unchanged = True
        report_skipped = True

    def get_field_info(self):
        """Return field metadata for frontend field selection."""
        return [
            {'field_name': 'code', 'display_name': 'Code', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Optional. Leave blank to auto-generate (e.g., PC, KG, LTR)'},
            {'field_name': 'name', 'display_name': 'UOM Name', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Full UOM name (e.g., Pieces, Kilograms, Liters)'},
            {'field_name': 'remarks', 'display_name': 'Remarks', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Additional notes (optional)'},
            {'field_name': 'erp_code', 'display_name': 'ERP Code', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'ERP system code (optional)'},
            {'field_name': 'erp_id', 'display_name': 'ERP ID', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'ERP system ID (optional)'},
        ]


class CategoryResource(HeaderValidationMixin, resources.ModelResource):
    """Resource for Category import/export with code-based identification and parent lookup."""
    code = Field(column_name='Code', attribute='code')
    name = Field(column_name='Category Name', attribute='name')
    parent = Field(
        column_name='Parent Code',
        attribute='parent',
        widget=ForeignKeyWidget(Category, field='code')
    )
    description = Field(column_name='Description', attribute='description')
    is_active = Field(column_name='Active', attribute='is_active')
    erp_code = Field(column_name='ERP Code', attribute='erp_code')
    erp_id = Field(column_name='ERP ID', attribute='erp_id')

    class Meta:
        model = Category
        fields = ('code', 'name', 'parent', 'description', 'is_active', 'erp_code', 'erp_id')
        export_order = ('code', 'name', 'parent', 'description', 'is_active', 'erp_code', 'erp_id')
        import_id_fields = ('code',)
        skip_unchanged = True
        report_skipped = True

    def get_field_info(self):
        """Return field metadata for frontend field selection."""
        return [
            {'field_name': 'code', 'display_name': 'Code', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Optional. Leave blank to auto-generate (e.g., ELECTRONICS, FOOD)'},
            {'field_name': 'name', 'display_name': 'Category Name', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Full category name'},
            {'field_name': 'parent', 'display_name': 'Parent Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Parent category code (optional)', 'foreign_model': 'Category', 'foreign_field': 'code'},
            {'field_name': 'description', 'display_name': 'Description', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Category description (optional)'},
            {'field_name': 'is_active', 'display_name': 'Active', 'is_mandatory': False, 'field_type': 'BOOLEAN', 'help_text': 'Active status (True/False)'},
            {'field_name': 'erp_code', 'display_name': 'ERP Code', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'ERP system code (optional)'},
            {'field_name': 'erp_id', 'display_name': 'ERP ID', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'ERP system ID (optional)'},
        ]


class BrandResource(HeaderValidationMixin, resources.ModelResource):
    """Resource for Brand import/export with code-based identification."""
    code = Field(column_name='Code', attribute='code')
    name = Field(column_name='Brand Name', attribute='name')
    description = Field(column_name='Description', attribute='description')
    is_active = Field(column_name='Active', attribute='is_active')
    erp_code = Field(column_name='ERP Code', attribute='erp_code')
    erp_id = Field(column_name='ERP ID', attribute='erp_id')

    class Meta:
        model = Brand
        fields = ('code', 'name', 'description', 'is_active', 'erp_code', 'erp_id')
        export_order = ('code', 'name', 'description', 'is_active', 'erp_code', 'erp_id')
        import_id_fields = ('code',)
        skip_unchanged = True
        report_skipped = True

    def get_field_info(self):
        """Return field metadata for frontend field selection."""
        return [
            {'field_name': 'code', 'display_name': 'Code', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Optional. Leave blank to auto-generate (e.g., SAMSUNG, NIKE)'},
            {'field_name': 'name', 'display_name': 'Brand Name', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Full brand name'},
            {'field_name': 'description', 'display_name': 'Description', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Brand description (optional)'},
            {'field_name': 'is_active', 'display_name': 'Active', 'is_mandatory': False, 'field_type': 'BOOLEAN', 'help_text': 'Active status (True/False)'},
            {'field_name': 'erp_code', 'display_name': 'ERP Code', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'ERP system code (optional)'},
            {'field_name': 'erp_id', 'display_name': 'ERP ID', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'ERP system ID (optional)'},
        ]


class TaxResource(HeaderValidationMixin, resources.ModelResource):
    """Resource for Tax import/export with code-based identification."""
    code = Field(column_name='Code', attribute='code')
    name = Field(column_name='Tax Name', attribute='name')
    tax_type = Field(column_name='Tax Type', attribute='tax_type')
    tax_rate = Field(column_name='Tax Rate', attribute='tax_rate')
    description = Field(column_name='Description', attribute='description')
    is_active = Field(column_name='Active', attribute='is_active')

    class Meta:
        model = Tax
        fields = ('code', 'name', 'tax_type', 'tax_rate', 'description', 'is_active')
        export_order = ('code', 'name', 'tax_type', 'tax_rate', 'description', 'is_active')
        import_id_fields = ('code',)
        skip_unchanged = True
        report_skipped = True

    def get_field_info(self):
        """Return field metadata for frontend field selection."""
        return [
            {'field_name': 'code', 'display_name': 'Code', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Optional. Leave blank to auto-generate (e.g., GST18, IGST12)'},
            {'field_name': 'name', 'display_name': 'Tax Name', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Full tax name'},
            {'field_name': 'tax_type', 'display_name': 'Tax Type', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Tax type (e.g., GST, IGST, CGST+SGST)'},
            {'field_name': 'tax_rate', 'display_name': 'Tax Rate', 'is_mandatory': True, 'field_type': 'DECIMAL', 'help_text': 'Tax percentage (e.g., 18.00)'},
            {'field_name': 'description', 'display_name': 'Description', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Tax description (optional)'},
            {'field_name': 'is_active', 'display_name': 'Active', 'is_mandatory': False, 'field_type': 'BOOLEAN', 'help_text': 'Active status (True/False)'},
        ]


class ItemResource(HeaderValidationMixin, resources.ModelResource):
    """Resource for Item import/export with code-based identification."""
    # Basic Information
    code = Field(column_name='Code', attribute='code')
    name = Field(column_name='Product Name', attribute='name')
    short_name = Field(column_name='Short Name', attribute='short_name')
    description = Field(column_name='Description', attribute='description')
    barcode = Field(column_name='Barcode', attribute='barcode')
    sku = Field(column_name='SKU', attribute='sku')
    company = Field(
        column_name='Company Code',
        attribute='company',
        widget=ForeignKeyWidget(Company, field='code')
    )
    company_name = Field(
        column_name='Company Name',
        attribute='company',
        widget=ForeignKeyWidget(Company, field='name')
    )
    
    # Classification
    item_type = Field(column_name='Item Type', attribute='item_type', widget=IntegerWidget())
    product_type = Field(column_name='Product Type', attribute='product_type', widget=IntegerWidget())
    category = Field(
        column_name='Category Code',
        attribute='category',
        widget=ForeignKeyWidget(Category, field='code')
    )
    category_name = Field(
        column_name='Category Name',
        attribute='category',
        widget=ForeignKeyWidget(Category, field='name')
    )
    brand = Field(
        column_name='Brand Code',
        attribute='brand',
        widget=ForeignKeyWidget(Brand, field='code')
    )
    brand_name = Field(
        column_name='Brand Name',
        attribute='brand',
        widget=ForeignKeyWidget(Brand, field='name')
    )
    bag_weight = Field(column_name='Bag Weight', attribute='bag_weight')
    
    # Unit of Measurement
    base_uom = Field(
        column_name='Base UOM Code',
        attribute='base_uom',
        widget=ForeignKeyWidget(UOM, field='code')
    )
    base_uom_name = Field(
        column_name='Base UOM Name',
        attribute='base_uom',
        widget=ForeignKeyWidget(UOM, field='name')
    )
    
    # Tax & Legal
    hsn_code = Field(column_name='HSN Code', attribute='hsn_code')
    sac_code = Field(column_name='SAC Code', attribute='sac_code')
    
    # Supplier & Manufacturer
    manufacturer = Field(column_name='Manufacturer', attribute='manufacturer')
    
    # Pricing
    mrp = Field(column_name='MRP', attribute='mrp')
    selling_price = Field(column_name='Selling Price', attribute='selling_price')
    cost_price = Field(column_name='Cost Price', attribute='cost_price')
    min_price = Field(column_name='Min Price', attribute='min_price')
    price_includes_tax = Field(column_name='Price Includes Tax', attribute='price_includes_tax')
    
    # Inventory & Stock
    is_stockable = Field(column_name='Stockable', attribute='is_stockable')
    track_inventory = Field(column_name='Track Inventory', attribute='track_inventory')
    allow_negative_stock = Field(column_name='Allow Negative Stock', attribute='allow_negative_stock')
    min_stock_level = Field(column_name='Min Stock Level', attribute='min_stock_level')
    max_stock_level = Field(column_name='Max Stock Level', attribute='max_stock_level')
    reorder_level = Field(column_name='Reorder Level', attribute='reorder_level')
    reorder_quantity = Field(column_name='Reorder Quantity', attribute='reorder_quantity')
    
    # Product Specifications
    weight = Field(column_name='Weight', attribute='weight')
    weight_unit = Field(column_name='Weight Unit', attribute='weight_unit')
    
    # Business Flags
    is_active = Field(column_name='Active', attribute='is_active')
    is_saleable = Field(column_name='Saleable', attribute='is_saleable')
    is_purchasable = Field(column_name='Purchasable', attribute='is_purchasable')
    is_featured = Field(column_name='Featured', attribute='is_featured')
    allow_discount = Field(column_name='Allow Discount', attribute='allow_discount')
    
    # ERP Integration
    erp_code = Field(column_name='ERP Code', attribute='erp_code')
    erp_id = Field(column_name='ERP ID', attribute='erp_id')
    sync_with_erp = Field(column_name='Sync With ERP', attribute='sync_with_erp')

    class Meta:
        model = Item
        fields = ('code', 'name', 'short_name', 'description', 'barcode', 'sku', 'company','company_name',
                 'item_type', 'product_type', 'category', 'category_name', 'brand', 'brand_name', 'bag_weight', 'base_uom', 'base_uom_name',
                 'hsn_code', 'sac_code', 'manufacturer',
                 'mrp', 'selling_price', 'cost_price', 'min_price', 'price_includes_tax',
                 'is_stockable', 'track_inventory', 'allow_negative_stock',
                 'min_stock_level', 'max_stock_level', 'reorder_level', 'reorder_quantity',
                 'weight', 'weight_unit',
                 'is_active', 'is_saleable', 'is_purchasable', 'is_featured', 'allow_discount',
                 'erp_code', 'erp_id', 'sync_with_erp')
        export_order = ('code', 'name', 'short_name', 'description', 'barcode', 'sku', 'company','company_name',
                       'item_type', 'product_type', 'category', 'category_name', 'brand', 'brand_name', 'bag_weight', 'base_uom', 'base_uom_name',
                       'hsn_code', 'sac_code', 'manufacturer',
                       'mrp', 'selling_price', 'cost_price', 'min_price', 'price_includes_tax',
                       'is_stockable', 'track_inventory', 'allow_negative_stock',
                       'min_stock_level', 'max_stock_level', 'reorder_level', 'reorder_quantity',
                       'weight', 'weight_unit',
                       'is_active', 'is_saleable', 'is_purchasable', 'is_featured', 'allow_discount',
                       'erp_code', 'erp_id', 'sync_with_erp')
        import_id_fields = ('code',)
        skip_unchanged = True
        report_skipped = True



    def import_field(self, field, obj, data, is_m2m=False, **kwargs):
        """
        Override to:
        1. Skip fields whose column is not in the uploaded CSV.
        2. For code/name pairs sharing the same attribute, skip the empty
           one so it doesn't overwrite the value set by its counterpart.
        """
        if not field.attribute or field.column_name not in data:
            return

        # Skip columns not present in the actual CSV file
        if not hasattr(self, '_import_headers'):
            self._import_headers = []
        if field.column_name not in self._import_headers:
            return

        raw_value = data.get(field.column_name)
        has_value = raw_value is not None and str(raw_value).strip() != ''

        if not has_value:
            # Track which attributes already got a real value
            if not hasattr(self, '_set_attributes'):
                self._set_attributes = set()
            if field.attribute in self._set_attributes:
                return  # Another field (code or name) already set this
            # For existing records, don't blank out optional fields
            if obj.pk:
                try:
                    model_field = obj._meta.get_field(field.attribute)
                    if model_field.blank or model_field.null:
                        return
                except Exception:
                    return
            return

        # Has a value — let the library do the proper widget.clean + setattr
        if not hasattr(self, '_set_attributes'):
            self._set_attributes = set()
        self._set_attributes.add(field.attribute)
        field.save(obj, data, is_m2m, **kwargs)

    def import_obj(self, obj, data, dry_run, **kwargs):
        """Reset per-row tracking, then delegate to the library's import_obj."""
        self._set_attributes = set()
        super().import_obj(obj, data, dry_run, **kwargs)
    


    def before_import(self, dataset, using_transactions=None, dry_run=None, **kwargs):
        self._import_headers = list(dataset.headers)
        self._csv_headers = list(dataset.headers)
        return super().before_import(dataset, **kwargs)
    
    def get_or_init_instance(self, instance_loader, row):
        """
        Get or initialize instance and capture tax_code from row for preview
        """
        result = super().get_or_init_instance(instance_loader, row)
        instance, is_new = result
        

        
        return result

    def get_field_info(self):
        """Return field metadata for frontend field selection."""
        return [
            # Basic Information
            {'field_name': 'code', 'display_name': 'Code', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Optional. Leave blank to auto-generate a unique item code'},
            {'field_name': 'name', 'display_name': 'Product Name', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Full product name'},
            {'field_name': 'short_name', 'display_name': 'Short Name', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Short name (optional)'},
            {'field_name': 'description', 'display_name': 'Description', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Item description'},
            {'field_name': 'barcode', 'display_name': 'Barcode', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Barcode'},
            {'field_name': 'sku', 'display_name': 'SKU', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Stock Keeping Unit'},
            {'field_name': 'company', 'display_name': 'Company Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Company code', 'foreign_model': 'Company', 'foreign_field': 'code'},
            {'field_name': 'company_name', 'display_name': 'Company Name', 'is_mandatory': True, 'field_type': 'FOREIGN_KEY', 'help_text': 'Company name (alternative to code)', 'foreign_model': 'Company', 'foreign_field': 'name'},
            
            # Classification
            {'field_name': 'item_type', 'display_name': 'Product Type', 'is_mandatory': True, 'field_type': 'NUMBER', 'help_text': '1=Material, 2=Service'},
            {'field_name': 'product_type', 'display_name': 'Product Type', 'is_mandatory': True, 'field_type': 'NUMBER', 'help_text': '1=Group, 2=Product'},
            {'field_name': 'category', 'display_name': 'Category Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Category code', 'foreign_model': 'Category', 'foreign_field': 'code'},
            {'field_name': 'category_name', 'display_name': 'Category Name', 'is_mandatory': True, 'field_type': 'FOREIGN_KEY', 'help_text': 'Category name (alternative to code)', 'foreign_model': 'Category', 'foreign_field': 'name'},
            {'field_name': 'brand', 'display_name': 'Brand Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Brand code', 'foreign_model': 'Brand', 'foreign_field': 'code'},
            {'field_name': 'brand_name', 'display_name': 'Brand Name', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Brand name (alternative to code)', 'foreign_model': 'Brand', 'foreign_field': 'name'},
            {'field_name': 'bag_weight', 'display_name': 'Bag Weight', 'is_mandatory': False, 'field_type': 'DECIMAL', 'help_text': 'Bag weight in KG'},
            {'field_name': 'base_uom', 'display_name': 'Base UOM Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Base UOM code', 'foreign_model': 'UOM', 'foreign_field': 'code'},
            {'field_name': 'base_uom_name', 'display_name': 'Base UOM Name', 'is_mandatory': True, 'field_type': 'FOREIGN_KEY', 'help_text': 'Base UOM name (alternative to code)', 'foreign_model': 'UOM', 'foreign_field': 'name'},
            
            # Tax & Legal
            {'field_name': 'hsn_code', 'display_name': 'HSN Code', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'HSN code'},
            {'field_name': 'sac_code', 'display_name': 'SAC Code', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'SAC code'},

            {'field_name': 'manufacturer', 'display_name': 'Manufacturer', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Manufacturer name'},
            
            # Pricing
            {'field_name': 'mrp', 'display_name': 'MRP', 'is_mandatory': False, 'field_type': 'DECIMAL', 'help_text': 'Maximum Retail Price'},
            {'field_name': 'selling_price', 'display_name': 'Selling Price', 'is_mandatory': False, 'field_type': 'DECIMAL', 'help_text': 'Selling price'},
            {'field_name': 'cost_price', 'display_name': 'Cost Price', 'is_mandatory': False, 'field_type': 'DECIMAL', 'help_text': 'Cost/Purchase price'},
            {'field_name': 'min_price', 'display_name': 'Min Price', 'is_mandatory': False, 'field_type': 'DECIMAL', 'help_text': 'Minimum selling price'},
            {'field_name': 'price_includes_tax', 'display_name': 'Price Includes Tax', 'is_mandatory': False, 'field_type': 'BOOLEAN', 'help_text': 'True/False'},
            
            # Inventory & Stock
            {'field_name': 'is_stockable', 'display_name': 'Stockable', 'is_mandatory': False, 'field_type': 'BOOLEAN', 'help_text': 'True/False'},
            {'field_name': 'track_inventory', 'display_name': 'Track Inventory', 'is_mandatory': False, 'field_type': 'BOOLEAN', 'help_text': 'True/False'},
            {'field_name': 'allow_negative_stock', 'display_name': 'Allow Negative Stock', 'is_mandatory': False, 'field_type': 'BOOLEAN', 'help_text': 'True/False'},
            {'field_name': 'min_stock_level', 'display_name': 'Min Stock Level', 'is_mandatory': False, 'field_type': 'DECIMAL', 'help_text': 'Minimum stock level'},
            {'field_name': 'max_stock_level', 'display_name': 'Max Stock Level', 'is_mandatory': False, 'field_type': 'DECIMAL', 'help_text': 'Maximum stock level'},
            {'field_name': 'reorder_level', 'display_name': 'Reorder Level', 'is_mandatory': False, 'field_type': 'DECIMAL', 'help_text': 'Reorder point'},
            {'field_name': 'reorder_quantity', 'display_name': 'Reorder Quantity', 'is_mandatory': False, 'field_type': 'DECIMAL', 'help_text': 'Reorder quantity'},
            
            # Product Specifications
            {'field_name': 'weight', 'display_name': 'Weight', 'is_mandatory': False, 'field_type': 'DECIMAL', 'help_text': 'Product weight'},
            {'field_name': 'weight_unit', 'display_name': 'Weight Unit', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'kg, g, lbs, oz'},
            
            # Business Flags
            {'field_name': 'is_active', 'display_name': 'Active', 'is_mandatory': False, 'field_type': 'BOOLEAN', 'help_text': 'True/False'},
            {'field_name': 'is_saleable', 'display_name': 'Saleable', 'is_mandatory': False, 'field_type': 'BOOLEAN', 'help_text': 'True/False'},
            {'field_name': 'is_purchasable', 'display_name': 'Purchasable', 'is_mandatory': False, 'field_type': 'BOOLEAN', 'help_text': 'True/False'},
            {'field_name': 'is_featured', 'display_name': 'Featured', 'is_mandatory': False, 'field_type': 'BOOLEAN', 'help_text': 'True/False'},
            {'field_name': 'allow_discount', 'display_name': 'Allow Discount', 'is_mandatory': False, 'field_type': 'BOOLEAN', 'help_text': 'True/False'},
            
            # ERP Integration
            {'field_name': 'erp_code', 'display_name': 'ERP Code', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'ERP system code (optional)'},
            {'field_name': 'erp_id', 'display_name': 'ERP ID', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'ERP system ID (optional)'},
            {'field_name': 'sync_with_erp', 'display_name': 'Sync With ERP', 'is_mandatory': False, 'field_type': 'BOOLEAN', 'help_text': 'True/False'},
        ]

    def before_import_row(self, row, **kwargs):
        """
        Clean and validate data before import
        """
        # Clean foreign key fields - extract code from "CODE (Name)" format
        fk_fields = ['Company Code', 'Category Code', 'Base UOM Code', 'Brand Code']
        for field in fk_fields:
            if field in row and row[field]:
                value = str(row[field]).strip()
                # Extract code before parenthesis if exists: "TDH (Tenali Double Horse)" -> "TDH"
                if '(' in value:
                    value = value.split('(')[0].strip()
                row[field] = value if value else None
        
        # Clean item_type and product_type - ensure they are single digit integers
        if 'Item Type' in row and row['Item Type']:
            try:
                # Convert to int and ensure it's a valid value
                item_type = int(float(str(row['Item Type']).strip()))
                if item_type not in [1, 2]:
                    item_type = 1  # Default to Material
                row['Item Type'] = item_type
            except (ValueError, TypeError):
                row['Item Type'] = 1
        
        if 'Product Type' in row and row['Product Type']:
            try:
                # Convert to int and ensure it's a valid value
                product_type = int(float(str(row['Product Type']).strip()))
                if product_type not in [1, 2]:
                    product_type = 2  # Default to Product
                row['Product Type'] = product_type
            except (ValueError, TypeError):
                row['Product Type'] = 2
        
        # Validate foreign key lookups and provide better error messages
        errors = []
        
        # Check Company (by code or name)
        company_code = str(row.get('Company Code') or '').strip()
        company_name = str(row.get('Company Name') or '').strip()
        if company_code and not Company.objects.filter(code=company_code, is_deleted=False).exists():
            errors.append(f"Company with code '{company_code}' does not exist")
        elif not company_code and company_name and not Company.objects.filter(name=company_name, is_deleted=False).exists():
            errors.append(f"Company with name '{company_name}' does not exist")
        
        # Check Category (by code or name)
        category_code = str(row.get('Category Code') or '').strip()
        category_name = str(row.get('Category Name') or '').strip()
        if category_code and not Category.objects.filter(code=category_code, is_deleted=False).exists():
            errors.append(f"Category with code '{category_code}' does not exist")
        elif not category_code and category_name and not Category.objects.filter(name=category_name, is_deleted=False).exists():
            errors.append(f"Category with name '{category_name}' does not exist")
        
        # Check Base UOM (by code or name)
        uom_code = str(row.get('Base UOM Code') or '').strip()
        uom_name = str(row.get('Base UOM Name') or '').strip()
        if uom_code and not UOM.objects.filter(code=uom_code, is_deleted=False).exists():
            errors.append(f"Base UOM with code '{uom_code}' does not exist")
        elif not uom_code and uom_name and not UOM.objects.filter(name=uom_name, is_deleted=False).exists():
            errors.append(f"Base UOM with name '{uom_name}' does not exist")
        
        # Check Brand (by code or name, optional)
        brand_code = str(row.get('Brand Code') or '').strip()
        brand_name = str(row.get('Brand Name') or '').strip()
        if brand_code and not Brand.objects.filter(code=brand_code, is_deleted=False).exists():
            errors.append(f"Brand with code '{brand_code}' does not exist")
        elif not brand_code and brand_name and not Brand.objects.filter(name=brand_name, is_deleted=False).exists():
            errors.append(f"Brand with name '{brand_name}' does not exist")
        
        # If there are validation errors, raise them
        if errors:
            from django.core.exceptions import ValidationError
            raise ValidationError("; ".join(errors))

    def after_save_instance(self, instance, using_transactions, dry_run):
        """
        After saving an item:
        1. Create base UOM conversion record if it doesn't exist
        2. Create ItemTaxComposition if tax is provided
        """
        if not dry_run:
            from Masters.models import ItemUOMConversion
            from django.utils import timezone
            
            # Create base UOM conversion
            base_uom_exists = ItemUOMConversion.objects.filter(
                item=instance,
                alternate_uom=instance.base_uom,
                is_deleted=False
            ).exists()
            
            if not base_uom_exists:
                ItemUOMConversion.objects.create(
                    item=instance,
                    alternate_uom=instance.base_uom,
                    conversion_factor=1.0,
                    is_default_purchase=True,
                    is_default_sales=True
                )


class ItemTaxCompositionResource(HeaderValidationMixin, resources.ModelResource):
    """Resource for ItemTaxComposition import/export"""
    item = Field(column_name='Item Code', attribute='item', widget=ForeignKeyWidget(Item, field='code'))
    tax = Field(column_name='Tax Code', attribute='tax', widget=ForeignKeyWidget(Tax, field='code'))
    composition_type = Field(column_name='Composition Type', attribute='composition_type')
    effective_from = Field(column_name='Effective From', attribute='effective_from')
    effective_to = Field(column_name='Effective To', attribute='effective_to')

    class Meta:
        model = ItemTaxComposition
        fields = ('item', 'tax', 'composition_type', 'effective_from', 'effective_to')
        export_order = ('item', 'tax', 'composition_type', 'effective_from', 'effective_to')
        import_id_fields = ('item', 'tax', 'effective_from')
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        """Validate composition type and dates"""
        from datetime import datetime
        from django.core.exceptions import ValidationError as DjangoValidationError
        
        # Clean composition type
        if 'Composition Type' in row and row['Composition Type']:
            comp_type = str(row['Composition Type']).strip().upper()
            if comp_type not in ['PRIMARY', 'CESS']:
                raise DjangoValidationError(f"Invalid composition type '{comp_type}'. Must be PRIMARY or CESS")
            row['Composition Type'] = comp_type
        else:
            row['Composition Type'] = 'PRIMARY'  # Default
        
        # Parse dates
        for date_field in ['Effective From', 'Effective To']:
            if date_field in row and row[date_field]:
                try:
                    if isinstance(row[date_field], str):
                        row[date_field] = datetime.strptime(row[date_field], '%d-%m-%Y').date()
                except ValueError:
                    raise DjangoValidationError(f"Invalid date format for {date_field}. Use DD-MM-YYYY")
        
        # Validate PRIMARY tax type
        if row.get('Composition Type') == 'PRIMARY' and 'Tax Code' in row:
            tax_code = str(row['Tax Code']).strip()
            if tax_code:
                try:
                    tax = Tax.objects.get(code=tax_code, is_deleted=False)
                    if tax.is_cess:
                        raise DjangoValidationError(f"PRIMARY composition cannot use CESS tax '{tax_code}'")
                except Tax.DoesNotExist:
                    raise DjangoValidationError(f"Tax '{tax_code}' not found")
        
        # Validate CESS tax type
        if row.get('Composition Type') == 'CESS' and 'Tax Code' in row:
            tax_code = str(row['Tax Code']).strip()
            if tax_code:
                try:
                    tax = Tax.objects.get(code=tax_code, is_deleted=False)
                    if not tax.is_cess:
                        raise DjangoValidationError(f"CESS composition must use CESS tax, '{tax_code}' is not CESS")
                except Tax.DoesNotExist:
                    raise DjangoValidationError(f"Tax '{tax_code}' not found")

    def after_save_instance(self, instance, using_transactions, dry_run):
        """Auto-close overlapping PRIMARY compositions"""
        if not dry_run and instance.composition_type == 'PRIMARY':
            from datetime import timedelta
            
            # Find overlapping PRIMARY compositions for same item
            overlapping = ItemTaxComposition.objects.filter(
                item=instance.item,
                composition_type='PRIMARY',
                effective_from__lt=instance.effective_from,
                effective_to__isnull=True,
                is_deleted=False
            ).exclude(id=instance.id)
            
            # Auto-close them
            if overlapping.exists():
                close_date = instance.effective_from - timedelta(days=1)
                for comp in overlapping:
                    if close_date >= comp.effective_from:
                        comp.effective_to = close_date
                        comp.save()

    def get_field_info(self):
        """Return field metadata for frontend field selection"""
        return [
            {'field_name': 'item', 'display_name': 'Product Code', 'is_mandatory': True, 'field_type': 'FOREIGN_KEY', 'help_text': 'Item code', 'foreign_model': 'Item', 'foreign_field': 'code'},
            {'field_name': 'tax', 'display_name': 'Tax Code', 'is_mandatory': True, 'field_type': 'FOREIGN_KEY', 'help_text': 'Tax code', 'foreign_model': 'Tax', 'foreign_field': 'code'},
            {'field_name': 'composition_type', 'display_name': 'Composition Type', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'PRIMARY or CESS (default: PRIMARY)'},
            {'field_name': 'effective_from', 'display_name': 'Effective From', 'is_mandatory': True, 'field_type': 'DATE', 'help_text': 'Date format: DD-MM-YYYY'},
            {'field_name': 'effective_to', 'display_name': 'Effective To', 'is_mandatory': False, 'field_type': 'DATE', 'help_text': 'Leave empty for ongoing (format: DD-MM-YYYY)'},
        ]
            



        report_skipped = True



# ==================== Channel Partner Resources ====================

class SuperstockistResource(HeaderValidationMixin, resources.ModelResource):
    """Resource for Superstockist import/export"""
    code = Field(column_name='Code', attribute='code')
    name = Field(column_name='Name', attribute='name')
    company = Field(column_name='Company Code', attribute='company', widget=ForeignKeyWidget(Company, field='code'))
    
    # Contact Information
    contact_person = Field(column_name='Contact Person', attribute='contact_person')
    phone = Field(column_name='Phone', attribute='phone')
    email = Field(column_name='Email', attribute='email')
    mobile = Field(column_name='Mobile', attribute='mobile')
    contact_person_2 = Field(column_name='Contact Person 2', attribute='contact_person_2')
    phone_2 = Field(column_name='Phone 2', attribute='phone_2')
    email_2 = Field(column_name='Email 2', attribute='email_2')
    mobile_2 = Field(column_name='Mobile 2', attribute='mobile_2')
    
    # Billing Address
    state = Field(column_name='Billing State Code', attribute='state', widget=ForeignKeyWidget(State, field='code'))
    city = Field(column_name='Billing City Code', attribute='city', widget=ForeignKeyWidget(City, field='code'))
    area = Field(column_name='Billing Village/Town Code', attribute='area', widget=ForeignKeyWidget(Area, field='code'))
    address = Field(column_name='Billing Address', attribute='address')
    pincode = Field(column_name='Billing Pincode', attribute='pincode')
    
    # Shipping Address
    shipping_same_as_billing = Field(column_name='Shipping Same as Billing', attribute='shipping_same_as_billing')
    shipping_state = Field(column_name='Shipping State Code', attribute='shipping_state', widget=ForeignKeyWidget(State, field='code'))
    shipping_city = Field(column_name='Shipping City Code', attribute='shipping_city', widget=ForeignKeyWidget(City, field='code'))
    shipping_area = Field(column_name='Shipping Village/Town Code', attribute='shipping_area', widget=ForeignKeyWidget(Area, field='code'))
    shipping_address = Field(column_name='Shipping Address', attribute='shipping_address')
    shipping_pincode = Field(column_name='Shipping Pincode', attribute='shipping_pincode')
    
    # Financial Information
    gstin = Field(column_name='GSTIN', attribute='gstin')
    pan = Field(column_name='PAN', attribute='pan')
    credit_limit = Field(column_name='Credit Limit', attribute='credit_limit')
    credit_days = Field(column_name='Credit Days', attribute='credit_days')
    
    # Bank Details
    aadhar = Field(column_name='Aadhar', attribute='aadhar')
    bank_account_number = Field(column_name='Bank Account Number', attribute='bank_account_number')
    bank_name = Field(column_name='Bank Name', attribute='bank_name')
    bank_branch = Field(column_name='Bank Branch', attribute='bank_branch')
    bank_ifsc = Field(column_name='Bank IFSC', attribute='bank_ifsc')
    bank_account_type = Field(column_name='Bank Account Type', attribute='bank_account_type')
    google_location = Field(column_name='Google Location', attribute='google_location')
    
    # Status
    is_active = Field(column_name='Is Active', attribute='is_active')
    effective_from = Field(column_name='Effective From', attribute='effective_from')
    effective_to = Field(column_name='Effective To', attribute='effective_to')
    erp_code = Field(column_name='ERP Code', attribute='erp_code')
    
    class Meta:
        model = Superstockist
        fields = ('code', 'name', 'company', 'contact_person', 'phone', 'email', 'mobile',
                 'contact_person_2', 'phone_2', 'email_2', 'mobile_2',
                 'state', 'city', 'area', 'address', 'pincode',
                 'shipping_same_as_billing', 'shipping_state', 'shipping_city', 'shipping_area', 
                 'shipping_address', 'shipping_pincode',
                 'gstin', 'pan', 'credit_limit', 'credit_days',
                 'aadhar', 'bank_account_number', 'bank_name', 'bank_branch', 'bank_ifsc', 'bank_account_type', 'google_location',
                 'is_active', 'effective_from', 'effective_to', 'erp_code')
        export_order = fields
        import_id_fields = ('code',)
        skip_unchanged = True
        report_skipped = True
    
    def get_field_info(self):
        """Return field metadata for frontend field selection."""
        return [
            {'field_name': 'code', 'display_name': 'Code', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Optional. Leave blank to auto-generate (e.g., SS001)'},
            {'field_name': 'name', 'display_name': 'Name', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Superstockist name'},
            {'field_name': 'company', 'display_name': 'Company Code', 'is_mandatory': True, 'field_type': 'FOREIGN_KEY', 'help_text': 'Company code', 'foreign_model': 'Company', 'foreign_field': 'code'},
            {'field_name': 'contact_person', 'display_name': 'Contact Person', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Primary contact person name'},
            {'field_name': 'phone', 'display_name': 'Phone', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Contact phone number'},
            {'field_name': 'email', 'display_name': 'Email', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Email address'},
            {'field_name': 'mobile', 'display_name': 'Mobile', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Mobile number'},
            {'field_name': 'contact_person_2', 'display_name': 'Contact Person 2', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Secondary contact person name'},
            {'field_name': 'phone_2', 'display_name': 'Phone 2', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Secondary phone number'},
            {'field_name': 'email_2', 'display_name': 'Email 2', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Secondary email address'},
            {'field_name': 'mobile_2', 'display_name': 'Mobile 2', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Secondary mobile number'},
            {'field_name': 'state', 'display_name': 'Billing State Code', 'is_mandatory': True, 'field_type': 'FOREIGN_KEY', 'help_text': 'Billing state code (e.g., AP, TS)', 'foreign_model': 'State', 'foreign_field': 'code'},
            {'field_name': 'city', 'display_name': 'Billing City Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Billing city code', 'foreign_model': 'City', 'foreign_field': 'code'},
            {'field_name': 'area', 'display_name': 'Billing Village/Town Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Billing village/town code', 'foreign_model': 'Area', 'foreign_field': 'code'},
            {'field_name': 'address', 'display_name': 'Billing Address', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Complete billing address'},
            {'field_name': 'pincode', 'display_name': 'Billing Pincode', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Billing PIN code'},
            {'field_name': 'shipping_same_as_billing', 'display_name': 'Shipping Same as Billing', 'is_mandatory': False, 'field_type': 'BOOLEAN', 'help_text': 'TRUE/FALSE - Use billing address for shipping'},
            {'field_name': 'shipping_state', 'display_name': 'Shipping State Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Shipping state code', 'foreign_model': 'State', 'foreign_field': 'code'},
            {'field_name': 'shipping_city', 'display_name': 'Shipping City Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Shipping city code', 'foreign_model': 'City', 'foreign_field': 'code'},
            {'field_name': 'shipping_area', 'display_name': 'Shipping Village/Town Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Shipping village/town code', 'foreign_model': 'Area', 'foreign_field': 'code'},
            {'field_name': 'shipping_address', 'display_name': 'Shipping Address', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Complete shipping address'},
            {'field_name': 'shipping_pincode', 'display_name': 'Shipping Pincode', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Shipping PIN code'},
            {'field_name': 'gstin', 'display_name': 'GSTIN', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': '15-character GST Identification Number'},
            {'field_name': 'pan', 'display_name': 'PAN', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': '10-character PAN number'},
            {'field_name': 'credit_limit', 'display_name': 'Credit Limit', 'is_mandatory': False, 'field_type': 'DECIMAL', 'help_text': 'Credit limit amount'},
            {'field_name': 'credit_days', 'display_name': 'Credit Days', 'is_mandatory': False, 'field_type': 'INTEGER', 'help_text': 'Credit period in days'},
            {'field_name': 'aadhar', 'display_name': 'Aadhar', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Aadhar number (12 digits)'},
            {'field_name': 'bank_account_number', 'display_name': 'Bank Account Number', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Bank account number'},
            {'field_name': 'bank_name', 'display_name': 'Bank Name', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Bank name'},
            {'field_name': 'bank_branch', 'display_name': 'Bank Branch', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Bank branch'},
            {'field_name': 'bank_ifsc', 'display_name': 'Bank IFSC', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'IFSC code (11 characters)'},
            {'field_name': 'bank_account_type', 'display_name': 'Bank Account Type', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'SAVINGS or CURRENT'},
            {'field_name': 'google_location', 'display_name': 'Google Location', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Google Maps location URL'},
            {'field_name': 'is_active', 'display_name': 'Is Active', 'is_mandatory': False, 'field_type': 'BOOLEAN', 'help_text': 'TRUE/FALSE - Active status'},
            {'field_name': 'effective_from', 'display_name': 'Effective From', 'is_mandatory': False, 'field_type': 'DATE', 'help_text': 'Effective from date (YYYY-MM-DD)'},
            {'field_name': 'effective_to', 'display_name': 'Effective To', 'is_mandatory': False, 'field_type': 'DATE', 'help_text': 'Effective to date (YYYY-MM-DD)'},
            {'field_name': 'erp_code', 'display_name': 'ERP Code', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'ERP system code'},
            {'field_name': 'agent', 'display_name': 'Agent Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Agent code', 'foreign_model': 'Agent', 'foreign_field': 'code'},
            {'field_name': 'agent_name', 'display_name': 'Agent Name', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Agent name'},
        ]


class SuperstockistLocationResource(HeaderValidationMixin, resources.ModelResource):
    """Resource for Superstockist Location mapping import/export"""
    superstockist = Field(column_name='Superstockist Code', attribute='superstockist', widget=ForeignKeyWidget(Superstockist, field='code'))
    state = Field(column_name='State Code', attribute='state', widget=ForeignKeyWidget(State, field='code'))
    city = Field(column_name='City Code', attribute='city', widget=ForeignKeyWidget(City, field='code'))
    area = Field(column_name='Area Code', attribute='area', widget=ForeignKeyWidget(Area, field='code'))
    
    class Meta:
        model = SuperstockistLocation
        fields = ('superstockist', 'state', 'city', 'area')
        export_order = fields
        import_id_fields = ('superstockist', 'state', 'city', 'area')
        skip_unchanged = True
        report_skipped = True
    
    def get_field_info(self):
        """Return field metadata for frontend field selection."""
        return [
            {'field_name': 'superstockist', 'display_name': 'Superstockist Code', 'is_mandatory': True, 'field_type': 'FOREIGN_KEY', 'help_text': 'Superstockist code (e.g., SS001)', 'foreign_model': 'Superstockist', 'foreign_field': 'code'},
            {'field_name': 'state', 'display_name': 'State Code', 'is_mandatory': True, 'field_type': 'FOREIGN_KEY', 'help_text': 'State code for coverage (e.g., AP, TS). Required.', 'foreign_model': 'State', 'foreign_field': 'code'},
            {'field_name': 'city', 'display_name': 'City Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Optional - City code for coverage. Leave empty for state-level coverage.', 'foreign_model': 'City', 'foreign_field': 'code'},
            {'field_name': 'area', 'display_name': 'Area Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Optional - Area code for coverage. Leave empty for city-level coverage.', 'foreign_model': 'Area', 'foreign_field': 'code'},
        ]


class DistributorResource(HeaderValidationMixin, resources.ModelResource):
    """Resource for Distributor import/export"""
    code = Field(column_name='Code', attribute='code')
    name = Field(column_name='Name', attribute='name')
    company = Field(column_name='Company Code', attribute='company', widget=ForeignKeyWidget(Company, field='code'))
    company_name = Field(column_name='Company Name', attribute='company', widget=ForeignKeyWidget(Company, field='name'))
    superstockist = Field(column_name='Superstockist Code', attribute='superstockist', widget=ForeignKeyWidget(Superstockist, field='code'))
    superstockist_name = Field(column_name='Superstockist Name', attribute='superstockist', widget=ForeignKeyWidget(Superstockist, field='name'))
    # Contact Information
    contact_person = Field(column_name='Contact Person', attribute='contact_person')
    phone = Field(column_name='Phone', attribute='phone')
    email = Field(column_name='Email', attribute='email')
    mobile = Field(column_name='Mobile', attribute='mobile')
    contact_person_2 = Field(column_name='Contact Person 2', attribute='contact_person_2')
    phone_2 = Field(column_name='Phone 2', attribute='phone_2')
    email_2 = Field(column_name='Email 2', attribute='email_2')
    mobile_2 = Field(column_name='Mobile 2', attribute='mobile_2')
    
    # Billing Address
    state = Field(column_name='Billing State Code', attribute='state', widget=ForeignKeyWidget(State, field='code'))
    state_name = Field(column_name='Billing State Name', attribute='state', widget=ForeignKeyWidget(State, field='name'))
    district = Field(column_name='Billing District Code', attribute='district', widget=ForeignKeyWidget(District, field='code'))
    district_name = Field(column_name='Billing District Name', attribute='district', widget=ForeignKeyWidget(District, field='name'))
    mandal = Field(column_name='Billing Mandal Code', attribute='mandal', widget=ForeignKeyWidget(Mandal, field='code'))
    mandal_name = Field(column_name='Billing Mandal Name', attribute='mandal', widget=ForeignKeyWidget(Mandal, field='name'))
    city = Field(column_name='Billing City Code', attribute='city', widget=ForeignKeyWidget(City, field='code'))
    city_name = Field(column_name='Billing City Name', attribute='city', widget=ForeignKeyWidget(City, field='name'))
    area = Field(column_name='Billing Village/Town Code', attribute='area', widget=ForeignKeyWidget(Area, field='code'))
    area_name = Field(column_name='Billing Village/Town Name', attribute='area', widget=ForeignKeyWidget(Area, field='name'))
    address = Field(column_name='Billing Address', attribute='address')
    pincode = Field(column_name='Billing Pincode', attribute='pincode')
    
    # Shipping Address
    shipping_same_as_billing = Field(column_name='Shipping Same as Billing', attribute='shipping_same_as_billing')
    shipping_state = Field(column_name='Shipping State Code', attribute='shipping_state', widget=ForeignKeyWidget(State, field='code'))
    shipping_state_name = Field(column_name='Shipping State Name', attribute='shipping_state', widget=ForeignKeyWidget(State, field='name'))
    shipping_district = Field(column_name='Shipping District Code', attribute='shipping_district', widget=ForeignKeyWidget(District, field='code'))
    shipping_district_name = Field(column_name='Shipping District Name', attribute='shipping_district', widget=ForeignKeyWidget(District, field='name'))
    shipping_mandal = Field(column_name='Shipping Mandal Code', attribute='shipping_mandal', widget=ForeignKeyWidget(Mandal, field='code'))
    shipping_mandal_name = Field(column_name='Shipping Mandal Name', attribute='shipping_mandal', widget=ForeignKeyWidget(Mandal, field='name'))
    shipping_city = Field(column_name='Shipping City Code', attribute='shipping_city', widget=ForeignKeyWidget(City, field='code'))
    shipping_city_name = Field(column_name='Shipping City Name', attribute='shipping_city', widget=ForeignKeyWidget(City, field='name'))
    shipping_area = Field(column_name='Shipping Village/Town Code', attribute='shipping_area', widget=ForeignKeyWidget(Area, field='code'))
    shipping_area_name = Field(column_name='Shipping Village/Town Name', attribute='shipping_area', widget=ForeignKeyWidget(Area, field='name'))
    shipping_address = Field(column_name='Shipping Address', attribute='shipping_address')
    shipping_pincode = Field(column_name='Shipping Pincode', attribute='shipping_pincode')
    
    # Financial Information
    gstin = Field(column_name='GSTIN', attribute='gstin')
    pan = Field(column_name='PAN', attribute='pan')
    credit_limit = Field(column_name='Credit Limit', attribute='credit_limit')
    credit_days = Field(column_name='Credit Days', attribute='credit_days')
    
    # Bank Details
    aadhar = Field(column_name='Aadhar', attribute='aadhar')
    bank_account_number = Field(column_name='Bank Account Number', attribute='bank_account_number')
    bank_name = Field(column_name='Bank Name', attribute='bank_name')
    bank_branch = Field(column_name='Bank Branch', attribute='bank_branch')
    bank_ifsc = Field(column_name='Bank IFSC', attribute='bank_ifsc')
    bank_account_type = Field(column_name='Bank Account Type', attribute='bank_account_type')
    google_location = Field(column_name='Google Location', attribute='google_location')
    
    # Status
    is_active = Field(column_name='Is Active', attribute='is_active')
    effective_from = Field(column_name='Effective From', attribute='effective_from')
    effective_to = Field(column_name='Effective To', attribute='effective_to')
    erp_code = Field(column_name='ERP Code', attribute='erp_code')
    
    agent = Field(column_name='Agent Code', attribute='agent', widget=ForeignKeyWidget(Agent, field='code'))
    agent_name = Field(column_name='Agent Name', attribute='agent', widget=ForeignKeyWidget(Agent, field='name'))
    
    # User creation fields
    user_username = Field(column_name='User Username', attribute='user_username')
    user_phone = Field(column_name='User Phone', attribute='user_phone')
    user_groups = Field(
        column_name='User Groups',
        attribute='user_groups',
        widget=ManyToManyWidget(Group, field='name', separator=',')
    )
    
    class Meta:
        model = Distributor
        fields = ('code', 'name', 'company', 'company_name', 'superstockist', 'superstockist_name', 'contact_person', 'phone', 'email', 'mobile',
                 'contact_person_2', 'phone_2', 'email_2', 'mobile_2',
                 'state', 'state_name', 'district', 'district_name', 'mandal', 'mandal_name', 'city', 'city_name', 'area', 'area_name', 'address', 'pincode',
                 'shipping_same_as_billing', 'shipping_state', 'shipping_state_name', 'shipping_district', 'shipping_district_name', 'shipping_mandal', 'shipping_mandal_name', 
                 'shipping_city', 'shipping_city_name', 'shipping_area', 'shipping_area_name', 'shipping_address', 'shipping_pincode',
                 'gstin', 'pan', 'credit_limit', 'credit_days',
                 'aadhar', 'bank_account_number', 'bank_name', 'bank_branch', 'bank_ifsc', 'bank_account_type', 'google_location',
                 'is_active', 'effective_from', 'effective_to', 'erp_code', 'agent', 'agent_name',
                 'user_username', 'user_phone', 'user_groups')
        export_order = fields
        import_id_fields = ('code',)
        skip_unchanged = True
        report_skipped = True
    
    def before_import_row(self, row, **kwargs):
        super().before_import_row(row, **kwargs)
        name = str(row.get('Name') or '').strip()
        phone = str(row.get('Phone') or row.get('Mobile') or '').strip()
        if name and not row.get('User Username'):
            row['User Username'] = name
        if phone:
            if not row.get('User Phone'):
                row['User Phone'] = phone

    def after_save_instance(self, instance, using_transactions, dry_run):
        if dry_run:
            return
        # Set password from phone if not provided
        if instance.user_username and not instance.user_password:
            instance.user_password = instance.user_phone or instance.user_username
            instance.save(update_fields=['user_password'])

    def after_import_row(self, row, row_result, **kwargs):
        if row_result.import_type not in ('new', 'update'):
            return
        try:
            instance = Distributor.objects.get(id=row_result.object_id)
            self._create_user_for_distributor(instance)
        except Distributor.DoesNotExist:
            pass

    def _create_user_for_distributor(self, distributor):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        username = (distributor.user_username or distributor.name or '').strip()
        if not username:
            return
        # If user already exists for this distributor, sync groups
        existing_user = User.objects.filter(distributor=distributor).first()
        if existing_user:
            if distributor.user_groups.exists():
                existing_user.groups.set(distributor.user_groups.all())
            return
        # Skip if username taken
        if User.objects.filter(username=username).exists():
            return
        password = (distributor.user_password or distributor.user_phone or username).strip()
        phone = (distributor.user_phone or '').strip()
        user = User(
            username=username,
            first_name=distributor.name,
            phone=phone or None,
            channel_partner_type='DISTRIBUTOR',
            has_all_companies=distributor.user_has_all_companies,
            has_all_locations=distributor.user_has_all_locations,
            device_access=distributor.user_device_access or 3,
            is_active=True,
        )
        user.set_password(password)
        user.save()
        user.distributor = distributor
        user.save(update_fields=['distributor_id'])
        if distributor.user_companies.exists():
            user.companies.set(distributor.user_companies.all())
        if distributor.user_locations.exists():
            user.locations.set(distributor.user_locations.all())
        if distributor.user_groups.exists():
            user.groups.set(distributor.user_groups.all())
    
    def get_field_info(self):
        """Return field metadata for frontend field selection."""
        return [
            {'field_name': 'code', 'display_name': 'Code', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Optional. Leave blank to auto-generate (e.g., DIST001)'},
            {'field_name': 'name', 'display_name': 'Name', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Distributor name'},
            {'field_name': 'company', 'display_name': 'Company Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Company code', 'foreign_model': 'Company', 'foreign_field': 'code'},
            {'field_name': 'company_name', 'display_name': 'Company Name', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Company name'},
            {'field_name': 'superstockist', 'display_name': 'Superstockist Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Optional - Parent superstockist code (if hierarchy enabled)', 'foreign_model': 'Superstockist', 'foreign_field': 'code'},
            {'field_name': 'superstockist_name', 'display_name': 'Superstockist Name', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Superstockist name'},
            {'field_name': 'contact_person', 'display_name': 'Contact Person', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Primary contact person name'},
            {'field_name': 'phone', 'display_name': 'Phone', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Contact phone number'},
            {'field_name': 'email', 'display_name': 'Email', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Email address'},
            {'field_name': 'mobile', 'display_name': 'Mobile', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Mobile number'},
            {'field_name': 'contact_person_2', 'display_name': 'Contact Person 2', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Secondary contact person name'},
            {'field_name': 'phone_2', 'display_name': 'Phone 2', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Secondary phone number'},
            {'field_name': 'email_2', 'display_name': 'Email 2', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Secondary email address'},
            {'field_name': 'mobile_2', 'display_name': 'Mobile 2', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Secondary mobile number'},
            {'field_name': 'state', 'display_name': 'Billing State Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Billing state code (e.g., AP, TS)', 'foreign_model': 'State', 'foreign_field': 'code'},
            {'field_name': 'state_name', 'display_name': 'Billing State Name', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Billing state name'},
            {'field_name': 'district', 'display_name': 'Billing District Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Billing district code', 'foreign_model': 'District', 'foreign_field': 'code'},
            {'field_name': 'district_name', 'display_name': 'Billing District Name', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Billing district name'},
            {'field_name': 'mandal', 'display_name': 'Billing Mandal Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Billing mandal code', 'foreign_model': 'Mandal', 'foreign_field': 'code'},
            {'field_name': 'mandal_name', 'display_name': 'Billing Mandal Name', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Billing mandal name'},
            {'field_name': 'city', 'display_name': 'Billing City Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Billing city code', 'foreign_model': 'City', 'foreign_field': 'code'},
            {'field_name': 'city_name', 'display_name': 'Billing City Name', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Billing city name'},
            {'field_name': 'area', 'display_name': 'Billing Village/Town Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Billing village/town code', 'foreign_model': 'Area', 'foreign_field': 'code'},
            {'field_name': 'area_name', 'display_name': 'Billing Village/Town Name', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Billing village/town name'},
            {'field_name': 'address', 'display_name': 'Billing Address', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Complete billing address'},
            {'field_name': 'pincode', 'display_name': 'Billing Pincode', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Billing PIN code'},
            {'field_name': 'shipping_same_as_billing', 'display_name': 'Shipping Same as Billing', 'is_mandatory': False, 'field_type': 'BOOLEAN', 'help_text': 'TRUE/FALSE - Use billing address for shipping'},
            {'field_name': 'shipping_state', 'display_name': 'Shipping State Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Shipping state code', 'foreign_model': 'State', 'foreign_field': 'code'},
            {'field_name': 'shipping_state_name', 'display_name': 'Shipping State Name', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Shipping state name'},
            {'field_name': 'shipping_district', 'display_name': 'Shipping District Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Shipping district code', 'foreign_model': 'District', 'foreign_field': 'code'},
            {'field_name': 'shipping_district_name', 'display_name': 'Shipping District Name', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Shipping district name'},
            {'field_name': 'shipping_mandal', 'display_name': 'Shipping Mandal Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Shipping mandal code', 'foreign_model': 'Mandal', 'foreign_field': 'code'},
            {'field_name': 'shipping_mandal_name', 'display_name': 'Shipping Mandal Name', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Shipping mandal name'},
            {'field_name': 'shipping_city', 'display_name': 'Shipping City Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Shipping city code', 'foreign_model': 'City', 'foreign_field': 'code'},
            {'field_name': 'shipping_city_name', 'display_name': 'Shipping City Name', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Shipping city name'},
            {'field_name': 'shipping_area', 'display_name': 'Shipping Village/Town Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Shipping Village/Town Code', 'foreign_model': 'Area', 'foreign_field': 'code'},
            {'field_name': 'shipping_area_name', 'display_name': 'Shipping Village/Town Name', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Shipping Village/Town Name'},
            {'field_name': 'shipping_address', 'display_name': 'Shipping Address', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Complete shipping address'},
            {'field_name': 'shipping_pincode', 'display_name': 'Shipping Pincode', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Shipping PIN code'},
            {'field_name': 'gstin', 'display_name': 'GSTIN', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': '15-character GST Identification Number'},
            {'field_name': 'pan', 'display_name': 'PAN', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': '10-character PAN number'},
            {'field_name': 'credit_limit', 'display_name': 'Credit Limit', 'is_mandatory': False, 'field_type': 'DECIMAL', 'help_text': 'Credit limit amount'},
            {'field_name': 'credit_days', 'display_name': 'Credit Days', 'is_mandatory': False, 'field_type': 'INTEGER', 'help_text': 'Credit period in days'},
            {'field_name': 'aadhar', 'display_name': 'Aadhar', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Aadhar number (12 digits)'},
            {'field_name': 'bank_account_number', 'display_name': 'Bank Account Number', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Bank account number'},
            {'field_name': 'bank_name', 'display_name': 'Bank Name', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Bank name'},
            {'field_name': 'bank_branch', 'display_name': 'Bank Branch', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Bank branch'},
            {'field_name': 'bank_ifsc', 'display_name': 'Bank IFSC', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'IFSC code (11 characters)'},
            {'field_name': 'bank_account_type', 'display_name': 'Bank Account Type', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'SAVINGS or CURRENT'},
            {'field_name': 'google_location', 'display_name': 'Google Location', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Google Maps location URL'},
            {'field_name': 'is_active', 'display_name': 'Is Active', 'is_mandatory': False, 'field_type': 'BOOLEAN', 'help_text': 'TRUE/FALSE - Active status'},
            {'field_name': 'effective_from', 'display_name': 'Effective From', 'is_mandatory': False, 'field_type': 'DATE', 'help_text': 'Effective from date (YYYY-MM-DD)'},
            {'field_name': 'effective_to', 'display_name': 'Effective To', 'is_mandatory': False, 'field_type': 'DATE', 'help_text': 'Effective to date (YYYY-MM-DD)'},
            {'field_name': 'erp_code', 'display_name': 'ERP Code', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'ERP system code'},
            {'field_name': 'agent', 'display_name': 'Agent Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Agent code', 'foreign_model': 'Agent', 'foreign_field': 'code'},
            {'field_name': 'agent_name', 'display_name': 'Agent Name', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Agent name'},
            {'field_name': 'user_username', 'display_name': 'User Username', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Username for auto-created user. Auto-filled from Phone if empty.'},
            {'field_name': 'user_phone', 'display_name': 'User Phone', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Phone for auto-created user. Auto-filled from Phone if empty.'},
            {'field_name': 'user_groups', 'display_name': 'User Groups', 'is_mandatory': True, 'field_type': 'MANY_TO_MANY', 'help_text': 'Comma-separated group names (e.g., Distributor,Sales)', 'foreign_model': 'Group', 'foreign_field': 'name'},
        ]


class DistributorLocationResource(HeaderValidationMixin, resources.ModelResource):
    """Resource for Distributor Location mapping import/export"""
    distributor = Field(column_name='Distributor Code', attribute='distributor', widget=ForeignKeyWidget(Distributor, field='code'))
    state = Field(column_name='State Code', attribute='state', widget=ForeignKeyWidget(State, field='code'))
    city = Field(column_name='City Code', attribute='city', widget=ForeignKeyWidget(City, field='code'))
    area = Field(column_name='Area Code', attribute='area', widget=ForeignKeyWidget(Area, field='code'))
    
    class Meta:
        model = DistributorLocation
        fields = ('distributor', 'state', 'city', 'area')
        export_order = fields
        import_id_fields = ('distributor', 'state', 'city', 'area')
        skip_unchanged = True
        report_skipped = True
    
    def get_field_info(self):
        """Return field metadata for frontend field selection."""
        return [
            {'field_name': 'distributor', 'display_name': 'Distributor Code', 'is_mandatory': True, 'field_type': 'FOREIGN_KEY', 'help_text': 'Distributor code (e.g., DIST001)', 'foreign_model': 'Distributor', 'foreign_field': 'code'},
            {'field_name': 'state', 'display_name': 'State Code', 'is_mandatory': True, 'field_type': 'FOREIGN_KEY', 'help_text': 'State code for coverage (e.g., AP, TS). Required.', 'foreign_model': 'State', 'foreign_field': 'code'},
            {'field_name': 'city', 'display_name': 'City Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Optional - City code for coverage. Leave empty for state-level coverage.', 'foreign_model': 'City', 'foreign_field': 'code'},
            {'field_name': 'area', 'display_name': 'Area Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Optional - Area code for coverage. Leave empty for city-level coverage.', 'foreign_model': 'Area', 'foreign_field': 'code'},
        ]


class RetailerResource(HeaderValidationMixin, resources.ModelResource):
    """Resource for Retailer import/export"""
    code = Field(column_name='Code', attribute='code')
    name = Field(column_name='Name', attribute='name')
    company = Field(column_name='Company Code', attribute='company', widget=ForeignKeyWidget(Company, field='code'))
    distributor = Field(column_name='Distributor Code', attribute='distributor', widget=ForeignKeyWidget(Distributor, field='code'))
    
    # Contact Information
    contact_person = Field(column_name='Contact Person', attribute='contact_person')
    phone = Field(column_name='Phone', attribute='phone')
    email = Field(column_name='Email', attribute='email')
    mobile = Field(column_name='Mobile', attribute='mobile')
    contact_person_2 = Field(column_name='Contact Person 2', attribute='contact_person_2')
    phone_2 = Field(column_name='Phone 2', attribute='phone_2')
    email_2 = Field(column_name='Email 2', attribute='email_2')
    mobile_2 = Field(column_name='Mobile 2', attribute='mobile_2')
    
    # Billing Address
    state = Field(column_name='Billing State Code', attribute='state', widget=ForeignKeyWidget(State, field='code'))
    city = Field(column_name='Billing City Code', attribute='city', widget=ForeignKeyWidget(City, field='code'))
    area = Field(column_name='Billing Village/Town Code', attribute='area', widget=ForeignKeyWidget(Area, field='code'))
    address = Field(column_name='Billing Address', attribute='address')
    pincode = Field(column_name='Billing Pincode', attribute='pincode')
    
    # Shipping Address
    shipping_same_as_billing = Field(column_name='Shipping Same as Billing', attribute='shipping_same_as_billing')
    shipping_state = Field(column_name='Shipping State Code', attribute='shipping_state', widget=ForeignKeyWidget(State, field='code'))
    shipping_city = Field(column_name='Shipping City Code', attribute='shipping_city', widget=ForeignKeyWidget(City, field='code'))
    shipping_area = Field(column_name='Shipping Village/Town Code', attribute='shipping_area', widget=ForeignKeyWidget(Area, field='code'))
    shipping_address = Field(column_name='Shipping Address', attribute='shipping_address')
    shipping_pincode = Field(column_name='Shipping Pincode', attribute='shipping_pincode')
    
    # Retailer Specific
    outlet_type = Field(column_name='Outlet Type Code', attribute='outlet_type', widget=ForeignKeyWidget(OutletType, field='code'))
    outlet_size = Field(column_name='Outlet Size', attribute='outlet_size')
    
    # Financial Information
    gstin = Field(column_name='GSTIN', attribute='gstin')
    pan = Field(column_name='PAN', attribute='pan')
    credit_limit = Field(column_name='Credit Limit', attribute='credit_limit')
    credit_days = Field(column_name='Credit Days', attribute='credit_days')
    
    # Bank Details
    aadhar = Field(column_name='Aadhar', attribute='aadhar')
    bank_account_number = Field(column_name='Bank Account Number', attribute='bank_account_number')
    bank_name = Field(column_name='Bank Name', attribute='bank_name')
    bank_branch = Field(column_name='Bank Branch', attribute='bank_branch')
    bank_ifsc = Field(column_name='Bank IFSC', attribute='bank_ifsc')
    bank_account_type = Field(column_name='Bank Account Type', attribute='bank_account_type')
    google_location = Field(column_name='Google Location', attribute='google_location')
    
    # Status
    is_active = Field(column_name='Is Active', attribute='is_active')
    effective_from = Field(column_name='Effective From', attribute='effective_from')
    effective_to = Field(column_name='Effective To', attribute='effective_to')
    erp_code = Field(column_name='ERP Code', attribute='erp_code')
    
    class Meta:
        model = Retailer
        fields = ('code', 'name', 'company', 'distributor', 'contact_person', 'phone', 'email', 'mobile',
                 'contact_person_2', 'phone_2', 'email_2', 'mobile_2',
                 'state', 'city', 'area', 'address', 'pincode',
                 'shipping_same_as_billing', 'shipping_state', 'shipping_city', 'shipping_area', 
                 'shipping_address', 'shipping_pincode',
                 'outlet_type', 'outlet_size',
                 'gstin', 'pan', 'credit_limit', 'credit_days',
                 'aadhar', 'bank_account_number', 'bank_name', 'bank_branch', 'bank_ifsc', 'bank_account_type', 'google_location',
                 'is_active', 'effective_from', 'effective_to', 'erp_code')
        export_order = fields
        import_id_fields = ('code',)
        skip_unchanged = True
        report_skipped = True
    
    def get_field_info(self):
        """Return field metadata for frontend field selection."""
        return [
            {'field_name': 'code', 'display_name': 'Code', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Optional. Leave blank to auto-generate (e.g., RET001)'},
            {'field_name': 'name', 'display_name': 'Name', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Retailer name'},
            {'field_name': 'company', 'display_name': 'Company Code', 'is_mandatory': True, 'field_type': 'FOREIGN_KEY', 'help_text': 'Company code', 'foreign_model': 'Company', 'foreign_field': 'code'},
            {'field_name': 'distributor', 'display_name': 'Distributor Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Optional - Parent distributor code (if hierarchy enabled)', 'foreign_model': 'Distributor', 'foreign_field': 'code'},
            {'field_name': 'contact_person', 'display_name': 'Contact Person', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Primary contact person name'},
            {'field_name': 'phone', 'display_name': 'Phone', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Contact phone number'},
            {'field_name': 'email', 'display_name': 'Email', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Email address'},
            {'field_name': 'mobile', 'display_name': 'Mobile', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Mobile number'},
            {'field_name': 'contact_person_2', 'display_name': 'Contact Person 2', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Secondary contact person name'},
            {'field_name': 'phone_2', 'display_name': 'Phone 2', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Secondary phone number'},
            {'field_name': 'email_2', 'display_name': 'Email 2', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Secondary email address'},
            {'field_name': 'mobile_2', 'display_name': 'Mobile 2', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Secondary mobile number'},
            {'field_name': 'state', 'display_name': 'Billing State Code', 'is_mandatory': True, 'field_type': 'FOREIGN_KEY', 'help_text': 'Billing state code (e.g., AP, TS)', 'foreign_model': 'State', 'foreign_field': 'code'},
            {'field_name': 'city', 'display_name': 'Billing City Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Billing city code', 'foreign_model': 'City', 'foreign_field': 'code'},
            {'field_name': 'area', 'display_name': 'Billing Village/Town Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Billing village/town code', 'foreign_model': 'Area', 'foreign_field': 'code'},
            {'field_name': 'address', 'display_name': 'Billing Address', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Complete billing address'},
            {'field_name': 'pincode', 'display_name': 'Billing Pincode', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Billing PIN code'},
            {'field_name': 'shipping_same_as_billing', 'display_name': 'Shipping Same as Billing', 'is_mandatory': False, 'field_type': 'BOOLEAN', 'help_text': 'TRUE/FALSE - Use billing address for shipping'},
            {'field_name': 'shipping_state', 'display_name': 'Shipping State Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Shipping state code', 'foreign_model': 'State', 'foreign_field': 'code'},
            {'field_name': 'shipping_city', 'display_name': 'Shipping City Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Shipping city code', 'foreign_model': 'City', 'foreign_field': 'code'},
            {'field_name': 'shipping_area', 'display_name': 'Shipping Village/Town Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Shipping village/town code', 'foreign_model': 'Area', 'foreign_field': 'code'},
            {'field_name': 'shipping_address', 'display_name': 'Shipping Address', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Complete shipping address'},
            {'field_name': 'shipping_pincode', 'display_name': 'Shipping Pincode', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Shipping PIN code'},
            {'field_name': 'outlet_type', 'display_name': 'Outlet Type Code', 'is_mandatory': True, 'field_type': 'FOREIGN_KEY', 'help_text': 'Outlet type code (e.g., GEN-STORE). Required.', 'foreign_model': 'OutletType', 'foreign_field': 'code'},
            {'field_name': 'outlet_size', 'display_name': 'Outlet Size', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Outlet size (e.g., Small, Medium, Large)'},
            {'field_name': 'gstin', 'display_name': 'GSTIN', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': '15-character GST Identification Number'},
            {'field_name': 'pan', 'display_name': 'PAN', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': '10-character PAN number'},
            {'field_name': 'credit_limit', 'display_name': 'Credit Limit', 'is_mandatory': False, 'field_type': 'DECIMAL', 'help_text': 'Credit limit amount'},
            {'field_name': 'credit_days', 'display_name': 'Credit Days', 'is_mandatory': False, 'field_type': 'INTEGER', 'help_text': 'Credit period in days'},
            {'field_name': 'aadhar', 'display_name': 'Aadhar', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Aadhar number (12 digits)'},
            {'field_name': 'bank_account_number', 'display_name': 'Bank Account Number', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Bank account number'},
            {'field_name': 'bank_name', 'display_name': 'Bank Name', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Bank name'},
            {'field_name': 'bank_branch', 'display_name': 'Bank Branch', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Bank branch'},
            {'field_name': 'bank_ifsc', 'display_name': 'Bank IFSC', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'IFSC code (11 characters)'},
            {'field_name': 'bank_account_type', 'display_name': 'Bank Account Type', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'SAVINGS or CURRENT'},
            {'field_name': 'google_location', 'display_name': 'Google Location', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Google Maps location URL'},
            {'field_name': 'is_active', 'display_name': 'Is Active', 'is_mandatory': False, 'field_type': 'BOOLEAN', 'help_text': 'TRUE/FALSE - Active status'},
            {'field_name': 'effective_from', 'display_name': 'Effective From', 'is_mandatory': False, 'field_type': 'DATE', 'help_text': 'Effective from date (YYYY-MM-DD)'},
            {'field_name': 'effective_to', 'display_name': 'Effective To', 'is_mandatory': False, 'field_type': 'DATE', 'help_text': 'Effective to date (YYYY-MM-DD)'},
            {'field_name': 'erp_code', 'display_name': 'ERP Code', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'ERP system code'},
            {'field_name': 'agent', 'display_name': 'Agent Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Agent code', 'foreign_model': 'Agent', 'foreign_field': 'code'},
            {'field_name': 'agent_name', 'display_name': 'Agent Name', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Agent name'},
        ]


class RetailerLocationResource(HeaderValidationMixin, resources.ModelResource):
    """Resource for Retailer Location mapping import/export"""
    retailer = Field(column_name='Retailer Code', attribute='retailer', widget=ForeignKeyWidget(Retailer, field='code'))
    state = Field(column_name='State Code', attribute='state', widget=ForeignKeyWidget(State, field='code'))
    city = Field(column_name='City Code', attribute='city', widget=ForeignKeyWidget(City, field='code'))
    area = Field(column_name='Area Code', attribute='area', widget=ForeignKeyWidget(Area, field='code'))
    
    class Meta:
        model = RetailerLocation
        fields = ('retailer', 'state', 'city', 'area')
        export_order = fields
        import_id_fields = ('retailer', 'state', 'city', 'area')
        skip_unchanged = True
        report_skipped = True
    
    def get_field_info(self):
        """Return field metadata for frontend field selection."""
        return [
            {'field_name': 'retailer', 'display_name': 'Retailer Code', 'is_mandatory': True, 'field_type': 'FOREIGN_KEY', 'help_text': 'Retailer code (e.g., RET001)', 'foreign_model': 'Retailer', 'foreign_field': 'code'},
            {'field_name': 'state', 'display_name': 'State Code', 'is_mandatory': True, 'field_type': 'FOREIGN_KEY', 'help_text': 'State code for coverage (e.g., AP, TS). Required.', 'foreign_model': 'State', 'foreign_field': 'code'},
            {'field_name': 'city', 'display_name': 'City Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Optional - City code for coverage. Leave empty for state-level coverage.', 'foreign_model': 'City', 'foreign_field': 'code'},
            {'field_name': 'area', 'display_name': 'Area Code', 'is_mandatory': False, 'field_type': 'FOREIGN_KEY', 'help_text': 'Optional - Area code for coverage. Leave empty for city-level coverage.', 'foreign_model': 'Area', 'foreign_field': 'code'},
        ]

class OutletTypeResource(HeaderValidationMixin, resources.ModelResource):
    """Resource for Country import/export with code-based identification."""
    code = Field(column_name='Code', attribute='code')
    name = Field(column_name='Country Name', attribute='name')
    erp_code = Field(column_name='ERP Code', attribute='erp_code')
    erp_id = Field(column_name='ERP ID', attribute='erp_id')

    class Meta:
        model = OutletType
        fields = ('code', 'name', 'erp_code', 'erp_id')
        export_order = ('code', 'name', 'erp_code', 'erp_id')
        import_id_fields = ('code',)  # Use code for matching existing records
        skip_unchanged = True
        report_skipped = True

    def get_field_info(self):
        """Return field metadata for frontend field selection."""
        return [
            {'field_name': 'code', 'display_name': 'Code', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Optional. Leave blank to auto-generate (e.g., IND, US, UK)'},
            {'field_name': 'name', 'display_name': 'Country Name', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Full country name'},
            {'field_name': 'erp_code', 'display_name': 'ERP Code', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'ERP Code'},
            {'field_name': 'erp_id', 'display_name': 'ERP ID', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'ERP ID'},
        ]


class AgentResource(HeaderValidationMixin, resources.ModelResource):
    """Resource for Agent import/export."""
    code = Field(column_name='Code', attribute='code')
    name = Field(column_name='Agent Name', attribute='name')
    phone = Field(column_name='Phone', attribute='phone')
    email = Field(column_name='Email', attribute='email')

    class Meta:
        model = Agent
        fields = ('code', 'name', 'phone', 'email')
        export_order = ('code', 'name', 'phone', 'email')
        import_id_fields = ('code',)
        skip_unchanged = True
        report_skipped = True

    def get_field_info(self):
        return [
            {'field_name': 'code', 'display_name': 'Code', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Optional. Leave blank to auto-generate'},
            {'field_name': 'name', 'display_name': 'Agent Name', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Agent/Broker name'},
            {'field_name': 'phone', 'display_name': 'Phone', 'is_mandatory': True, 'field_type': 'TEXT', 'help_text': 'Phone number'},
            {'field_name': 'email', 'display_name': 'Email', 'is_mandatory': False, 'field_type': 'TEXT', 'help_text': 'Email address (optional)'},
        ]


class PriceBookResource(HeaderValidationMixin, resources.ModelResource):
    """Import/Export resource for PriceBook with auto-generation of document and codes"""
    
    # Only user-provided fields (no document_number, code, location_type, price_type)
    item = Field(
        column_name='Product Name',
        attribute='item',
        widget=ForeignKeyWidget(Item, field='name')
    )
    
    # Geographic fields
    state = Field(
        column_name='State Code',
        attribute='state',
        widget=ForeignKeyWidget(State, field='code')
    )
    city = Field(
        column_name='City Code',
        attribute='city',
        widget=ForeignKeyWidget(City, field='code')
    )
    area = Field(
        column_name='Area Code',
        attribute='area',
        widget=ForeignKeyWidget(Area, field='code')
    )
    
    # Channel partner fields
    superstockist = Field(
        column_name='Superstockist Code',
        attribute='superstockist',
        widget=ForeignKeyWidget(Superstockist, field='code')
    )
    distributor = Field(
        column_name='Distributor Code',
        attribute='distributor',
        widget=ForeignKeyWidget(Distributor, field='code')
    )
    retailer = Field(
        column_name='Retailer Code',
        attribute='retailer',
        widget=ForeignKeyWidget(Retailer, field='code')
    )
    
    # Price fields
    selling_price = Field(column_name='Selling Price', attribute='selling_price')
    discount_percentage = Field(column_name='Discount %', attribute='discount_percentage')
    
    # Validity fields
    effective_from = Field(column_name='Effective From', attribute='effective_from')
    effective_to = Field(column_name='Effective To', attribute='effective_to')
    is_active = Field(column_name='Is Active', attribute='is_active')
    
    # Additional fields
    remarks = Field(column_name='Remarks', attribute='remarks')
    erp_code = Field(column_name='ERP Code', attribute='erp_code')
    erp_id = Field(column_name='ERP ID', attribute='erp_id')
    
    class Meta:
        model = PriceBook
        skip_unchanged = True
        report_skipped = True
        import_id_fields = []  # No ID fields since we're always creating new
        fields = (
            'item',
            'state', 'city', 'area',
            'superstockist', 'distributor', 'retailer',
            'selling_price', 'discount_percentage',
            'effective_from', 'effective_to', 'is_active', 'remarks',
            'erp_code', 'erp_id'
        )
    
    def before_import(self, dataset, using_transactions=None, dry_run=None, **kwargs):
        """Store actual CSV headers to filter diff_headers later"""
        # Store headers from the uploaded file
        self._csv_headers = list(dataset.headers)
        return super().before_import(dataset, **kwargs)
    
    def before_import_row(self, row, **kwargs):
        """Preprocess row data and auto-generate document number, code, location_type, price_type"""
        import datetime
        
        # Initialize import session tracking
        if not hasattr(self, '_import_session'):
            self._import_session = {
                'document_date': datetime.date.today(),
                'row_counter': 0
            }
        
        # Increment row counter
        self._import_session['row_counter'] += 1
        row_num = self._import_session['row_counter']

        # Normalize code-like fields from display values to raw codes
        def _clean_code(value):
            if value is None:
                return None
            if isinstance(value, str):
                cleaned = value.strip()
                if cleaned in ('', '-', '--', '---', 'N/A', 'NA', 'None'):
                    return None
                if '(' in cleaned:
                    cleaned = cleaned.split('(')[0].strip()
                return cleaned
            return value

        for field in [
            'Product Name', 'State Code', 'City Code', 'Area Code',
            'Superstockist Code', 'Distributor Code', 'Retailer Code'
        ]:
            if field in row:
                row[field] = _clean_code(row[field])

        # Normalize selling price -> Decimal and capture for base/mrp defaults
        from decimal import Decimal, InvalidOperation
        sp_raw = row.get('Selling Price')
        if sp_raw is not None:
            try:
                sp_val = Decimal(str(sp_raw).replace(',', '').strip())
                row['Selling Price'] = sp_val
                # Store for later defaults
                row['_computed_selling_price'] = sp_val
            except (InvalidOperation, AttributeError):
                pass

        # Parse effective_from/effective_to to YYYY-MM-DD (accept dd/mm/yy or dd/mm/yyyy)
        def _parse_date(value):
            if value in (None, '', '---', '--', '-', 'N/A', 'NA', 'None'):
                return None
            if isinstance(value, datetime.datetime):
                return value.date()
            if isinstance(value, datetime.date):
                return value
            if isinstance(value, str):
                val = value.strip().strip('"“”')
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y']:
                    try:
                        return datetime.datetime.strptime(val, fmt).date()
                    except ValueError:
                        continue
            return None

        ef_from = _parse_date(row.get('Effective From'))
        ef_to = _parse_date(row.get('Effective To'))
        if ef_from:
            row['Effective From'] = ef_from
        if ef_to:
            row['Effective To'] = ef_to
        
        # Auto-detect location_type (most specific wins).
        # If both partner + geographic columns are provided, treat as partner-scoped
        # and clear geographic columns to avoid model-level validation conflicts.
        has_partner_scope = any([
            row.get('Retailer Code'),
            row.get('Distributor Code'),
            row.get('Superstockist Code'),
        ])
        has_geographic_scope = any([
            row.get('Area Code'),
            row.get('City Code'),
            row.get('State Code'),
        ])

        if has_partner_scope and has_geographic_scope:
            row['State Code'] = None
            row['City Code'] = None
            row['Area Code'] = None

        location_type = 'BASE'  # Default
        if row.get('Retailer Code'):
            location_type = 'RETAILER'
        elif row.get('Distributor Code'):
            location_type = 'DISTRIBUTOR'
        elif row.get('Superstockist Code'):
            location_type = 'SUPERSTOCKIST'
        elif row.get('Area Code'):
            location_type = 'AREA'
        elif row.get('City Code'):
            location_type = 'CITY'
        elif row.get('State Code'):
            location_type = 'STATE'
        
        # Auto-set price_type based on location_type
        if location_type in ['STATE', 'CITY', 'AREA']:
            price_type = 'GEOGRAPHIC'
        elif location_type in ['SUPERSTOCKIST', 'DISTRIBUTOR', 'RETAILER']:
            price_type = 'CHANNEL_PARTNER'
        else:
            price_type = 'BASE'
        
        # Store computed values for after_import_row
        row['_computed_location_type'] = location_type
        row['_computed_price_type'] = price_type
        row['_computed_row_num'] = row_num
        
        # Handle boolean conversion
        if 'Is Active' in row:
            raw_is_active = row.get('Is Active')
            if raw_is_active in (None, '', '---', '--', '-', 'N/A', 'NA', 'None'):
                row['Is Active'] = None
            else:
                row['Is Active'] = str(raw_is_active).strip().upper() in ['TRUE', '1', 'YES', 'Y']
        
        # Handle empty string to None for optional fields
        optional_fields = [
            'State Code', 'City Code', 'Area Code',
            'Superstockist Code', 'Distributor Code', 'Retailer Code',
            'Effective To', 'Remarks', 'ERP Code', 'ERP ID', 'Discount %'
        ]
        for field in optional_fields:
            if field in row and not row[field]:
                row[field] = None
        
        # Default values
        if 'Discount %' in row and not row['Discount %']:
            row['Discount %'] = 0
        
        if 'Is Active' not in row or row['Is Active'] is None:
            row['Is Active'] = True
    
    def import_obj(self, obj, data, dry_run, **kwargs):
        """Set required fields before validation"""
        # Auto-set base_price and mrp from selling_price if not provided
        selling_price = getattr(obj, 'selling_price', None)
        if selling_price:
            if not getattr(obj, 'base_price', None):
                obj.base_price = selling_price
            if not getattr(obj, 'mrp', None):
                obj.mrp = selling_price
        # Fallback to computed selling price from row if obj missing
        if not selling_price and data.get('_computed_selling_price'):
            sp_val = data.get('_computed_selling_price')
            obj.selling_price = sp_val
            if not getattr(obj, 'base_price', None):
                obj.base_price = sp_val
            if not getattr(obj, 'mrp', None):
                obj.mrp = sp_val
        
        # Set company if not set
        if not getattr(obj, 'company_id', None):
            from Masters.models import Company
            company = Company.objects.filter(is_deleted=False).first()
            if company:
                obj.company = company
        
        # Set code placeholder (will be replaced in after_import_row)
        if not getattr(obj, 'code', None):
            import uuid
            obj.code = f'TEMP-{uuid.uuid4().hex[:8].upper()}'
        
        # Set price_type from computed value
        computed_price_type = data.get('_computed_price_type')
        if computed_price_type:
            obj.price_type = computed_price_type
        
        return super().import_obj(obj, data, dry_run, **kwargs)
    
    def after_import_row(self, row, row_result, **kwargs):
        """Create a separate PriceBookDocument per row and auto-close superseded prices"""
        from datetime import datetime, timedelta
        from Masters.models import PriceBookDocument, Company
        
        if row_result.import_type not in ['new', 'update'] or not hasattr(row_result, 'object_id'):
            return
        
        # Track IDs created in this import session so we never close our own entries
        if not hasattr(self, '_session_entry_ids'):
            self._session_entry_ids = set()
        self._session_entry_ids.add(row_result.object_id)
        
        try:
            price_book = PriceBook.objects.get(id=row_result.object_id)
            
            location_type = row.get('_computed_location_type', 'BASE')
            price_type = row.get('_computed_price_type', 'BASE')
            row_num = row.get('_computed_row_num', 1)
            
            price_book.price_type = price_type
            
            document_date = self._import_session['document_date']
            effective_from = row.get('Effective From')
            effective_to = row.get('Effective To')
            
            if isinstance(effective_from, str):
                effective_from = datetime.strptime(effective_from, '%Y-%m-%d').date()
            if isinstance(effective_to, str) and effective_to:
                effective_to = datetime.strptime(effective_to, '%Y-%m-%d').date()
            
            # Create a separate document for each row
            document_number = PriceBookDocument.generate_document_number()
            document = PriceBookDocument.objects.create(
                document_number=document_number,
                document_date=document_date,
                location_type=location_type,
                effective_from=effective_from,
                effective_to=effective_to,
                remarks=f'Imported from file on {document_date}',
                total_entries=1,
            )
            
            item_code = price_book.item.code if price_book.item else 'UNKNOWN'
            doc_seq = document_number.split('-')[-1]
            price_book.code = f"PB-{item_code}-{doc_seq}-{row_num:03d}"
            price_book.document = document
            
            if not price_book.company_id:
                company = Company.objects.filter(is_deleted=False).first()
                if company:
                    price_book.company = company
            
            price_book.save()
            
            # Auto-close: find ongoing prices (effective_to is NULL) for same item + scope
            if row_result.import_type == 'new' and effective_from:
                previous_day = effective_from - timedelta(days=1)
                
                close_filters = {
                    'item_id': price_book.item_id,
                    'effective_to__isnull': True,
                    'is_deleted': False,
                }
                if location_type == 'BASE':
                    close_filters.update({
                        'state__isnull': True, 'city__isnull': True, 'area__isnull': True,
                        'superstockist__isnull': True, 'distributor__isnull': True, 'retailer__isnull': True,
                    })
                else:
                    field_map = {
                        'STATE': 'state_id', 'CITY': 'city_id', 'AREA': 'area_id',
                        'SUPERSTOCKIST': 'superstockist_id', 'DISTRIBUTOR': 'distributor_id',
                        'RETAILER': 'retailer_id',
                    }
                    fk_field = field_map.get(location_type)
                    fk_value = getattr(price_book, fk_field, None) if fk_field else None
                    if fk_field and fk_value:
                        close_filters[fk_field] = fk_value
                
                superseded = PriceBook.objects.filter(**close_filters).exclude(
                    id__in=self._session_entry_ids
                )
                
                for old_entry in superseded:
                    if old_entry.effective_from < effective_from:
                        old_entry.effective_to = previous_day
                        old_entry.save(update_fields=['effective_to'])
                
                # Mark affected documents as CLOSED if all their entries now have an end date
                affected_doc_ids = set(
                    superseded.exclude(document__isnull=True).values_list('document_id', flat=True)
                )
                for doc_id in affected_doc_ids:
                    open_count = PriceBook.objects.filter(
                        document_id=doc_id, is_deleted=False, effective_to__isnull=True
                    ).count()
                    if open_count == 0:
                        PriceBookDocument.objects.filter(
                            id=doc_id, status='ACTIVE'
                        ).update(status='CLOSED')
            
        except Exception as e:
            import traceback
            traceback.print_exc()
    
    def get_field_info(self):
        """Return field information for import UI based on channel configuration"""
        from .models import ChannelPartnerConfiguration
        
        # Get active channel configuration
        try:
            config = ChannelPartnerConfiguration.objects.filter(is_active=True, is_deleted=False).first()
        except ChannelPartnerConfiguration.DoesNotExist:
            config = None
        
        # Default configuration if none exists
        enable_superstockist = config.enable_superstockist if config else False
        enable_distributor = config.enable_distributor if config else False
        enable_retailer = config.enable_retailer if config else False
        
        # Base fields (always shown)
        fields = [
            {'field_name': 'item', 'display_name': 'Product Name', 'is_mandatory': True,
             'field_type': 'FOREIGN_KEY', 'help_text': 'Product name (e.g., Rice Bran Oil 1L). Required.',
             'foreign_model': 'Item', 'foreign_field': 'name'},
            
            {'field_name': 'state', 'display_name': 'State Code', 'is_mandatory': False,
             'field_type': 'FOREIGN_KEY', 'help_text': 'State code for geographic pricing (e.g., TS). Optional - system will auto-detect location type.',
             'foreign_model': 'State', 'foreign_field': 'code'},
            
            {'field_name': 'city', 'display_name': 'City Code', 'is_mandatory': False,
             'field_type': 'FOREIGN_KEY', 'help_text': 'City code for geographic pricing (e.g., HYD). Optional - higher priority than State.',
             'foreign_model': 'City', 'foreign_field': 'code'},
            
            {'field_name': 'area', 'display_name': 'Area Code', 'is_mandatory': False,
             'field_type': 'FOREIGN_KEY', 'help_text': 'Area code for geographic pricing (e.g., AREA-001). Optional - highest priority for geographic.',
             'foreign_model': 'Area', 'foreign_field': 'code'},
        ]
        
        # Add channel partner fields only if enabled
        if enable_superstockist:
            fields.append(
                {'field_name': 'superstockist', 'display_name': 'Superstockist Code', 'is_mandatory': False,
                 'field_type': 'FOREIGN_KEY', 'help_text': 'Superstockist code for channel pricing (e.g., SS-001). Optional.',
                 'foreign_model': 'Superstockist', 'foreign_field': 'code'}
            )
        
        if enable_distributor:
            fields.append(
                {'field_name': 'distributor', 'display_name': 'Distributor Code', 'is_mandatory': False,
                 'field_type': 'FOREIGN_KEY', 'help_text': 'Distributor code for channel pricing (e.g., DIST-001). Optional.',
                 'foreign_model': 'Distributor', 'foreign_field': 'code'}
            )
        
        if enable_retailer:
            fields.append(
                {'field_name': 'retailer', 'display_name': 'Retailer Code', 'is_mandatory': False,
                 'field_type': 'FOREIGN_KEY', 'help_text': 'Retailer code for channel pricing (e.g., RET-001). Optional.',
                 'foreign_model': 'Retailer', 'foreign_field': 'code'}
            )
        
        # Add remaining common fields
        fields.extend([
            {'field_name': 'selling_price', 'display_name': 'Selling Price', 'is_mandatory': True,
             'field_type': 'DECIMAL', 'help_text': 'Selling price (e.g., 120.00). Required.'},
            
            {'field_name': 'discount_percentage', 'display_name': 'Discount %', 'is_mandatory': False,
             'field_type': 'DECIMAL', 'help_text': 'Discount percentage (0-100). Optional, defaults to 0.'},
            
            {'field_name': 'effective_from', 'display_name': 'Effective From', 'is_mandatory': True,
             'field_type': 'DATE', 'help_text': 'Price effective from date (YYYY-MM-DD). Required.'},
            
            {'field_name': 'effective_to', 'display_name': 'Effective To', 'is_mandatory': False,
             'field_type': 'DATE', 'help_text': 'Price effective to date (YYYY-MM-DD). Leave blank for ongoing/indefinite.'},
            
            {'field_name': 'is_active', 'display_name': 'Is Active', 'is_mandatory': False,
             'field_type': 'BOOLEAN', 'help_text': 'Is this price active? (TRUE/FALSE). Defaults to TRUE.'},
            
            {'field_name': 'remarks', 'display_name': 'Remarks', 'is_mandatory': False,
             'field_type': 'TEXT', 'help_text': 'Additional notes or comments about this price.'},
            
            {'field_name': 'erp_code', 'display_name': 'ERP Code', 'is_mandatory': False,
             'field_type': 'TEXT', 'help_text': 'ERP price code for integration.'},
            
            {'field_name': 'erp_id', 'display_name': 'ERP ID', 'is_mandatory': False,
             'field_type': 'TEXT', 'help_text': 'ERP price ID for integration.'},
        ])
        
        return fields


class ProjectResource(HeaderValidationMixin, resources.ModelResource):
    """Import/Export resource for Project master."""
    code = Field(column_name='Project Code', attribute='code')
    name = Field(column_name='Project Name', attribute='name')
    developer_name = Field(column_name='Developer', attribute='developer_name')
    project_type = Field(column_name='Project Type', attribute='project_type')
    approval_type = Field(column_name='Approval Type', attribute='approval_type')
    status = Field(column_name='Status', attribute='status')
    location = Field(
        column_name='Location Code',
        attribute='location',
        widget=ForeignKeyWidget(Location, 'code'),
    )
    rera_number = Field(column_name='RERA Number', attribute='rera_number')
    total_area = Field(column_name='Total Area', attribute='total_area')
    launch_date = Field(column_name='Launch Date', attribute='launch_date')
    possession_date = Field(column_name='Possession Date', attribute='possession_date')
    is_active = Field(column_name='Active', attribute='is_active')

    class Meta:
        model = Project
        fields = (
            'code', 'name', 'developer_name', 'project_type',
            'approval_type', 'status', 'location', 'rera_number',
            'total_area', 'launch_date', 'possession_date', 'is_active',
        )
        export_order = fields
        import_id_fields = ('code',)
        skip_unchanged = True
        report_skipped = True

    def get_field_info(self):
        return [
            {'field_name': 'code', 'display_name': 'Project Code', 'is_mandatory': False,
             'field_type': 'TEXT', 'help_text': 'Optional. Leave blank to auto-generate (prefix PROJ-).'},
            {'field_name': 'name', 'display_name': 'Project Name', 'is_mandatory': True,
             'field_type': 'TEXT', 'help_text': 'Project name'},
            {'field_name': 'developer_name', 'display_name': 'Developer', 'is_mandatory': False,
             'field_type': 'TEXT', 'help_text': 'Developer / builder name'},
            {'field_name': 'project_type', 'display_name': 'Project Type', 'is_mandatory': True,
             'field_type': 'CHOICE', 'help_text': 'PLOT / FLAT / VILLA / MIXED'},
            {'field_name': 'approval_type', 'display_name': 'Approval Type', 'is_mandatory': False,
             'field_type': 'CHOICE', 'help_text': 'GVMC / VMRDA / DTCP / HMDA / PANCHAYAT / PENDING / NA'},
            {'field_name': 'status', 'display_name': 'Status', 'is_mandatory': False,
             'field_type': 'CHOICE', 'help_text': 'UPCOMING / ACTIVE / COMPLETED / SOLD_OUT'},
            {'field_name': 'location', 'display_name': 'Location Code', 'is_mandatory': False,
             'field_type': 'FK', 'help_text': 'Location master code'},
            {'field_name': 'rera_number', 'display_name': 'RERA Number', 'is_mandatory': False,
             'field_type': 'TEXT'},
            {'field_name': 'total_area', 'display_name': 'Total Area', 'is_mandatory': False,
             'field_type': 'TEXT'},
            {'field_name': 'launch_date', 'display_name': 'Launch Date', 'is_mandatory': False,
             'field_type': 'DATE'},
            {'field_name': 'possession_date', 'display_name': 'Possession Date', 'is_mandatory': False,
             'field_type': 'DATE'},
            {'field_name': 'is_active', 'display_name': 'Active', 'is_mandatory': False,
             'field_type': 'BOOLEAN', 'help_text': 'TRUE / FALSE / 1 / 0'},
        ]
