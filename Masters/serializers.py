import re

from django.db import transaction
from rest_framework import serializers
from General.models import GeneralSettings
from .models import (
    Country, State, District, Mandal, City, Area, Route, RouteCoverage, Company, Location, LocationContact, WareHouse, UOM,
    Category, Brand, Tax, Item, ItemTaxComposition, ItemUOMConversion,
    ItemFieldConfiguration, OutletType, Superstockist, SuperstockistLocation, SuperstockistContact,
    Distributor, DistributorLocation, DistributorContact, Retailer, RetailerLocation, RetailerContact,
    ChannelPartnerConfiguration, PriceBook, PriceBookDocument, PriceBookHistory,
    Scheme, SchemeCondition, SchemeBenefit, SchemeApplicability, SchemeItem, SchemeHistory,
    Agent,
    Project,
)
from .validators import (
    validate_unique_name_case_insensitive,
    validate_unique_code_case_insensitive,
    validate_pan_number,
    validate_pincode,
    validate_contact_phone,
    validate_contact_email,
)


class DuplicateValidationSerializerMixin:
    """Mixin to add duplicate validation to serializers"""
    
    def validate_name(self, value):
        """Validate name for case-insensitive duplicates"""
        if value:
            return validate_unique_name_case_insensitive(
                self.Meta.model,
                value,
                instance=self.instance
            )
        return value
    
    def validate_code(self, value):
        """Validate code for case-insensitive duplicates"""
        if value:
            return validate_unique_code_case_insensitive(
                self.Meta.model,
                value,
                instance=self.instance
            )
        return value

# ==================== Mini Serializers (Must be defined first) ====================

class CountryMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ('id', 'name')


class StateMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ('id', 'name')


class CityMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ('id', 'name')


class AreaMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ('id', 'name')


class RouteMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ('id', 'name')


class CompanyMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ('id', 'name')


class LocationMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ('id', 'name')


class LocationContactSerializer(serializers.ModelSerializer):
    def validate_phone(self, value):
        try:
            return validate_contact_phone(value)
        except Exception as exc:
            raise serializers.ValidationError(str(exc))

    def validate_email(self, value):
        try:
            return validate_contact_email(value)
        except Exception as exc:
            raise serializers.ValidationError(str(exc))

    class Meta:
        model = LocationContact
        fields = ['id', 'location', 'contact_person', 'phone', 'email', 'designation', 'is_primary', 'created_on']
        read_only_fields = ['id', 'location', 'created_on']


class SuperstockistContactSerializer(serializers.ModelSerializer):
    def validate_phone(self, value):
        try:
            return validate_contact_phone(value)
        except Exception as exc:
            raise serializers.ValidationError(str(exc))

    def validate_email(self, value):
        try:
            return validate_contact_email(value)
        except Exception as exc:
            raise serializers.ValidationError(str(exc))

    class Meta:
        model = SuperstockistContact
        fields = ['id', 'superstockist', 'contact_person', 'phone', 'email', 'designation', 'is_primary', 'created_on']
        read_only_fields = ['id', 'superstockist', 'created_on']


class DistributorContactSerializer(serializers.ModelSerializer):
    contact_person = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)

    def validate_phone(self, value):
        try:
            return validate_contact_phone(value)
        except Exception as exc:
            raise serializers.ValidationError(str(exc))

    def validate_email(self, value):
        try:
            return validate_contact_email(value)
        except Exception as exc:
            raise serializers.ValidationError(str(exc))

    class Meta:
        model = DistributorContact
        fields = ['id', 'distributor', 'contact_person', 'phone', 'email', 'designation', 'is_primary', 'created_on']
        read_only_fields = ['id', 'distributor', 'created_on']


class RetailerContactSerializer(serializers.ModelSerializer):
    def validate_phone(self, value):
        try:
            return validate_contact_phone(value)
        except Exception as exc:
            raise serializers.ValidationError(str(exc))

    def validate_email(self, value):
        try:
            return validate_contact_email(value)
        except Exception as exc:
            raise serializers.ValidationError(str(exc))

    class Meta:
        model = RetailerContact
        fields = ['id', 'retailer', 'contact_person', 'phone', 'email', 'designation', 'is_primary', 'created_on']
        read_only_fields = ['id', 'retailer', 'created_on']


class WareHouseMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = WareHouse
        fields = ('id', 'name')


class UOMMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = UOM
        fields = ('id', 'name')


class CategoryMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name')


class BrandMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ('id', 'name')


class TaxMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tax
        fields = ['id', 'name', 'tax_type', 'tax_rate', 'is_cess']


class ItemMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'code', 'name', 'barcode','image']


class OutletTypeMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutletType
        fields = ['id', 'name']


class AgentMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = ('id', 'code', 'name')


class SuperstockistMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Superstockist
        fields = ('id', 'code', 'name')


class DistributorMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Distributor
        fields = ('id', 'code', 'name')


class RetailerMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Retailer
        fields = ('id', 'code', 'name')


# ==================== Full Serializers ====================

class CountrySerializer(DuplicateValidationSerializerMixin, serializers.ModelSerializer):
    code = serializers.CharField(max_length=10, required=False, allow_blank=True)
    
    class Meta:
        model = Country
        fields = ['id', 'code', 'name', 'created_on', 'modified_on']
        read_only_fields = ['id', 'created_on', 'modified_on']


class StateSerializer(DuplicateValidationSerializerMixin, serializers.ModelSerializer):
    country = CountryMiniSerializer(read_only=True)
    country_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source='country', 
        queryset=Country.objects.filter(is_deleted=False)
    )
    code = serializers.CharField(max_length=10, required=False, allow_blank=True)
    
    class Meta:
        model = State
        fields = ['id', 'code', 'name', 'gst_code', 'country', 'country_id', 'created_on', 'modified_on']
        read_only_fields = ['id', 'created_on', 'modified_on']


class DistrictSerializer(DuplicateValidationSerializerMixin, serializers.ModelSerializer):
    state = StateMiniSerializer(read_only=True)
    state_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source='state', 
        queryset=State.objects.filter(is_deleted=False)
    )
    country = CountryMiniSerializer(read_only=True, source='state.country')
    code = serializers.CharField(max_length=10, required=False, allow_blank=True, allow_null=True)
    
    class Meta:
        model = District
        fields = ['id', 'code', 'name', 'state', 'state_id', 'country', 'created_on', 'modified_on']
        read_only_fields = ['id', 'created_on', 'modified_on']


class MandalSerializer(DuplicateValidationSerializerMixin, serializers.ModelSerializer):
    district = serializers.SerializerMethodField(read_only=True)
    district_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source='district', 
        queryset=District.objects.filter(is_deleted=False)
    )
    state = StateMiniSerializer(read_only=True)
    state_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source='state', 
        queryset=State.objects.filter(is_deleted=False)
    )
    country = CountryMiniSerializer(read_only=True, source='state.country')
    code = serializers.CharField(max_length=10, required=False, allow_blank=True, allow_null=True)
    
    def get_district(self, obj):
        if obj.district:
            return {'id': obj.district.id, 'code': obj.district.code, 'name': obj.district.name}
        return None
    
    class Meta:
        model = Mandal
        fields = ['id', 'code', 'name', 'district', 'district_id', 'state', 'state_id', 'country', 'created_on', 'modified_on']
        read_only_fields = ['id', 'created_on', 'modified_on']


class CitySerializer(DuplicateValidationSerializerMixin, serializers.ModelSerializer):
    state = StateMiniSerializer(read_only=True)
    state_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source='state', 
        queryset=State.objects.filter(is_deleted=False)
    )
    country = CountryMiniSerializer(read_only=True)
    country_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source='country',
        queryset=Country.objects.filter(is_deleted=False),
        required=False, allow_null=True
    )
    district = serializers.SerializerMethodField(read_only=True)
    district_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source='district', 
        queryset=District.objects.filter(is_deleted=False),
        required=False, allow_null=True
    )
    mandal = serializers.SerializerMethodField(read_only=True)
    mandal_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source='mandal', 
        queryset=Mandal.objects.filter(is_deleted=False),
        required=False, allow_null=True
    )
    code = serializers.CharField(max_length=10, required=False, allow_blank=True, allow_null=True)
    
    def get_district(self, obj):
        if obj.district:
            return {'id': obj.district.id, 'code': obj.district.code, 'name': obj.district.name}
        return None
    
    def get_mandal(self, obj):
        if obj.mandal:
            return {'id': obj.mandal.id, 'code': obj.mandal.code, 'name': obj.mandal.name}
        return None
    
    class Meta:
        model = City
        fields = ['id', 'code', 'name', 'state', 'state_id', 'country', 'country_id', 'district', 'district_id', 'mandal', 'mandal_id', 'pincode', 'created_on', 'modified_on']
        read_only_fields = ['id', 'created_on', 'modified_on']


class AreaSerializer(DuplicateValidationSerializerMixin, serializers.ModelSerializer):
    country = CountryMiniSerializer(read_only=True)
    country_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source='country',
        queryset=Country.objects.filter(is_deleted=False)
    )
    state = StateMiniSerializer(read_only=True)
    state_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source='state', 
        queryset=State.objects.filter(is_deleted=False)
    )
    district = serializers.SerializerMethodField(read_only=True)
    district_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source='district', 
        queryset=District.objects.filter(is_deleted=False)
    )
    mandal = serializers.SerializerMethodField(read_only=True)
    mandal_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source='mandal', 
        queryset=Mandal.objects.filter(is_deleted=False)
    )
    city = CityMiniSerializer(read_only=True)
    city_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source='city', 
        queryset=City.objects.filter(is_deleted=False)
    )
    code = serializers.CharField(max_length=10, required=False, allow_blank=True, allow_null=True)
    
    def get_district(self, obj):
        if obj.district:
            return {'id': obj.district.id, 'code': obj.district.code, 'name': obj.district.name}
        return None
    
    def get_mandal(self, obj):
        if obj.mandal:
            return {'id': obj.mandal.id, 'code': obj.mandal.code, 'name': obj.mandal.name}
        return None
    
    class Meta:
        model = Area
        fields = ['id', 'code', 'name', 'country', 'country_id', 'state', 'state_id', 'district', 'district_id', 'mandal', 'mandal_id', 'city', 'city_id', 'pincode', 'created_on', 'modified_on']
        read_only_fields = ['id', 'created_on', 'modified_on']




class RouteCoverageSerializer(serializers.ModelSerializer):
    state_name = serializers.CharField(source='state.name', read_only=True)
    city_name = serializers.CharField(source='city.name', read_only=True)
    area_name = serializers.CharField(source='area.name', read_only=True)

    class Meta:
        model = RouteCoverage
        fields = ('id', 'state', 'state_name', 'city', 'city_name', 'area', 'area_name')


class RouteSerializer(DuplicateValidationSerializerMixin, serializers.ModelSerializer):
    coverages = RouteCoverageSerializer(many=True, read_only=True)
    location_summary = serializers.SerializerMethodField(read_only=True)
    location_states = serializers.ListField(child=serializers.UUIDField(), write_only=True, required=False)
    location_cities = serializers.ListField(child=serializers.UUIDField(), write_only=True, required=False)
    location_areas = serializers.ListField(child=serializers.UUIDField(), write_only=True, required=False)
    code = serializers.CharField(max_length=10, required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Route
        fields = (
            'id', 'code', 'name', 'is_active',
            'created_on', 'modified_on',
            'coverages', 'location_summary',
            'location_states', 'location_cities', 'location_areas',
        )
        read_only_fields = ('id', 'created_on', 'modified_on')

    def validate_name(self, value):
        if value:
            return value.strip()
        return value

    def validate_code(self, value):
        if value:
            return value.upper()
        return value

    def get_location_summary(self, obj):
        coverage_qs = obj.coverages.all()
        if not coverage_qs.exists():
            return None
        return {
            'states': coverage_qs.values('state').distinct().count(),
            'cities': coverage_qs.values('city').distinct().count(),
            'areas': coverage_qs.values('area').distinct().count(),
        }

    def _create_coverages(self, route, location_areas):
        seen_area_ids = set()
        for area_id in location_areas:
            if str(area_id) in seen_area_ids:
                continue
            seen_area_ids.add(str(area_id))
            area = Area.objects.get(pk=area_id)
            conflict_qs = RouteCoverage.objects.filter(
                route__name__iexact=route.name,
                state_id=area.state_id,
                city_id=area.city_id,
                route__is_deleted=False,
            ).exclude(route_id=route.id)
            if conflict_qs.exists():
                raise serializers.ValidationError({
                    'name': (
                        f'Route name "{route.name}" already exists for '
                        f'{area.state.name} - {area.city.name}.'
                    )
                })
            RouteCoverage.objects.create(
                route=route,
                state_id=area.state_id,
                city_id=area.city_id,
                area_id=area.id,
            )

    def create(self, validated_data):
        validated_data.pop('location_states', [])
        validated_data.pop('location_cities', [])
        location_areas = validated_data.pop('location_areas', [])

        if not location_areas:
            raise serializers.ValidationError({'location_areas': 'At least one coverage area must be selected'})

        route = Route.objects.create(**validated_data)
        self._create_coverages(route, location_areas)
        return route

    def update(self, instance, validated_data):
        validated_data.pop('location_states', None)
        validated_data.pop('location_cities', None)
        location_areas = validated_data.pop('location_areas', None)

        if location_areas is not None and not location_areas:
            raise serializers.ValidationError({'location_areas': 'At least one coverage area must be selected'})

        # Route must always end up with at least one area after update.
        if location_areas is None and not instance.coverages.exists():
            raise serializers.ValidationError({'location_areas': 'At least one coverage area must be selected'})

        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if location_areas is not None:
                instance.coverages.all().delete()
                self._create_coverages(instance, location_areas)
        return instance


class CompanySerializer(DuplicateValidationSerializerMixin, serializers.ModelSerializer):
    state = StateMiniSerializer(read_only=True)
    state_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source='state', 
        queryset=State.objects.filter(is_deleted=False)
    )
    city = CityMiniSerializer(read_only=True)
    city_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source='city', 
        queryset=City.objects.filter(is_deleted=False)
    )
    
    class Meta:
        model = Company
        fields = [
            'id', 'code', 'name', 'email', 'phone',
            'address', 'state', 'state_id', 'city', 'city_id',
            'pan_number', 'gst_number', 'logo',
            'created_on', 'modified_on'
        ]
        read_only_fields = ['id', 'created_on', 'modified_on']
    
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
    
    def validate_gst_number(self, value):
        if value:
            import re
            value = value.upper().strip()
            if not re.match(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$', value):
                raise serializers.ValidationError("Invalid GST number format.")
        return value


class LocationSerializer(serializers.ModelSerializer):
    company = serializers.SerializerMethodField(read_only=True)
    companies = CompanyMiniSerializer(many=True, read_only=True)
    company_ids = serializers.PrimaryKeyRelatedField(
        write_only=True,
        source='companies',
        many=True,
        queryset=Company.objects.filter(is_deleted=False),
        required=True,
        allow_empty=False,
    )
    city = CityMiniSerializer(read_only=True)
    city_id = serializers.PrimaryKeyRelatedField(write_only=True, source='city', queryset=City.objects.filter(is_deleted=False))
    state = StateMiniSerializer(read_only=True)
    state_id = serializers.PrimaryKeyRelatedField(write_only=True, source='state', queryset=State.objects.filter(is_deleted=False))
    country = CountryMiniSerializer(read_only=True)
    country_id = serializers.PrimaryKeyRelatedField(write_only=True, source='country', queryset=Country.objects.filter(is_deleted=False))
    contacts = LocationContactSerializer(many=True, read_only=True)
    
    class Meta:
        model = Location
        fields = [
            'id', 'code', 'name', 'company', 'companies', 'company_ids', 'city', 'city_id',
            'state', 'state_id', 'country', 'country_id', 'address', 'pincode',
            'erp_code', 'erp_id', 'contacts', 'created_on', 'modified_on'
        ]
        read_only_fields = ['id', 'created_on', 'modified_on']

    def get_company(self, obj):
        company = obj.companies.filter(is_deleted=False).first()
        if not company:
            return None
        return CompanyMiniSerializer(company).data

    def validate(self, attrs):
        # Enforce at least one mapped company for location create/update.
        companies = attrs.get('companies')
        if companies is None and self.instance:
            companies = self.instance.companies.all()

        if not companies:
            raise serializers.ValidationError({'company_ids': 'At least one company is required.'})
        return attrs


class WareHouseSerializer(DuplicateValidationSerializerMixin, serializers.ModelSerializer):
    location = LocationMiniSerializer(read_only=True)
    location_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source='location', 
        queryset=Location.objects.filter(is_deleted=False)
    )
    
    class Meta:
        model = WareHouse
        fields = [
            'id', 'code', 'name', 'location', 'location_id',
            'erp_code', 'erp_id', 'created_on', 'modified_on'
        ]
        read_only_fields = ['id', 'created_on', 'modified_on']


class UOMSerializer(DuplicateValidationSerializerMixin, serializers.ModelSerializer):
    code = serializers.CharField(max_length=10, required=False, allow_blank=True)
    
    class Meta:
        model = UOM
        fields = ['id', 'code', 'name', 'remarks', 'erp_code', 'erp_id', 'created_on', 'modified_on']
        read_only_fields = ['id', 'created_on', 'modified_on']


class CategorySerializer(DuplicateValidationSerializerMixin, serializers.ModelSerializer):
    parent = CategoryMiniSerializer(read_only=True)
    parent_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source='parent', 
        queryset=Category.objects.filter(is_deleted=False, is_active=True),
        required=False, allow_null=True
    )
    
    class Meta:
        model = Category
        fields = [
            'id', 'code', 'name', 'description', 'parent', 'parent_id', 
            'is_active', 'erp_code', 'erp_id', 'created_on', 'modified_on'
        ]
        read_only_fields = ['id', 'created_on', 'modified_on']


class BrandSerializer(DuplicateValidationSerializerMixin, serializers.ModelSerializer):
    code = serializers.CharField(max_length=30, required=False, allow_blank=True)
    
    class Meta:
        model = Brand
        fields = [
            'id', 'code', 'name', 'description', 'is_active',
            'erp_code', 'erp_id', 'created_on', 'modified_on'
        ]
        read_only_fields = ['id', 'created_on', 'modified_on']


class TaxSerializer(DuplicateValidationSerializerMixin, serializers.ModelSerializer):
    code = serializers.CharField(max_length=30, required=False, allow_blank=True)
    
    class Meta:
        model = Tax
        fields = [
            'id', 'code', 'name', 'tax_type', 'tax_rate', 'is_cess', 'is_active',
            'description', 'created_on', 'modified_on'
        ]
        read_only_fields = ['id', 'created_on', 'modified_on']


class ItemTaxCompositionSerializer(serializers.ModelSerializer):
    """Serializer for Item Tax Composition (PRIMARY GST + CESS)"""
    tax = TaxMiniSerializer(read_only=True)
    tax_id = serializers.PrimaryKeyRelatedField(
        queryset=Tax.objects.all(),
        source='tax',
        write_only=True
    )
    item_name = serializers.CharField(source='item.name', read_only=True)
    composition_type_display = serializers.CharField(
        source='get_composition_type_display',
        read_only=True
    )
    
    class Meta:
        model = ItemTaxComposition
        fields = [
            'id', 'item', 'item_name',
            'tax', 'tax_id',
            'composition_type', 'composition_type_display',
            'effective_from', 'effective_to',
            'created_on', 'modified_on'
        ]
        read_only_fields = ['created_on', 'modified_on']
    
    def validate(self, attrs):
        """Validate ItemTaxComposition business rules"""
        # Call model's clean method for validation
        instance = ItemTaxComposition(**attrs)
        instance.clean()
        return attrs


class ItemTaxCompositionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating ItemTaxComposition (write operations)"""
    
    class Meta:
        model = ItemTaxComposition
        fields = [
            'id', 'item', 'tax',
            'composition_type',
            'effective_from', 'effective_to'
        ]
    
    def validate(self, attrs):
        """Validate ItemTaxComposition business rules"""
        instance = ItemTaxComposition(**attrs)
        instance.clean()
        return attrs


class OutletTypeSerializer(DuplicateValidationSerializerMixin, serializers.ModelSerializer):
    code = serializers.CharField(max_length=30, required=False, allow_blank=True)
    
    class Meta:
        model = OutletType
        fields = ['id', 'code', 'name', 'erp_code', 'erp_id', 'created_on', 'modified_on']
        read_only_fields = ['id', 'created_on', 'modified_on']


class AgentSerializer(DuplicateValidationSerializerMixin, serializers.ModelSerializer):
    code = serializers.CharField(max_length=30, required=False, allow_blank=True)

    class Meta:
        model = Agent
        fields = ['id', 'code', 'name', 'phone', 'email', 'is_active', 'created_on', 'modified_on']
        read_only_fields = ['id', 'created_on', 'modified_on']

    def validate_phone(self, value):
        if value:
            return validate_contact_phone(value)
        return value

    def validate_email(self, value):
        if value:
            return validate_contact_email(value)
        return value


# Item Attribute Serializers

class ItemUOMConversionSerializer(serializers.ModelSerializer):
    alternate_uom_name = serializers.CharField(source='alternate_uom.name', read_only=True)
    base_uom_name = serializers.CharField(source='item.base_uom.name', read_only=True)
    
    class Meta:
        model = ItemUOMConversion
        fields = [
            'id', 'item', 'alternate_uom', 'alternate_uom_name', 'base_uom_name',
            'conversion_factor', 'is_default_purchase', 'is_default_sales', 'barcode',
            'created_on'
        ]
        read_only_fields = ['created_on']


class ItemListSerializer(serializers.ModelSerializer):
    """Optimized serializer for item list view - excludes heavy fields like images"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    base_uom_name = serializers.CharField(source='base_uom.name', read_only=True)
    base_uom_code = serializers.CharField(source='base_uom.code', read_only=True)
    item_type_display = serializers.CharField(source='get_item_type_display', read_only=True)
    
    class Meta:
        model = Item
        fields = [
            'id', 'code', 'name', 'company', 'company_name', 'bag_weight',
            'item_type', 'item_type_display',
            'category', 'category_name', 'brand', 'brand_name',
            'base_uom_name', 'base_uom_code', 'hsn_code', 'mrp', 'selling_price',
            'is_active', 'is_saleable', 'created_on'
        ]


class ItemSerializer(DuplicateValidationSerializerMixin, serializers.ModelSerializer):
    # Read-only nested objects
    company_name = serializers.CharField(source='company.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    base_uom_name = serializers.CharField(source='base_uom.name', read_only=True)
    base_uom_code = serializers.CharField(source='base_uom.code', read_only=True)
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    

    
    # Current tax
    current_tax = serializers.SerializerMethodField()
    
    # Related data
    uom_conversions = ItemUOMConversionSerializer(many=True, required=False)
    tax_compositions = serializers.SerializerMethodField()
    
    # Write-only fields for nested data
    tax_compositions_data = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True
    )
    
    # Display fields
    item_type_display = serializers.CharField(source='get_item_type_display', read_only=True)
    product_type_display = serializers.CharField(source='get_product_type_display', read_only=True)
    tax_category_display = serializers.CharField(source='get_tax_category_display', read_only=True)
    
    def get_current_tax(self, obj):
        tax = obj.current_tax
        if tax:
            return {
                'id': tax.id,
                'name': tax.name,
                'rate': float(tax.tax_rate)
            }
        return None
    
    def get_tax_compositions(self, obj):
        """Get current tax compositions for this item"""
        compositions = obj.tax_compositions.filter(is_deleted=False).select_related('tax')
        return ItemTaxCompositionSerializer(compositions, many=True).data
    
    class Meta:
        model = Item
        fields = [
            'id', 'code', 'name', 'description', 'short_name', 'barcode', 'sku',
            'company', 'company_name', 'bag_weight',
            'item_type', 'item_type_display', 'product_type', 'product_type_display',
            'parent', 'parent_name', 'category', 'category_name', 'brand', 'brand_name',
            'base_uom', 'base_uom_name', 'base_uom_code',
            'hsn_code', 'sac_code', 'tax_category', 'tax_category_display',
            'cess_applicable', 'cess_rate',
            'cost_price', 'selling_price', 'mrp', 'min_price', 'price_includes_tax',
            'is_stockable', 'track_inventory', 
            'min_stock_level', 'max_stock_level', 'reorder_level', 'reorder_quantity',
            'weight', 'weight_unit', 'length', 'width', 'height',
            'image', 'additional_images',
            'is_active', 'is_saleable', 'is_purchasable', 'is_featured',
            'allow_discount', 'allow_negative_stock',
            'manufacturer', 'warranty_period', 'warranty_description',
            'erp_code', 'erp_id', 'sync_with_erp',
            'tags', 'notes', 'specifications',
            'current_tax', 'uom_conversions', 'tax_compositions', 'tax_compositions_data',
            'created_on', 'modified_on'
        ]
        read_only_fields = ['created_on', 'modified_on']
    
    def validate_barcode(self, value):
        if value:
            value = value.upper()
        return value
    
    def validate_category(self, value):
        if value and not value.is_active:
            raise serializers.ValidationError("Selected category is inactive")
        return value
    
    def validate_brand(self, value):
        if value and not value.is_active:
            raise serializers.ValidationError("Selected brand is inactive")
        return value

    def validate(self, data):
        data = super().validate(data)

        if GeneralSettings.is_company_scoped_item_enforcement_enabled():
            company = data.get('company', serializers.empty)
            if self.instance is None:
                if company in [serializers.empty, None]:
                    raise serializers.ValidationError({'company': 'Company is required when company-scoped item enforcement is enabled.'})
            else:
                if company is None:
                    raise serializers.ValidationError({'company': 'Company is required when company-scoped item enforcement is enabled.'})
                if company is serializers.empty and not self.instance.company_id:
                    raise serializers.ValidationError({'company': 'Company is required when company-scoped item enforcement is enabled.'})

        return data

    def create(self, validated_data):
        """
        Create item and handle UOM conversions and tax compositions in single transaction
        """
        # Extract related data
        uom_conversions_data = validated_data.pop('uom_conversions', [])
        tax_compositions_data = validated_data.pop('tax_compositions_data', [])
        
        # Create the item
        item = super().create(validated_data)
        
        # Create base UOM conversion record with conversion factor 1.0
        ItemUOMConversion.objects.create(
            item=item,
            alternate_uom=item.base_uom,
            conversion_factor=1.0,
            is_default_purchase=True,
            is_default_sales=True
        )
        
        # Create additional UOM conversions if provided
        for conversion_data in uom_conversions_data:
            # Skip if it's the base UOM (already created above)
            if conversion_data.get('alternate_uom') != item.base_uom:
                ItemUOMConversion.objects.create(
                    item=item,
                    **conversion_data
                )
        
        # Create tax compositions if provided
        if tax_compositions_data:
            import json
            try:
                # Parse JSON string if it's a string
                if isinstance(tax_compositions_data, str):
                    compositions_list = json.loads(tax_compositions_data)
                else:
                    compositions_list = tax_compositions_data
                
                for composition_data in compositions_list:
                    # Remove read-only fields
                    clean_data = {k: v for k, v in composition_data.items() 
                                if k in ['tax', 'composition_type', 'effective_from', 'effective_to']}
                    
                    # Convert tax ID string to Tax instance if needed
                    if 'tax' in clean_data and isinstance(clean_data['tax'], str):
                        clean_data['tax'] = Tax.objects.get(id=clean_data['tax'])
                    elif 'tax' in clean_data and isinstance(clean_data['tax'], dict):
                        clean_data['tax'] = Tax.objects.get(id=clean_data['tax']['id'])
                    
                    ItemTaxComposition.objects.create(
                        item=item,
                        **clean_data
                    )
            except (json.JSONDecodeError, TypeError) as e:
                # If parsing fails, skip tax compositions
                pass
        
        return item
    
    def update(self, instance, validated_data):
        """
        Update item and handle UOM conversions and tax compositions in single transaction
        """
        # Extract related data
        uom_conversions_data = validated_data.pop('uom_conversions', None)
        tax_compositions_data = validated_data.pop('tax_compositions_data', None)
        
        # Update the item
        item = super().update(instance, validated_data)
        
        # Handle UOM conversions update if provided
        if uom_conversions_data is not None:
            # Get existing conversion IDs from the request
            incoming_ids = [conv.get('id') for conv in uom_conversions_data if conv.get('id')]
            
            # Delete conversions not in the incoming list (except base UOM)
            ItemUOMConversion.objects.filter(
                item=item,
                is_deleted=False
            ).exclude(
                id__in=incoming_ids
            ).exclude(
                alternate_uom=item.base_uom  # Don't delete base UOM conversion
            ).update(is_deleted=True)
            
            # Update or create conversions
            for conversion_data in uom_conversions_data:
                conversion_id = conversion_data.pop('id', None)
                if conversion_id:
                    # Update existing conversion
                    ItemUOMConversion.objects.filter(id=conversion_id).update(**conversion_data)
                else:
                    # Create new conversion (skip if base UOM)
                    if conversion_data.get('alternate_uom') != item.base_uom:
                        ItemUOMConversion.objects.create(
                            item=item,
                            **conversion_data
                        )
        
        # Handle tax compositions update if provided
        if tax_compositions_data is not None and tax_compositions_data != '':
            import json
            try:
                # Parse JSON string if it's a string
                if isinstance(tax_compositions_data, str):
                    compositions_list = json.loads(tax_compositions_data)
                else:
                    compositions_list = tax_compositions_data
                
                # Get existing composition IDs from the request
                incoming_ids = [comp.get('id') for comp in compositions_list if comp.get('id')]
                
                # Delete compositions not in the incoming list
                ItemTaxComposition.objects.filter(
                    item=item,
                    is_deleted=False
                ).exclude(
                    id__in=incoming_ids
                ).update(is_deleted=True)
                
                # Update or create compositions
                for composition_data in compositions_list:
                    composition_id = composition_data.pop('id', None)
                    
                    # Remove read-only fields
                    clean_data = {k: v for k, v in composition_data.items() 
                                if k in ['tax', 'composition_type', 'effective_from', 'effective_to']}
                    
                    # Convert tax ID string to Tax instance if needed
                    if 'tax' in clean_data and isinstance(clean_data['tax'], str):
                        clean_data['tax'] = Tax.objects.get(id=clean_data['tax'])
                    elif 'tax' in clean_data and isinstance(clean_data['tax'], dict):
                        clean_data['tax'] = Tax.objects.get(id=clean_data['tax']['id'])
                    
                    if composition_id:
                        # Update existing composition
                        ItemTaxComposition.objects.filter(id=composition_id).update(**clean_data)
                    else:
                        # Create new composition
                        ItemTaxComposition.objects.create(
                            item=item,
                            **clean_data
                        )
            except (json.JSONDecodeError, TypeError) as e:
                # If parsing fails, skip tax compositions
                pass
        
        return item


class ItemFieldConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemFieldConfiguration
        fields = [
            'id', 'field_name', 'display_label', 'is_visible', 
            'is_required', 'is_readonly', 'display_order', 'section'
        ]
        read_only_fields = ['id']


# ==================== Channel Partner Serializers ====================

class ChannelPartnerConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChannelPartnerConfiguration
        fields = [
            'id', 'name', 'enable_superstockist', 'enable_distributor', 'enable_retailer',
            'enforce_channel_hierarchy', 'is_active', 'created_on', 'modified_on'
        ]
        read_only_fields = ['id', 'created_on', 'modified_on']


class SuperstockistLocationSerializer(serializers.ModelSerializer):
    state_name = serializers.CharField(source='state.name', read_only=True)
    city_name = serializers.CharField(source='city.name', read_only=True)
    area_name = serializers.CharField(source='area.name', read_only=True)
    
    class Meta:
        model = SuperstockistLocation
        fields = ('id', 'state', 'state_name', 'city', 'city_name', 'area', 'area_name')


class SuperstockistSerializer(DuplicateValidationSerializerMixin, serializers.ModelSerializer):
    # Read-only fields for display
    state = serializers.PrimaryKeyRelatedField(read_only=True)
    state_name = serializers.CharField(source='state.name', read_only=True)
    city = serializers.PrimaryKeyRelatedField(read_only=True)
    city_name = serializers.CharField(source='city.name', read_only=True)
    area = serializers.PrimaryKeyRelatedField(read_only=True)
    area_name = serializers.CharField(source='area.name', read_only=True)
    shipping_state = serializers.PrimaryKeyRelatedField(read_only=True)
    shipping_state_name = serializers.CharField(source='shipping_state.name', read_only=True)
    shipping_city = serializers.PrimaryKeyRelatedField(read_only=True)
    shipping_city_name = serializers.CharField(source='shipping_city.name', read_only=True)
    shipping_area = serializers.PrimaryKeyRelatedField(read_only=True)
    shipping_area_name = serializers.CharField(source='shipping_area.name', read_only=True)
    company = serializers.PrimaryKeyRelatedField(read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    # Write-only fields for updates
    state_id = serializers.PrimaryKeyRelatedField(write_only=True, source='state', queryset=State.objects.filter(is_deleted=False))
    city_id = serializers.PrimaryKeyRelatedField(write_only=True, source='city', queryset=City.objects.filter(is_deleted=False), required=False, allow_null=True)
    area_id = serializers.PrimaryKeyRelatedField(write_only=True, source='area', queryset=Area.objects.filter(is_deleted=False), required=True)
    shipping_state_id = serializers.PrimaryKeyRelatedField(write_only=True, source='shipping_state', queryset=State.objects.filter(is_deleted=False), required=False, allow_null=True)
    shipping_city_id = serializers.PrimaryKeyRelatedField(write_only=True, source='shipping_city', queryset=City.objects.filter(is_deleted=False), required=False, allow_null=True)
    shipping_area_id = serializers.PrimaryKeyRelatedField(write_only=True, source='shipping_area', queryset=Area.objects.filter(is_deleted=False), required=False, allow_null=True)
    company_id = serializers.PrimaryKeyRelatedField(write_only=True, source='company', queryset=Company.objects.filter(is_deleted=False), required=False, allow_null=True)
    
    locations = SuperstockistLocationSerializer(many=True, read_only=True)
    location_summary = serializers.SerializerMethodField(read_only=True)
    contacts = SuperstockistContactSerializer(many=True, read_only=True)
    
    # Write-only fields for location IDs (UUIDs)
    location_states = serializers.ListField(child=serializers.UUIDField(), write_only=True, required=False)
    location_cities = serializers.ListField(child=serializers.UUIDField(), write_only=True, required=False)
    location_areas = serializers.ListField(child=serializers.UUIDField(), write_only=True, required=False)
    
    def get_location_summary(self, obj):
        """Get summary of coverage areas"""
        locations_qs = obj.locations.all()
        if not locations_qs.exists():
            return None
        
        states_count = locations_qs.values('state').distinct().count()
        cities_count = locations_qs.values('city').distinct().count()
        areas_count = locations_qs.count()
        
        return {
            'states': states_count,
            'cities': cities_count,
            'areas': areas_count
        }
    
    class Meta:
        model = Superstockist
        fields = (
            'id', 'code', 'name', 
            'state', 'state_id', 'state_name', 
            'city', 'city_id', 'city_name', 
            'area', 'area_id', 'area_name', 
            'address', 'pincode',
            'shipping_same_as_billing', 
            'shipping_state', 'shipping_state_id', 'shipping_state_name', 
            'shipping_city', 'shipping_city_id', 'shipping_city_name', 
            'shipping_area', 'shipping_area_id', 'shipping_area_name',
            'shipping_address', 'shipping_pincode',
            'gstin', 'pan', 'credit_limit', 'credit_days',
            'aadhar', 'bank_account_number', 'bank_name', 'bank_branch', 'bank_ifsc', 'bank_account_type', 'google_location',
            'is_active', 'effective_from', 'effective_to',
            'erp_code',
            'company', 'company_id', 'company_name',
            'created_on', 'modified_on',
            'locations', 'location_summary', 'contacts',
            'location_states', 'location_cities', 'location_areas'
        )
        read_only_fields = ('id', 'created_on', 'modified_on')
    
    def validate_code(self, value):
        """Auto-convert code to uppercase"""
        if value:
            return value.upper()
        return value
    
    def validate_gstin(self, value):
        """Validate GSTIN format and auto-convert to uppercase"""
        if value:
            value = value.upper()
            if len(value) != 15:
                raise serializers.ValidationError("GSTIN must be 15 characters long")
        return value
    
    def validate_pan(self, value):
        """Validate PAN format and auto-convert to uppercase"""
        if value:
            value = value.upper()
            if len(value) != 10:
                raise serializers.ValidationError("PAN must be 10 characters long")
        return value

    def validate(self, data):
        area = data.get('area', serializers.empty)
        if self.instance is None:
            if area in [serializers.empty, None]:
                raise serializers.ValidationError({'area_id': 'Area is required'})
        else:
            if area is None:
                raise serializers.ValidationError({'area_id': 'Area is required'})
            if area is serializers.empty and not self.instance.area_id:
                raise serializers.ValidationError({'area_id': 'Area is required'})
        return data
    
    def create(self, validated_data):
        location_states = validated_data.pop('location_states', [])
        location_cities = validated_data.pop('location_cities', [])
        location_areas = validated_data.pop('location_areas', [])
        
        if not location_states and not location_cities and not location_areas:
            raise serializers.ValidationError({"location_areas": "At least one coverage area must be selected"})
        
        superstockist = Superstockist.objects.create(**validated_data)
        for state_id in location_states:
            SuperstockistLocation.objects.create(superstockist=superstockist, state_id=state_id)
        for city_id in location_cities:
            city = City.objects.get(pk=city_id)
            SuperstockistLocation.objects.create(superstockist=superstockist, state_id=city.state_id, city_id=city_id)
        for area_id in location_areas:
            area = Area.objects.get(pk=area_id)
            SuperstockistLocation.objects.create(superstockist=superstockist, state_id=area.state_id, area_id=area_id)
        return superstockist
    
    def update(self, instance, validated_data):
        location_states = validated_data.pop('location_states', None)
        location_cities = validated_data.pop('location_cities', None)
        location_areas = validated_data.pop('location_areas', None)
        
        # Build update dict with proper field names
        update_dict = {}
        for attr, value in validated_data.items():
            if value is None:
                # For None values, check if it's a foreign key field
                if attr in ['state', 'city', 'area', 'shipping_state', 'shipping_city', 'shipping_area', 'company']:
                    update_dict[f"{attr}_id"] = None
                else:
                    update_dict[attr] = None
            elif hasattr(value, 'pk'):  # It's a related object
                update_dict[f"{attr}_id"] = value.pk
            else:
                update_dict[attr] = value
        
        # Normalize GSTIN if present
        if 'gstin' in update_dict and update_dict['gstin']:
            update_dict['gstin'] = update_dict['gstin'].upper().strip()
        
        # Save without calling full_clean() by using update on queryset
        Superstockist.objects.filter(pk=instance.pk).update(**update_dict)
        instance.refresh_from_db()
        
        if location_states is not None or location_cities is not None or location_areas is not None:
            instance.locations.all().delete()
            if location_states:
                for state_id in location_states:
                    SuperstockistLocation.objects.create(superstockist=instance, state_id=state_id)
            if location_cities:
                for city_id in location_cities:
                    city = City.objects.get(pk=city_id)
                    SuperstockistLocation.objects.create(superstockist=instance, state_id=city.state_id, city_id=city_id)
            if location_areas:
                for area_id in location_areas:
                    area = Area.objects.get(pk=area_id)
                    SuperstockistLocation.objects.create(superstockist=instance, state_id=area.state_id, area_id=area_id)
        return instance


class DistributorLocationSerializer(serializers.ModelSerializer):
    state_name = serializers.CharField(source='state.name', read_only=True)
    district_name = serializers.CharField(source='district.name', read_only=True)
    mandal_name = serializers.CharField(source='mandal.name', read_only=True)
    city_name = serializers.CharField(source='city.name', read_only=True)
    area_name = serializers.CharField(source='area.name', read_only=True)
    
    class Meta:
        model = DistributorLocation
        fields = ('id', 'state', 'state_name', 'district', 'district_name', 'mandal', 'mandal_name', 'city', 'city_name', 'area', 'area_name')


class DistributorSerializer(DuplicateValidationSerializerMixin, serializers.ModelSerializer):
    # Read-only fields for display
    country = serializers.PrimaryKeyRelatedField(read_only=True)
    country_name = serializers.CharField(source='country.name', read_only=True)
    state = serializers.PrimaryKeyRelatedField(read_only=True)
    state_name = serializers.CharField(source='state.name', read_only=True)
    district = serializers.PrimaryKeyRelatedField(read_only=True)
    district_name = serializers.CharField(source='district.name', read_only=True)
    mandal = serializers.PrimaryKeyRelatedField(read_only=True)
    mandal_name = serializers.CharField(source='mandal.name', read_only=True)
    city = serializers.PrimaryKeyRelatedField(read_only=True)
    city_name = serializers.CharField(source='city.name', read_only=True)
    area = serializers.PrimaryKeyRelatedField(read_only=True)
    area_name = serializers.CharField(source='area.name', read_only=True)
    shipping_country = serializers.PrimaryKeyRelatedField(read_only=True)
    shipping_country_name = serializers.CharField(source='shipping_country.name', read_only=True)
    shipping_state = serializers.PrimaryKeyRelatedField(read_only=True)
    shipping_state_name = serializers.CharField(source='shipping_state.name', read_only=True)
    shipping_district = serializers.PrimaryKeyRelatedField(read_only=True)
    shipping_district_name = serializers.CharField(source='shipping_district.name', read_only=True)
    shipping_mandal = serializers.PrimaryKeyRelatedField(read_only=True)
    shipping_mandal_name = serializers.CharField(source='shipping_mandal.name', read_only=True)
    shipping_city = serializers.PrimaryKeyRelatedField(read_only=True)
    shipping_city_name = serializers.CharField(source='shipping_city.name', read_only=True)
    shipping_area = serializers.PrimaryKeyRelatedField(read_only=True)
    shipping_area_name = serializers.CharField(source='shipping_area.name', read_only=True)
    superstockist = serializers.PrimaryKeyRelatedField(read_only=True)
    superstockist_name = serializers.CharField(source='superstockist.name', read_only=True)
    company = serializers.PrimaryKeyRelatedField(read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    agent = serializers.PrimaryKeyRelatedField(read_only=True)
    agent_name = serializers.CharField(source='agent.name', read_only=True)
    
    # User fields - write-only IDs for M2M
    user_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    user_company_ids = serializers.ListField(child=serializers.UUIDField(), write_only=True, required=False)
    user_location_ids = serializers.ListField(child=serializers.UUIDField(), write_only=True, required=False)
    user_group_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    user_groups = serializers.SerializerMethodField(read_only=True)
    user_companies = serializers.SerializerMethodField(read_only=True)
    user_locations = serializers.SerializerMethodField(read_only=True)
    
    # Write-only fields for updates
    country_id = serializers.PrimaryKeyRelatedField(write_only=True, source='country', queryset=Country.objects.filter(is_deleted=False), required=False, allow_null=True)
    state_id = serializers.PrimaryKeyRelatedField(write_only=True, source='state', queryset=State.objects.filter(is_deleted=False))
    district_id = serializers.PrimaryKeyRelatedField(write_only=True, source='district', queryset=District.objects.filter(is_deleted=False), required=False, allow_null=True)
    mandal_id = serializers.PrimaryKeyRelatedField(write_only=True, source='mandal', queryset=Mandal.objects.filter(is_deleted=False), required=False, allow_null=True)
    city_id = serializers.PrimaryKeyRelatedField(write_only=True, source='city', queryset=City.objects.filter(is_deleted=False), required=False, allow_null=True)
    area_id = serializers.PrimaryKeyRelatedField(write_only=True, source='area', queryset=Area.objects.filter(is_deleted=False), required=True)
    shipping_country_id = serializers.PrimaryKeyRelatedField(write_only=True, source='shipping_country', queryset=Country.objects.filter(is_deleted=False), required=False, allow_null=True)
    shipping_state_id = serializers.PrimaryKeyRelatedField(write_only=True, source='shipping_state', queryset=State.objects.filter(is_deleted=False), required=False, allow_null=True)
    shipping_district_id = serializers.PrimaryKeyRelatedField(write_only=True, source='shipping_district', queryset=District.objects.filter(is_deleted=False), required=False, allow_null=True)
    shipping_mandal_id = serializers.PrimaryKeyRelatedField(write_only=True, source='shipping_mandal', queryset=Mandal.objects.filter(is_deleted=False), required=False, allow_null=True)
    shipping_city_id = serializers.PrimaryKeyRelatedField(write_only=True, source='shipping_city', queryset=City.objects.filter(is_deleted=False), required=False, allow_null=True)
    shipping_area_id = serializers.PrimaryKeyRelatedField(write_only=True, source='shipping_area', queryset=Area.objects.filter(is_deleted=False), required=False, allow_null=True)
    superstockist_id = serializers.PrimaryKeyRelatedField(
        write_only=True, 
        source='superstockist', 
        queryset=Superstockist.objects.filter(is_deleted=False, is_active=True),
        required=False,
        allow_null=True
    )
    company_id = serializers.PrimaryKeyRelatedField(write_only=True, source='company', queryset=Company.objects.filter(is_deleted=False), required=False, allow_null=True)
    agent_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        source='agent',
        queryset=Agent.objects.filter(is_deleted=False, is_active=True),
        required=False,
        allow_null=True
    )
    
    locations = DistributorLocationSerializer(many=True, read_only=True)
    location_summary = serializers.SerializerMethodField(read_only=True)
    contacts = DistributorContactSerializer(many=True, read_only=True)
    
    # Write-only fields for location IDs (UUIDs)
    location_states = serializers.ListField(child=serializers.UUIDField(), write_only=True, required=False)
    location_districts = serializers.ListField(child=serializers.UUIDField(), write_only=True, required=False)
    location_mandals = serializers.ListField(child=serializers.UUIDField(), write_only=True, required=False)
    location_cities = serializers.ListField(child=serializers.UUIDField(), write_only=True, required=False)
    location_areas = serializers.ListField(child=serializers.UUIDField(), write_only=True, required=False)
    
    def get_location_summary(self, obj):
        """Get summary of coverage areas"""
        locations_qs = obj.locations.all()
        if not locations_qs.exists():
            return None
        
        states_count = locations_qs.values('state').distinct().count()
        cities_count = locations_qs.values('city').distinct().count()
        areas_count = locations_qs.count()
        
        return {
            'states': states_count,
            'cities': cities_count,
            'areas': areas_count
        }
    
    class Meta:
        model = Distributor
        fields = (
            'id', 'code', 'name',
            'superstockist', 'superstockist_id', 'superstockist_name',
            'country', 'country_id', 'country_name',
            'state', 'state_id', 'state_name',
            'district', 'district_id', 'district_name',
            'mandal', 'mandal_id', 'mandal_name',
            'city', 'city_id', 'city_name', 
            'area', 'area_id', 'area_name',
            'street', 
            'address', 'pincode',
            'shipping_same_as_billing',
            'shipping_country', 'shipping_country_id', 'shipping_country_name',
            'shipping_state', 'shipping_state_id', 'shipping_state_name',
            'shipping_district', 'shipping_district_id', 'shipping_district_name',
            'shipping_mandal', 'shipping_mandal_id', 'shipping_mandal_name',
            'shipping_city', 'shipping_city_id', 'shipping_city_name', 
            'shipping_area', 'shipping_area_id', 'shipping_area_name',
            'shipping_street',
            'shipping_address', 'shipping_pincode',
            'gstin', 'pan', 'credit_limit', 'credit_days',
            'aadhar', 'bank_account_number', 'bank_name', 'bank_branch', 'bank_ifsc', 'bank_account_type', 'google_location',
            'is_active', 'effective_from', 'effective_to',
            'erp_code',
            'company', 'company_id', 'company_name',
            'agent', 'agent_id', 'agent_name',
            'created_on', 'modified_on',
            'locations', 'location_summary', 'contacts',
            'location_states', 'location_districts', 'location_mandals', 'location_cities', 'location_areas',
            'user_username', 'user_password', 'user_phone', 'user_device_access',
            'user_has_all_companies', 'user_has_all_locations',
            'user_company_ids', 'user_location_ids', 'user_group_ids', 'user_groups', 'user_companies', 'user_locations',
        )
        read_only_fields = ('id', 'created_on', 'modified_on')
    
    def get_user_groups(self, obj):
        return [{'id': g.id, 'name': g.name} for g in obj.user_groups.all()]

    def get_user_companies(self, obj):
        return [{'id': str(c.id), 'name': c.name} for c in obj.user_companies.all()]

    def get_user_locations(self, obj):
        return [{'id': str(l.id), 'name': l.name} for l in obj.user_locations.all()]

    def validate_code(self, value):
        """Auto-convert code to uppercase"""
        if value:
            return value.upper()
        return value
    
    def validate_gstin(self, value):
        """Validate GSTIN format and auto-convert to uppercase"""
        if value:
            value = value.upper()
            if len(value) != 15:
                raise serializers.ValidationError("GSTIN must be 15 characters long")
        return value
    
    def validate_pan(self, value):
        """Validate PAN format and auto-convert to uppercase"""
        if value:
            value = value.upper()
            if len(value) != 10:
                raise serializers.ValidationError("PAN must be 10 characters long")
        return value
    
    def validate(self, data):
        """Validate hierarchy if enforced"""
        # Get active channel partner configuration
        try:
            config = ChannelPartnerConfiguration.objects.filter(is_active=True, is_deleted=False).first()
        except ChannelPartnerConfiguration.DoesNotExist:
            config = None
        
        superstockist = data.get('superstockist')
        
        # Check if hierarchy is enforced AND superstockist is enabled
        if config and config.enforce_channel_hierarchy and config.enable_superstockist and not superstockist:
            raise serializers.ValidationError({
                'superstockist_id': 'Superstockist is required when channel hierarchy is enforced and superstockist is enabled'
            })

        area = data.get('area', serializers.empty)
        if self.instance is None:
            if area in [serializers.empty, None]:
                raise serializers.ValidationError({'area_id': 'Area is required'})
        else:
            if area is None:
                raise serializers.ValidationError({'area_id': 'Area is required'})
            if area is serializers.empty and not self.instance.area_id:
                raise serializers.ValidationError({'area_id': 'Area is required'})
        
        return data
    
    def create(self, validated_data):
        location_states = validated_data.pop('location_states', [])
        location_districts = validated_data.pop('location_districts', [])
        location_mandals = validated_data.pop('location_mandals', [])
        location_cities = validated_data.pop('location_cities', [])
        location_areas = validated_data.pop('location_areas', [])
        
        # Extract M2M user fields
        user_password = validated_data.pop('user_password', '')
        user_company_ids = validated_data.pop('user_company_ids', [])
        user_location_ids = validated_data.pop('user_location_ids', [])
        user_group_ids = validated_data.pop('user_group_ids', [])
        
        if not location_states and not location_districts and not location_mandals and not location_cities and not location_areas:
            raise serializers.ValidationError({"location_areas": "At least one coverage area must be selected"})
        
        with transaction.atomic():
            distributor = Distributor.objects.create(**validated_data)
            
            # Set M2M user fields on model
            if user_company_ids:
                distributor.user_companies.set(user_company_ids)
            if user_location_ids:
                distributor.user_locations.set(user_location_ids)
            if user_group_ids:
                distributor.user_groups.set(user_group_ids)
            
            for state_id in location_states:
                DistributorLocation.objects.create(distributor=distributor, state_id=state_id)
            for district_id in location_districts:
                district = District.objects.get(pk=district_id)
                DistributorLocation.objects.create(distributor=distributor, state_id=district.state_id, district_id=district_id)
            for mandal_id in location_mandals:
                mandal = Mandal.objects.get(pk=mandal_id)
                DistributorLocation.objects.create(distributor=distributor, state_id=mandal.state_id, district_id=mandal.district_id, mandal_id=mandal_id)
            for city_id in location_cities:
                city = City.objects.get(pk=city_id)
                DistributorLocation.objects.create(distributor=distributor, state_id=city.state_id, district_id=city.district_id, mandal_id=city.mandal_id, city_id=city_id)
            for area_id in location_areas:
                area = Area.objects.get(pk=area_id)
                DistributorLocation.objects.create(distributor=distributor, state_id=area.state_id, district_id=area.district_id, mandal_id=area.mandal_id, city_id=area.city_id, area_id=area_id)
            
            # Auto-create user
            self._create_user_for_distributor(distributor, user_password)
        
        return distributor
    
    def _create_user_for_distributor(self, distributor, password=''):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        username = (distributor.user_username or '').strip() or distributor.code
        password = password.strip() if password else username
        
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({'user_username': f'Username "{username}" is already taken.'})
        
        phone = (distributor.user_phone or '').strip()
        if phone and User.objects.filter(phone=phone, is_active=True).exists():
            raise serializers.ValidationError({'user_phone': f'Phone number "{phone}" is already in use.'})
        
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
    
    def update(self, instance, validated_data):
        location_states = validated_data.pop('location_states', None)
        location_districts = validated_data.pop('location_districts', None)
        location_mandals = validated_data.pop('location_mandals', None)
        location_cities = validated_data.pop('location_cities', None)
        location_areas = validated_data.pop('location_areas', None)
        
        # Extract M2M user fields
        validated_data.pop('user_password', None)
        user_company_ids = validated_data.pop('user_company_ids', None)
        user_location_ids = validated_data.pop('user_location_ids', None)
        user_group_ids = validated_data.pop('user_group_ids', None)
        
        update_dict = {}
        for attr, value in validated_data.items():
            if value is None:
                if attr in ['country', 'state', 'district', 'mandal', 'city', 'area', 'shipping_country', 'shipping_state', 'shipping_district', 'shipping_mandal', 'shipping_city', 'shipping_area', 'company', 'superstockist', 'agent']:
                    update_dict[f"{attr}_id"] = None
                else:
                    update_dict[attr] = None
            elif hasattr(value, 'pk'):
                update_dict[f"{attr}_id"] = value.pk
            else:
                update_dict[attr] = value
        
        if 'gstin' in update_dict and update_dict['gstin']:
            update_dict['gstin'] = update_dict['gstin'].upper().strip()
        
        Distributor.objects.filter(pk=instance.pk).update(**update_dict)
        instance.refresh_from_db()
        
        if location_states is not None or location_districts is not None or location_mandals is not None or location_cities is not None or location_areas is not None:
            instance.locations.all().delete()
            if location_states:
                for state_id in location_states:
                    DistributorLocation.objects.create(distributor=instance, state_id=state_id)
            if location_districts:
                for district_id in location_districts:
                    district = District.objects.get(pk=district_id)
                    DistributorLocation.objects.create(distributor=instance, state_id=district.state_id, district_id=district_id)
            if location_mandals:
                for mandal_id in location_mandals:
                    mandal = Mandal.objects.get(pk=mandal_id)
                    DistributorLocation.objects.create(distributor=instance, state_id=mandal.state_id, district_id=mandal.district_id, mandal_id=mandal_id)
            if location_cities:
                for city_id in location_cities:
                    city = City.objects.get(pk=city_id)
                    DistributorLocation.objects.create(distributor=instance, state_id=city.state_id, district_id=city.district_id, mandal_id=city.mandal_id, city_id=city_id)
            if location_areas:
                for area_id in location_areas:
                    area = Area.objects.get(pk=area_id)
                    DistributorLocation.objects.create(distributor=instance, state_id=area.state_id, district_id=area.district_id, mandal_id=area.mandal_id, city_id=area.city_id, area_id=area_id)
        
        # Update user M2M fields on distributor model
        if user_company_ids is not None:
            instance.user_companies.set(user_company_ids)
        if user_location_ids is not None:
            instance.user_locations.set(user_location_ids)
        if user_group_ids is not None:
            instance.user_groups.set(user_group_ids)
        
        # Also update the linked user account if exists
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.filter(distributor=instance).first()
        if user:
            user_changed = False
            if 'user_phone' in update_dict:
                user.phone = update_dict['user_phone'] or None
                user_changed = True
            if 'user_device_access' in update_dict:
                user.device_access = update_dict['user_device_access']
                user_changed = True
            if 'user_has_all_companies' in update_dict:
                user.has_all_companies = update_dict['user_has_all_companies']
                user_changed = True
            if 'user_has_all_locations' in update_dict:
                user.has_all_locations = update_dict['user_has_all_locations']
                user_changed = True
            if user_changed:
                user.save()
            if user_group_ids is not None:
                user.groups.set(user_group_ids)
            if user_company_ids is not None:
                user.companies.set(user_company_ids)
            if user_location_ids is not None:
                user.locations.set(user_location_ids)
        
        return instance


class RetailerLocationSerializer(serializers.ModelSerializer):
    state_name = serializers.CharField(source='state.name', read_only=True)
    city_name = serializers.CharField(source='city.name', read_only=True)
    area_name = serializers.CharField(source='area.name', read_only=True)
    
    class Meta:
        model = RetailerLocation
        fields = ('id', 'state', 'state_name', 'city', 'city_name', 'area', 'area_name')


class RetailerSerializer(DuplicateValidationSerializerMixin, serializers.ModelSerializer):
    # Read-only FK IDs for display
    state = serializers.PrimaryKeyRelatedField(read_only=True)
    city = serializers.PrimaryKeyRelatedField(read_only=True)
    area = serializers.PrimaryKeyRelatedField(read_only=True)
    shipping_state = serializers.PrimaryKeyRelatedField(read_only=True)
    shipping_city = serializers.PrimaryKeyRelatedField(read_only=True)
    shipping_area = serializers.PrimaryKeyRelatedField(read_only=True)
    distributor = serializers.PrimaryKeyRelatedField(read_only=True)
    outlet_type = serializers.PrimaryKeyRelatedField(read_only=True)
    company = serializers.PrimaryKeyRelatedField(read_only=True)
    
    # User fields - write-only IDs for M2M
    user_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    user_company_ids = serializers.ListField(child=serializers.UUIDField(), write_only=True, required=False)
    user_location_ids = serializers.ListField(child=serializers.UUIDField(), write_only=True, required=False)
    user_group_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    
    # Read-only names for display
    state_name = serializers.CharField(source='state.name', read_only=True)
    state_id = serializers.PrimaryKeyRelatedField(write_only=True, source='state', queryset=State.objects.filter(is_deleted=False))
    city_name = serializers.CharField(source='city.name', read_only=True, allow_null=True)
    city_id = serializers.PrimaryKeyRelatedField(write_only=True, source='city', queryset=City.objects.filter(is_deleted=False), required=True)
    area_name = serializers.CharField(source='area.name', read_only=True, allow_null=True)
    area_id = serializers.PrimaryKeyRelatedField(write_only=True, source='area', queryset=Area.objects.filter(is_deleted=False), required=True)
    shipping_state_name = serializers.CharField(source='shipping_state.name', read_only=True, allow_null=True)
    shipping_state_id = serializers.PrimaryKeyRelatedField(write_only=True, source='shipping_state', queryset=State.objects.filter(is_deleted=False), required=False, allow_null=True)
    shipping_city_name = serializers.CharField(source='shipping_city.name', read_only=True, allow_null=True)
    shipping_city_id = serializers.PrimaryKeyRelatedField(write_only=True, source='shipping_city', queryset=City.objects.filter(is_deleted=False), required=False, allow_null=True)
    shipping_area_name = serializers.CharField(source='shipping_area.name', read_only=True, allow_null=True)
    shipping_area_id = serializers.PrimaryKeyRelatedField(write_only=True, source='shipping_area', queryset=Area.objects.filter(is_deleted=False), required=False, allow_null=True)
    distributor_name = serializers.CharField(source='distributor.name', read_only=True, allow_null=True)
    distributor_id = serializers.PrimaryKeyRelatedField(
        write_only=True, 
        source='distributor', 
        queryset=Distributor.objects.filter(is_deleted=False, is_active=True),
        required=False,
        allow_null=True
    )
    outlet_type_name = serializers.CharField(source='outlet_type.name', read_only=True, allow_null=True)
    outlet_type_id = serializers.PrimaryKeyRelatedField(write_only=True, source='outlet_type', queryset=OutletType.objects.filter(is_deleted=False), required=False, allow_null=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    company_id = serializers.PrimaryKeyRelatedField(write_only=True, source='company', queryset=Company.objects.filter(is_deleted=False), required=False, allow_null=True)
    effective_from = serializers.DateField(required=False, allow_null=True)
    effective_to = serializers.DateField(required=False, allow_null=True)
    locations = RetailerLocationSerializer(many=True, read_only=True)
    contacts = RetailerContactSerializer(many=True, read_only=True)
    
    def to_internal_value(self, data):
        """Convert empty strings to None for date fields before validation"""
        # Handle date fields that might be empty strings
        if 'effective_from' in data and data['effective_from'] == '':
            data['effective_from'] = None
        if 'effective_to' in data and data['effective_to'] == '':
            data['effective_to'] = None
        return super().to_internal_value(data)
    
    class Meta:
        model = Retailer
        fields = (
            'id', 'code', 'name',
            'distributor', 'distributor_id', 'distributor_name',
            'state', 'state_id', 'state_name', 
            'city', 'city_id', 'city_name', 
            'area', 'area_id', 'area_name', 
            'address', 'pincode',
            'shipping_same_as_billing', 
            'shipping_state', 'shipping_state_id', 'shipping_state_name',
            'shipping_city', 'shipping_city_id', 'shipping_city_name', 
            'shipping_area', 'shipping_area_id', 'shipping_area_name',
            'shipping_address', 'shipping_pincode',
            'outlet_type', 'outlet_type_id', 'outlet_type_name', 'outlet_size',
            'gstin', 'pan', 'credit_limit', 'credit_days',
            'aadhar', 'bank_account_number', 'bank_name', 'bank_branch', 'bank_ifsc', 'bank_account_type', 'google_location',
            'is_active', 'effective_from', 'effective_to',
            'erp_code',
            'company', 'company_id', 'company_name',
            'created_on', 'modified_on',
            'locations', 'contacts',
            'user_username', 'user_password', 'user_phone', 'user_device_access',
            'user_has_all_companies', 'user_has_all_locations',
            'user_company_ids', 'user_location_ids', 'user_group_ids',
        )
        read_only_fields = ('id', 'created_on', 'modified_on')
    
    def validate_code(self, value):
        """Auto-convert code to uppercase"""
        if value:
            return value.upper()
        return value
    
    def validate_gstin(self, value):
        """Validate GSTIN format and auto-convert to uppercase"""
        if value:
            value = value.upper()
            if len(value) != 15:
                raise serializers.ValidationError("GSTIN must be 15 characters long")
            
            # Check for uniqueness, excluding current instance if updating
            queryset = Retailer.objects.filter(gstin=value, is_deleted=False)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise serializers.ValidationError("Retailer with this GSTIN already exists.")
        
        return value
    
    def validate_pan(self, value):
        """Validate PAN format and auto-convert to uppercase"""
        if value:
            value = value.upper()
            if len(value) != 10:
                raise serializers.ValidationError("PAN must be 10 characters long")
        return value
    
    def validate(self, data):
        """Validate hierarchy if enforced"""
        # Get active channel partner configuration
        try:
            config = ChannelPartnerConfiguration.objects.filter(is_active=True, is_deleted=False).first()
        except ChannelPartnerConfiguration.DoesNotExist:
            config = None
        
        distributor = data.get('distributor')
        
        # Check if hierarchy is enforced AND distributor is enabled
        if config and config.enforce_channel_hierarchy and config.enable_distributor and not distributor:
            raise serializers.ValidationError({
                'distributor_id': 'Distributor is required when channel hierarchy is enforced and distributor is enabled'
            })
        
        return data
    
    def create(self, validated_data):
        validated_data.pop('location_states', [])
        validated_data.pop('location_cities', [])
        validated_data.pop('location_areas', [])
        
        # Extract M2M user fields
        user_password = validated_data.pop('user_password', '')
        user_company_ids = validated_data.pop('user_company_ids', [])
        user_location_ids = validated_data.pop('user_location_ids', [])
        user_group_ids = validated_data.pop('user_group_ids', [])
        
        with transaction.atomic():
            retailer = Retailer.objects.create(**validated_data)
            
            # Set M2M user fields on model
            if user_company_ids:
                retailer.user_companies.set(user_company_ids)
            if user_location_ids:
                retailer.user_locations.set(user_location_ids)
            if user_group_ids:
                retailer.user_groups.set(user_group_ids)
            
            # Auto-create user
            self._create_user_for_retailer(retailer, user_password)
        
        return retailer
    
    def _create_user_for_retailer(self, retailer, password=''):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        username = (retailer.user_username or '').strip() or retailer.code
        password = password.strip() if password else username
        
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({'user_username': f'Username "{username}" is already taken.'})
        
        phone = (retailer.user_phone or '').strip()
        if phone and User.objects.filter(phone=phone, is_active=True).exists():
            raise serializers.ValidationError({'user_phone': f'Phone number "{phone}" is already in use.'})
        
        user = User(
            username=username,
            first_name=retailer.name,
            phone=phone or None,
            channel_partner_type='RETAILER',
            has_all_companies=retailer.user_has_all_companies,
            has_all_locations=retailer.user_has_all_locations,
            device_access=retailer.user_device_access or 3,
            is_active=True,
        )
        user.set_password(password)
        user.save()
        
        user.retailer = retailer
        user.save(update_fields=['retailer_id'])
        
        if retailer.user_companies.exists():
            user.companies.set(retailer.user_companies.all())
        if retailer.user_locations.exists():
            user.locations.set(retailer.user_locations.all())
        if retailer.user_groups.exists():
            user.groups.set(retailer.user_groups.all())
    
    def update(self, instance, validated_data):
        validated_data.pop('location_states', None)
        validated_data.pop('location_cities', None)
        validated_data.pop('location_areas', None)
        
        # Extract M2M user fields
        validated_data.pop('user_password', None)
        user_company_ids = validated_data.pop('user_company_ids', None)
        user_location_ids = validated_data.pop('user_location_ids', None)
        user_group_ids = validated_data.pop('user_group_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class PriceBookDocumentSerializer(serializers.ModelSerializer):
    """Serializer for PriceBookDocument with summary information"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    pending_approver_names = serializers.SerializerMethodField()
    
    class Meta:
        model = PriceBookDocument
        fields = (
            'id', 'document_number', 'document_date', 'location_type',
            'cp_filter_state', 'cp_filter_city', 'cp_filter_area',
            'selected_categories', 'selected_brands',
            'status', 'status_display',
            'effective_from', 'effective_to', 'total_entries', 'remarks',
            'pending_approver_names',
            'created_on', 'modified_on'
        )
        read_only_fields = ('id', 'total_entries', 'status_display', 'pending_approver_names', 'created_on', 'modified_on')
    
    def get_pending_approver_names(self, obj):
        """Get pending approver names"""
        from Core.Users.serializers import get_pending_approver_names
        result = get_pending_approver_names(obj)
        if obj.authorized_status == 1:
            return result if result else 'TEST: No approvers found'
        return result


class PriceBookDocumentDetailSerializer(serializers.ModelSerializer):
    """Serializer for PriceBookDocument with all related price entries"""
    price_entries = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = PriceBookDocument
        fields = (
            'id', 'document_number', 'document_date', 'location_type',
            'cp_filter_state', 'cp_filter_city', 'cp_filter_area',
            'selected_categories', 'selected_brands',
            'status', 'status_display',
            'effective_from', 'effective_to', 'total_entries', 'remarks',
            'price_entries', 'created_on', 'modified_on'
        )
        read_only_fields = ('id', 'total_entries', 'status_display', 'created_on', 'modified_on')
    
    def get_price_entries(self, obj):
        """Get all price book entries for this document"""
        entries = obj.price_entries.filter(is_deleted=False).select_related(
            'item', 'state', 'city', 'area',
            'superstockist', 'distributor', 'retailer'
        )
        return PriceBookSerializer(entries, many=True).data


class PriceBookSerializer(DuplicateValidationSerializerMixin, serializers.ModelSerializer):
    """Full serializer for PriceBook with all related data"""
    
    # Read-only display fields
    item_name = serializers.CharField(source='item.name', read_only=True)
    item_code = serializers.CharField(source='item.code', read_only=True)
    document_number = serializers.SerializerMethodField()
    document_date = serializers.SerializerMethodField()
    state_name = serializers.CharField(source='state.name', read_only=True, allow_null=True)
    city_name = serializers.CharField(source='city.name', read_only=True, allow_null=True)
    area_name = serializers.CharField(source='area.name', read_only=True, allow_null=True)
    superstockist_name = serializers.CharField(source='superstockist.name', read_only=True, allow_null=True)
    distributor_name = serializers.CharField(source='distributor.name', read_only=True, allow_null=True)
    retailer_name = serializers.CharField(source='retailer.name', read_only=True, allow_null=True)
    
    # Write-only FK fields
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.filter(is_deleted=False),
        source='company',
        write_only=True,
        required=False,
        allow_null=True
    )
    document_id = serializers.PrimaryKeyRelatedField(
        queryset=PriceBookDocument.objects.all(),
        source='document',
        write_only=True,
        required=False,
        allow_null=True
    )
    item_id = serializers.PrimaryKeyRelatedField(
        queryset=Item.objects.filter(is_deleted=False),
        source='item',
        write_only=True
    )
    state_id = serializers.PrimaryKeyRelatedField(
        queryset=State.objects.filter(is_deleted=False),
        source='state',
        write_only=True,
        required=False,
        allow_null=True
    )
    city_id = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.filter(is_deleted=False),
        source='city',
        write_only=True,
        required=False,
        allow_null=True
    )
    area_id = serializers.PrimaryKeyRelatedField(
        queryset=Area.objects.filter(is_deleted=False),
        source='area',
        write_only=True,
        required=False,
        allow_null=True
    )
    superstockist_id = serializers.PrimaryKeyRelatedField(
        queryset=Superstockist.objects.filter(is_deleted=False),
        source='superstockist',
        write_only=True,
        required=False,
        allow_null=True
    )
    distributor_id = serializers.PrimaryKeyRelatedField(
        queryset=Distributor.objects.filter(is_deleted=False),
        source='distributor',
        write_only=True,
        required=False,
        allow_null=True
    )
    retailer_id = serializers.PrimaryKeyRelatedField(
        queryset=Retailer.objects.filter(is_deleted=False),
        source='retailer',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    # Computed fields
    scope_display = serializers.CharField(source='get_scope_display', read_only=True)
    margin_percentage = serializers.DecimalField(
        source='get_margin_percentage',
        max_digits=5,
        decimal_places=2,
        read_only=True
    )
    
    # Explicit DateField definitions
    effective_from = serializers.DateField(required=True)
    effective_to = serializers.DateField(required=False, allow_null=True)
    
    class Meta:
        model = PriceBook
        fields = (
            'id', 'code', 'company', 'company_id', 'document', 'document_id', 'item', 'item_id', 'item_name', 'item_code',
            'document_number', 'document_date',
            'price_type', 'state', 'state_id', 'state_name',
            'city', 'city_id', 'city_name', 'area', 'area_id', 'area_name',
            'superstockist', 'superstockist_id', 'superstockist_name',
            'distributor', 'distributor_id', 'distributor_name',
            'retailer', 'retailer_id', 'retailer_name',
            'base_price', 'selling_price', 'mrp', 'discount_percentage',
            'effective_from', 'effective_to', 'is_active',
            'erp_code', 'erp_id', 'remarks', 'scope_display', 'margin_percentage',
            'created_on', 'modified_on'
        )
        read_only_fields = ('id', 'company', 'document', 'item', 'created_on', 'modified_on')
        extra_kwargs = {
            'base_price': {'required': False, 'allow_null': True},
            'mrp': {'required': False, 'allow_null': True},
        }
    
    def get_document_number(self, obj):
        """Get document number from related document"""
        return obj.document.document_number if obj.document else None
    
    def get_document_date(self, obj):
        """Get document date from related document"""
        return obj.document.document_date if obj.document else None
    
    def to_internal_value(self, data):
        """Handle empty string to None conversion for date fields"""
        if 'effective_to' in data and data['effective_to'] == '':
            data['effective_to'] = None
        return super().to_internal_value(data)
    
    def validate_code(self, value):
        """Auto-convert code to uppercase"""
        if value:
            return value.upper()
        return value
    
    def validate(self, data):
        """Custom validation"""
        # Validate price relationships
        base_price = data.get('base_price')
        selling_price = data.get('selling_price')
        mrp = data.get('mrp')
        
        if base_price and selling_price and base_price > selling_price:
            raise serializers.ValidationError({
                'selling_price': 'Selling price must be greater than or equal to base price'
            })
        
        if selling_price and mrp and selling_price > mrp:
            raise serializers.ValidationError({
                'mrp': 'MRP must be greater than or equal to selling price'
            })
        
        # Validate date range
        effective_from = data.get('effective_from')
        effective_to = data.get('effective_to')
        if effective_from and effective_to and effective_from > effective_to:
            raise serializers.ValidationError({
                'effective_to': 'Effective to date must be after effective from date'
            })
        
        return data


class PriceBookMiniSerializer(serializers.ModelSerializer):
    """Minimal serializer for dropdowns"""
    item_name = serializers.CharField(source='item.name', read_only=True)
    scope_display = serializers.CharField(source='get_scope_display', read_only=True)
    
    class Meta:
        model = PriceBook
        fields = ('id', 'code', 'item_name', 'scope_display', 'selling_price', 'mrp')


class PriceBookHistorySerializer(serializers.ModelSerializer):
    """Serializer for Price Book History"""
    price_book_code = serializers.CharField(source='price_book.code', read_only=True)
    price_book_item = serializers.CharField(source='price_book.item.name', read_only=True)
    document_number = serializers.CharField(source='price_book.document.document_number', read_only=True, allow_null=True)
    document_date = serializers.DateField(source='price_book.document.document_date', read_only=True, allow_null=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    change_summary = serializers.CharField(source='get_change_summary', read_only=True)
    
    class Meta:
        model = PriceBookHistory
        fields = (
            'document_number', 'document_date', 'price_book_code', 'price_book_item',
            'action', 'action_display', 'changes', 'change_summary',
            'base_price', 'selling_price', 'mrp', 'discount_percentage',
            'effective_from', 'effective_to', 'is_active', 'remarks',
            'created_on', 'created_by_type', 'created_by_identifier'
        )
        read_only_fields = (
            'document_number', 'document_date', 'price_book_code', 'price_book_item',
            'action', 'action_display', 'changes', 'change_summary',
            'base_price', 'selling_price', 'mrp', 'discount_percentage',
            'effective_from', 'effective_to', 'is_active', 'remarks',
            'created_on', 'created_by_type', 'created_by_identifier'
        )


# ============================================================================
# SCHEME SERIALIZERS
# ============================================================================

class SchemeConditionSerializer(serializers.ModelSerializer):
    """Serializer for Scheme Conditions"""
    scheme = serializers.PrimaryKeyRelatedField(queryset=Scheme.objects.all(), required=False, allow_null=True)
    item_name = serializers.CharField(source='item.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    condition_type_display = serializers.CharField(source='get_condition_type_display', read_only=True)
    
    class Meta:
        model = SchemeCondition
        fields = (
            'id', 'scheme', 'condition_type', 'condition_type_display',
            'value_from', 'value_to', 'item', 'item_name',
            'category', 'category_name', 'items', 'logical_operator'
        )
        extra_kwargs = {
            'scheme': {'required': False},
        }
    
    def validate(self, data):
        condition_type = data.get('condition_type')
        value_from = data.get('value_from')
        value_to = data.get('value_to')
        
        # For range conditions, validate value_from <= value_to
        if condition_type in ['QUANTITY_RANGE', 'VALUE_RANGE']:
            if value_from and value_to and value_from > value_to:
                raise serializers.ValidationError(
                    {"value_to": "value_to must be >= value_from"}
                )
        
        # Map frontend 'items' array to combo_items for ITEM_COMBO
        if condition_type == 'ITEM_COMBO' and not data.get('items'):
            data['items'] = []
        
        return data


class SchemeBenefitSerializer(serializers.ModelSerializer):
    """Serializer for Scheme Benefits"""
    scheme = serializers.PrimaryKeyRelatedField(queryset=Scheme.objects.all(), required=False, allow_null=True)
    free_item_name = serializers.CharField(source='free_item.name', read_only=True)
    apply_to_item_name = serializers.CharField(source='apply_to_item.name', read_only=True)
    apply_to_category_name = serializers.CharField(source='apply_to_category.name', read_only=True)
    benefit_type_display = serializers.CharField(source='get_benefit_type_display', read_only=True)
    
    class Meta:
        model = SchemeBenefit
        fields = (
            'id', 'scheme', 'benefit_type', 'benefit_type_display',
            'discount_value', 'max_discount_amount',
            'free_item', 'free_item_name', 'free_quantity',
            'apply_to_item', 'apply_to_item_name',
            'apply_to_category', 'apply_to_category_name', 'apply_to_all'
        )
        extra_kwargs = {
            'scheme': {'required': False},
        }
    
    def validate(self, data):
        benefit_type = data.get('benefit_type')
        apply_to_all = data.get('apply_to_all', False)
        apply_to_item = data.get('apply_to_item')
        apply_to_category = data.get('apply_to_category')
        
        # Validate apply_to fields
        # if not apply_to_all:
        #     if not apply_to_item and not apply_to_category:
        #         raise serializers.ValidationError(
        #             "Either apply_to_item, apply_to_category, or apply_to_all must be set"
        #         )
        
        return data


class SchemeApplicabilitySerializer(serializers.ModelSerializer):
    """Serializer for Scheme Applicability"""
    scheme = serializers.PrimaryKeyRelatedField(queryset=Scheme.objects.all(), required=False, allow_null=True)
    state_name = serializers.CharField(source='state.name', read_only=True)
    city_name = serializers.CharField(source='city.name', read_only=True)
    area_name = serializers.CharField(source='area.name', read_only=True)
    retailer_name = serializers.CharField(source='retailer.name', read_only=True)
    distributor_name = serializers.CharField(source='distributor.name', read_only=True)
    superstockist_name = serializers.CharField(source='superstockist.name', read_only=True)
    customer_type_display = serializers.CharField(source='get_customer_type_display', read_only=True)
    
    class Meta:
        model = SchemeApplicability
        fields = (
            'id', 'scheme', 'state', 'state_name', 'city', 'city_name',
            'area', 'area_name', 'customer_type', 'customer_type_display',
            'retailer', 'retailer_name', 'distributor', 'distributor_name',
            'superstockist', 'superstockist_name', 'apply_to_all'
        )
        extra_kwargs = {
            'scheme': {'required': False},
        }


class SchemeItemSerializer(serializers.ModelSerializer):
    """Serializer for Scheme Items"""
    item_name = serializers.CharField(source='item.name', read_only=True)
    item_code = serializers.CharField(source='item.code', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_code = serializers.CharField(source='category.code', read_only=True)
    
    class Meta:
        model = SchemeItem
        fields = (
            'id', 'scheme', 'item', 'item_name', 'item_code',
            'category', 'category_name', 'category_code', 'include_all_items'
        )
        read_only_fields = ('scheme',)


class SchemeHistorySerializer(serializers.ModelSerializer):
    """Serializer for Scheme History"""
    scheme_code = serializers.CharField(source='scheme.code', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    change_summary = serializers.CharField(source='get_change_summary', read_only=True)
    
    class Meta:
        model = SchemeHistory
        fields = (
            'id', 'scheme', 'scheme_code', 'action', 'action_display',
            'changes', 'change_summary', 'changed_by_type',
            'changed_by_identifier', 'changed_at'
        )
        read_only_fields = fields


class SchemeSerializer(serializers.ModelSerializer):
    """Full Serializer for Schemes with nested objects"""
    code = serializers.CharField(required=False, allow_blank=True)
    company = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.filter(is_deleted=False),
        required=False,
        allow_null=True
    )
    conditions = SchemeConditionSerializer(many=True, required=False)
    benefits = SchemeBenefitSerializer(many=True, required=False)
    applicability = SchemeApplicabilitySerializer(many=True, required=False)
    items = SchemeItemSerializer(many=True, required=False)
    history = SchemeHistorySerializer(many=True, read_only=True)
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    scheme_type_display = serializers.CharField(source='get_scheme_type_display', read_only=True)
    authorized_status_name = serializers.CharField(source='get_authorized_status_display', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.first_name', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    pending_approver_names = serializers.SerializerMethodField()
    
    class Meta:
        model = Scheme
        fields = (
            'id', 'code', 'name', 'description', 'scheme_type', 'scheme_type_display',
            'status', 'status_display', 'priority', 'is_stackable', 'max_applications',
            'effective_from', 'effective_to', 'company', 'company_name',
            'max_discount_amount', 'requires_approval',
            'approved_by', 'approved_by_name', 'approved_at',
            'authorized_status', 'authorized_status_name', 'authorized_level', 'authorized_by_type',
            'authorized_by_identifier', 'authorized_on', 'current_authorized_level',
            'current_authorized_status', 'current_authorized_by_type', 'current_authorized_by_identifier',
            'current_authorized_on',
            'pending_approver_names',
            'conditions', 'benefits', 'applicability', 'items', 'history',
            'created_on', 'modified_on', 'created_by_type', 'created_by_identifier'
        )
        read_only_fields = (
            'id', 'history', 'company_name', 'status_display',
            'scheme_type_display', 'approved_by_name', 'created_on', 'modified_on',
            'authorized_status', 'authorized_status_name', 'authorized_level', 'authorized_by_type',
            'authorized_by_identifier', 'authorized_on', 'current_authorized_level',
            'current_authorized_status', 'current_authorized_by_type', 'current_authorized_by_identifier',
            'current_authorized_on', 'pending_approver_names'
        )
    
    def get_pending_approver_names(self, obj):
        """Get pending approver names"""
        from Core.Users.serializers import get_pending_approver_names
        result = get_pending_approver_names(obj)
        if obj.authorized_status == 1:
            return result if result else 'TEST: No approvers found'
        return result
    
    def create(self, validated_data):
        """Create scheme with nested objects"""
        conditions_data = validated_data.pop('conditions', [])
        benefits_data = validated_data.pop('benefits', [])
        applicability_data = validated_data.pop('applicability', [])
        items_data = validated_data.pop('items', [])
        
        # Get raw conditions from request to extract combo items
        
        scheme = Scheme.objects.create(**validated_data)
        
        # Create nested objects
        for condition_data in conditions_data:
            condition_data['scheme'] = scheme
            SchemeCondition.objects.create(**condition_data)
        
        for benefit_data in benefits_data:
            benefit_data['scheme'] = scheme
            SchemeBenefit.objects.create(**benefit_data)
        
        for applicability_data_item in applicability_data:
            applicability_data_item['scheme'] = scheme
            SchemeApplicability.objects.create(**applicability_data_item)
        
        for item_data in items_data:
            item_data['scheme'] = scheme
            SchemeItem.objects.create(**item_data)
        
        # Create history record
        SchemeHistory.objects.create(
            scheme=scheme,
            action='CREATED',
            changed_by_type=self.context.get('request').user.__class__.__name__ if self.context.get('request') else None,
            changed_by_identifier=str(self.context.get('request').user) if self.context.get('request') else None
        )
        
        return scheme
    
    def update(self, instance, validated_data):
        """Update scheme with nested objects"""
        conditions_data = validated_data.pop('conditions', None)
        benefits_data = validated_data.pop('benefits', None)
        applicability_data = validated_data.pop('applicability', None)
        items_data = validated_data.pop('items', None)
        
        # Track changes for history (old vs new)
        def _to_json_safe(value):
            from datetime import date, datetime
            from decimal import Decimal
            import uuid
            from django.db import models

            if isinstance(value, (datetime, date)):
                return value.isoformat()
            if isinstance(value, Decimal):
                return str(value)
            if isinstance(value, uuid.UUID):
                return str(value)
            if isinstance(value, models.Model):
                return str(value.pk)
            if isinstance(value, dict):
                return {k: _to_json_safe(v) for k, v in value.items()}
            if isinstance(value, (list, tuple)):
                return [_to_json_safe(v) for v in value]
            return value

        changes_payload = {}
        for attr, value in validated_data.items():
            old_val = getattr(instance, attr, None)
            if old_val != value:
                changes_payload[attr] = {
                    "old": _to_json_safe(old_val),
                    "new": _to_json_safe(value),
                }
            setattr(instance, attr, value)
        instance.save()
        
        # Update nested objects if provided
        if conditions_data is not None:
            instance.conditions.all().delete()
            for condition_data in conditions_data:
                condition_data['scheme'] = instance
                SchemeCondition.objects.create(**condition_data)
        
        if benefits_data is not None:
            instance.benefits.all().delete()
            for benefit_data in benefits_data:
                benefit_data['scheme'] = instance
                SchemeBenefit.objects.create(**benefit_data)
        
        if applicability_data is not None:
            instance.applicability.all().delete()
            for applicability_data_item in applicability_data:
                applicability_data_item['scheme'] = instance
                SchemeApplicability.objects.create(**applicability_data_item)
        
        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                item_data['scheme'] = instance
                SchemeItem.objects.create(**item_data)
        
        # Create history record
        SchemeHistory.objects.create(
            scheme=instance,
            action='UPDATED',
            changes=changes_payload,
            changed_by_type=self.context.get('request').user.__class__.__name__ if self.context.get('request') else None,
            changed_by_identifier=str(self.context.get('request').user) if self.context.get('request') else None
        )
        
        return instance
    
    def validate(self, data):
        """Validate scheme data"""
        effective_from = data.get('effective_from')
        effective_to = data.get('effective_to')
        scheme_type = data.get('scheme_type') or getattr(self.instance, 'scheme_type', None)
        
        if effective_from and effective_to:
            if effective_to < effective_from:
                raise serializers.ValidationError(
                    {"effective_to": "effective_to must be >= effective_from"}
                )

        if scheme_type:
            from Masters.scheme_constraints import get_allowed_benefit_types, get_allowed_condition_types

            allowed_condition_types = set(get_allowed_condition_types(scheme_type))
            allowed_benefit_types = set(get_allowed_benefit_types(scheme_type))

            conditions = data.get('conditions')
            if conditions is not None and allowed_condition_types:
                invalid_conditions = sorted({
                    condition.get('condition_type')
                    for condition in conditions
                    if condition.get('condition_type') and condition.get('condition_type') not in allowed_condition_types
                })
                if invalid_conditions:
                    raise serializers.ValidationError({
                        "conditions": (
                            f"Condition types not allowed for scheme_type {scheme_type}: "
                            f"{', '.join(invalid_conditions)}"
                        )
                    })

            benefits = data.get('benefits')
            if benefits is not None and allowed_benefit_types:
                invalid_benefits = sorted({
                    benefit.get('benefit_type')
                    for benefit in benefits
                    if benefit.get('benefit_type') and benefit.get('benefit_type') not in allowed_benefit_types
                })
                if invalid_benefits:
                    raise serializers.ValidationError({
                        "benefits": (
                            f"Benefit types not allowed for scheme_type {scheme_type}: "
                            f"{', '.join(invalid_benefits)}"
                        )
                    })

        benefits = data.get('benefits')
        if benefits is None or len(benefits) == 0:
            raise serializers.ValidationError({
                "benefits": "At least one benefit is required."
            })
        
        return data


class SchemeMiniSerializer(serializers.ModelSerializer):
    """Minimal serializer for Scheme dropdowns"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    scheme_type_display = serializers.CharField(source='get_scheme_type_display', read_only=True)

    class Meta:
        model = Scheme
        fields = ('id', 'code', 'name', 'priority', 'status', 'status_display', 'scheme_type', 'scheme_type_display')


# ============================================================================
# Project Master serializers — SRS Module 6
# ============================================================================

class ProjectSerializer(serializers.ModelSerializer):
    project_type_display = serializers.CharField(source='get_project_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approval_type_display = serializers.CharField(source='get_approval_type_display', read_only=True)

    # ponytail: permissive — accepts free text where model has choices/FK validators
    project_type = serializers.CharField(allow_blank=True, required=False)
    approval_type = serializers.CharField(allow_blank=True, required=False)
    location = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    sub = serializers.ImageField(allow_null=True, required=False)

    class Meta:
        model = Project
        fields = (
            'id', 'code', 'name', 'developer_name',
            'project_type', 'project_type_display',
            'location',
            'approval_type', 'approval_type_display',
            'status', 'status_display', 'is_active', 'is_deleted',
            'sub',
            'created_on', 'modified_on',
        )
        read_only_fields = ('code', 'is_deleted', 'created_on', 'modified_on')


class ProjectMiniSerializer(serializers.ModelSerializer):
    """Minimal serializer for Project dropdowns (used by Site Visit, Booking, etc.)."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    project_type_display = serializers.CharField(source='get_project_type_display', read_only=True)

    class Meta:
        model = Project
        fields = ('id', 'code', 'name', 'status', 'status_display',
                  'project_type', 'project_type_display', 'is_active')
