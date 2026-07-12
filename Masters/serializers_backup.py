from rest_framework import serializers
from .models import (
    Country, State, City, Area, Company, Location, WareHouse, UOM,
    Category, Brand, Tax, Item, ItemTaxComposition, ItemUOMConversion,
    ItemFieldConfiguration, OutletType, Superstockist, SuperstockistLocation,
    Distributor, DistributorLocation, Retailer, RetailerLocation,
    ChannelPartnerConfiguration, PriceBook, PriceBookDocument, PriceBookHistory
)

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


class CompanyMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ('id', 'name')


class LocationMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ('id', 'name')


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
        fields = ['id', 'code', 'name', 'barcode']


class OutletTypeMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutletType
        fields = ['id', 'name']


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


class LocationSerializer(serializers.ModelSerializer):
    company = CompanyMiniSerializer(read_only=True)
    company_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source='company', 
        queryset=Company.objects.filter(is_deleted=False),
        required=False, allow_null=True
    )
    city = CityMiniSerializer(read_only=True)
    city_id = serializers.PrimaryKeyRelatedField(write_only=True, source='city', queryset=City.objects.filter(is_deleted=False))
    state = StateMiniSerializer(read_only=True)
    state_id = serializers.PrimaryKeyRelatedField(write_only=True, source='state', queryset=State.objects.filter(is_deleted=False))
    country = CountryMiniSerializer(read_only=True)
    country_id = serializers.PrimaryKeyRelatedField(write_only=True, source='country', queryset=Country.objects.filter(is_deleted=False))
    
    class Meta:
        model = Location
        fields = '__all__'



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
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
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


class OutletTypeSerializer(serializers.ModelSerializer):
    code = serializers.CharField(max_length=30, required=True, allow_blank=False)
    
    class Meta:
        model = OutletType
        fields = ['id', 'code', 'name', 'erp_code', 'erp_id', 'created_on', 'modified_on']
        read_only_fields = ['id', 'created_on', 'modified_on']
    
    def validate_code(self, value):
        if value:
            value = value.upper()
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


class ItemSerializer(serializers.ModelSerializer):
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
            'current_tax', 'uom_conversions',
            'created_on', 'modified_on'
        ]
        read_only_fields = ['created_on', 'modified_on']
    
    def validate_code(self, value):
        if value:
            value = value.upper()
        return value
    
    def validate_barcode(self, value):
        if value:
            value = value.upper()
        return value

    def create(self, validated_data):
        """
        Create item and handle UOM conversions in single transaction
        """
        # Extract related data
        uom_conversions_data = validated_data.pop('uom_conversions', [])
        
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
        
        return item
    
    def update(self, instance, validated_data):
        """
        Update item and handle UOM conversions in single transaction
        """
        # Extract related data
        uom_conversions_data = validated_data.pop('uom_conversions', None)
        
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

class SuperstockistLocationSerializer(serializers.ModelSerializer):
    state_name = serializers.CharField(source='state.name', read_only=True)
    city_name = serializers.CharField(source='city.name', read_only=True)
    area_name = serializers.CharField(source='area.name', read_only=True)
    
    class Meta:
        model = SuperstockistLocation
        fields = ('id', 'state', 'state_name', 'city', 'city_name', 'area', 'area_name')


class SuperstockistSerializer(serializers.ModelSerializer):
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
    area_id = serializers.PrimaryKeyRelatedField(write_only=True, source='area', queryset=Area.objects.filter(is_deleted=False), required=False, allow_null=True)
    shipping_state_id = serializers.PrimaryKeyRelatedField(write_only=True, source='shipping_state', queryset=State.objects.filter(is_deleted=False), required=False, allow_null=True)
    shipping_city_id = serializers.PrimaryKeyRelatedField(write_only=True, source='shipping_city', queryset=City.objects.filter(is_deleted=False), required=False, allow_null=True)
    shipping_area_id = serializers.PrimaryKeyRelatedField(write_only=True, source='shipping_area', queryset=Area.objects.filter(is_deleted=False), required=False, allow_null=True)
    company_id = serializers.PrimaryKeyRelatedField(write_only=True, source='company', queryset=Company.objects.filter(is_deleted=False), required=False, allow_null=True)
    
    locations = SuperstockistLocationSerializer(many=True, read_only=True)
    location_summary = serializers.SerializerMethodField(read_only=True)
    
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
            'contact_person', 'phone', 'email', 'mobile',
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
            'is_active', 'effective_from', 'effective_to',
            'erp_code',
            'company', 'company_id', 'company_name',
            'created_on', 'modified_on',
            'locations', 'location_summary',
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
    
    def create(self, validated_data):
        """Create superstockist with locations"""
        # Extract location data
        location_states = validated_data.pop('location_states', [])
        location_cities = validated_data.pop('location_cities', [])
        location_areas = validated_data.pop('location_areas', [])
        
        # Create superstockist
        superstockist = Superstockist.objects.create(**validated_data)
        
        # Create location mappings
        self._save_locations(superstockist, location_states, location_cities, location_areas)
        
        return superstockist
    
    def update(self, instance, validated_data):
        """Update superstockist with locations"""
        # Extract location data
        location_states = validated_data.pop('location_states', None)
        location_cities = validated_data.pop('location_cities', None)
        location_areas = validated_data.pop('location_areas', None)
        
        # Update superstockist fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update locations if provided
        if location_states is not None or location_cities is not None or location_areas is not None:
            self._save_locations(
                instance, 
                location_states or [], 
                location_cities or [], 
                location_areas or []
            )
        
        return instance
    
    def _save_locations(self, superstockist, state_ids, city_ids, area_ids):
        """Helper method to save location mappings"""
        from .models import SuperstockistLocation, State, City, Area
        
        # Clear existing locations
        SuperstockistLocation.objects.filter(superstockist=superstockist).delete()
        
        # Create new location records
        locations_to_create = []
        
        # Add state-level locations
        for state_id in state_ids:
            locations_to_create.append(
                SuperstockistLocation(
                    superstockist=superstockist,
                    state_id=state_id,
                    city=None,
                    area=None
                )
            )
        
        # Add city-level locations
        for city_id in city_ids:
            try:
                city = City.objects.get(id=city_id)
                locations_to_create.append(
                    SuperstockistLocation(
                        superstockist=superstockist,
                        state=city.state,
                        city=city,
                        area=None
                    )
                )
            except City.DoesNotExist:
                pass
        
        # Add area-level locations
        for area_id in area_ids:
            try:
                area = Area.objects.get(id=area_id)
                locations_to_create.append(
                    SuperstockistLocation(
                        superstockist=superstockist,
                        state=area.state,
                        city=area.city,
                        area=area
                    )
                )
            except Area.DoesNotExist:
                pass
        
        # Bulk create all locations
        if locations_to_create:
            SuperstockistLocation.objects.bulk_create(locations_to_create)


class SuperstockistMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Superstockist
        fields = ('id', 'code', 'name')


class DistributorLocationSerializer(serializers.ModelSerializer):
    state_name = serializers.CharField(source='state.name', read_only=True)
    city_name = serializers.CharField(source='city.name', read_only=True)
    area_name = serializers.CharField(source='area.name', read_only=True)
    
    class Meta:
        model = DistributorLocation
        fields = ('id', 'state', 'state_name', 'city', 'city_name', 'area', 'area_name')


class DistributorSerializer(serializers.ModelSerializer):
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
    superstockist = serializers.PrimaryKeyRelatedField(read_only=True)
    superstockist_name = serializers.CharField(source='superstockist.name', read_only=True)
    company = serializers.PrimaryKeyRelatedField(read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    # Write-only fields for updates
    state_id = serializers.PrimaryKeyRelatedField(write_only=True, source='state', queryset=State.objects.filter(is_deleted=False))
    city_id = serializers.PrimaryKeyRelatedField(write_only=True, source='city', queryset=City.objects.filter(is_deleted=False), required=False, allow_null=True)
    area_id = serializers.PrimaryKeyRelatedField(write_only=True, source='area', queryset=Area.objects.filter(is_deleted=False), required=False, allow_null=True)
    shipping_state_id = serializers.PrimaryKeyRelatedField(write_only=True, source='shipping_state', queryset=State.objects.filter(is_deleted=False), required=False, allow_null=True)
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
    
    locations = DistributorLocationSerializer(many=True, read_only=True)
    location_summary = serializers.SerializerMethodField(read_only=True)
    
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
        model = Distributor
        fields = (
            'id', 'code', 'name',
            'superstockist', 'superstockist_id', 'superstockist_name',
            'contact_person', 'phone', 'email', 'mobile',
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
            'is_active', 'effective_from', 'effective_to',
            'erp_code',
            'company', 'company_id', 'company_name',
            'created_on', 'modified_on',
            'locations', 'location_summary',
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
        
        return data
    
    def create(self, validated_data):
        """Create distributor with locations"""
        # Extract location data
        location_states = validated_data.pop('location_states', [])
        location_cities = validated_data.pop('location_cities', [])
        location_areas = validated_data.pop('location_areas', [])
        
        # Create distributor
        distributor = Distributor.objects.create(**validated_data)
        
        # Create location mappings
        self._save_locations(distributor, location_states, location_cities, location_areas)
        
        return distributor
    
    def update(self, instance, validated_data):
        """Update distributor with locations"""
        # Extract location data
        location_states = validated_data.pop('location_states', None)
        location_cities = validated_data.pop('location_cities', None)
        location_areas = validated_data.pop('location_areas', None)
        
        # Update distributor fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update locations if provided
        if location_states is not None or location_cities is not None or location_areas is not None:
            self._save_locations(
                instance, 
                location_states or [], 
                location_cities or [], 
                location_areas or []
            )
        
        return instance
    
    def _save_locations(self, distributor, state_ids, city_ids, area_ids):
        """Helper method to save location mappings"""
        from .models import DistributorLocation, State, City, Area
        
        # Clear existing locations
        DistributorLocation.objects.filter(distributor=distributor).delete()
        
        # Create new location records
        locations_to_create = []
        
        # Add state-level locations
        for state_id in state_ids:
            locations_to_create.append(
                DistributorLocation(
                    distributor=distributor,
                    state_id=state_id,
                    city=None,
                    area=None
                )
            )
        
        # Add city-level locations
        for city_id in city_ids:
            try:
                city = City.objects.get(id=city_id)
                locations_to_create.append(
                    DistributorLocation(
                        distributor=distributor,
                        state=city.state,
                        city=city,
                        area=None
                    )
                )
            except City.DoesNotExist:
                pass
        
        # Add area-level locations
        for area_id in area_ids:
            try:
                area = Area.objects.get(id=area_id)
                locations_to_create.append(
                    DistributorLocation(
                        distributor=distributor,
                        state=area.state,
                        city=area.city,
                        area=area
                    )
                )
            except Area.DoesNotExist:
                pass
        
        # Bulk create all locations
        if locations_to_create:
            DistributorLocation.objects.bulk_create(locations_to_create)


class DistributorMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Distributor
        fields = ('id', 'code', 'name')


class RetailerLocationSerializer(serializers.ModelSerializer):
    state_name = serializers.CharField(source='state.name', read_only=True)
    city_name = serializers.CharField(source='city.name', read_only=True)
    area_name = serializers.CharField(source='area.name', read_only=True)
    
    class Meta:
        model = RetailerLocation
        fields = ('id', 'state', 'state_name', 'city', 'city_name', 'area', 'area_name')


class RetailerSerializer(serializers.ModelSerializer):
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
    
    # Read-only names for display
    state_name = serializers.CharField(source='state.name', read_only=True)
    state_id = serializers.PrimaryKeyRelatedField(write_only=True, source='state', queryset=State.objects.filter(is_deleted=False))
    city_name = serializers.CharField(source='city.name', read_only=True, allow_null=True)
    city_id = serializers.PrimaryKeyRelatedField(write_only=True, source='city', queryset=City.objects.filter(is_deleted=False), required=False, allow_null=True)
    area_name = serializers.CharField(source='area.name', read_only=True, allow_null=True)
    area_id = serializers.PrimaryKeyRelatedField(write_only=True, source='area', queryset=Area.objects.filter(is_deleted=False), required=False, allow_null=True)
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
            'contact_person', 'phone', 'email', 'mobile',
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
            'is_active', 'effective_from', 'effective_to',
            'erp_code',
            'company', 'company_id', 'company_name',
            'created_on', 'modified_on',
            'locations'
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


class RetailerMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Retailer
        fields = ('id', 'code', 'name')


class PriceBookDocumentSerializer(serializers.ModelSerializer):
    """Serializer for PriceBookDocument with summary information"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = PriceBookDocument
        fields = (
            'id', 'document_number', 'document_date', 'location_type',
            'cp_filter_state', 'cp_filter_city', 'cp_filter_area',
            'status', 'status_display',
            'effective_from', 'effective_to', 'total_entries', 'remarks',
            'created_on', 'modified_on'
        )
        read_only_fields = ('id', 'total_entries', 'status_display', 'created_on', 'modified_on')


class PriceBookDocumentDetailSerializer(serializers.ModelSerializer):
    """Serializer for PriceBookDocument with all related price entries"""
    price_entries = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = PriceBookDocument
        fields = (
            'id', 'document_number', 'document_date', 'location_type',
            'cp_filter_state', 'cp_filter_city', 'cp_filter_area',
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


class PriceBookSerializer(serializers.ModelSerializer):
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
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    change_summary = serializers.CharField(source='get_change_summary', read_only=True)
    
    class Meta:
        model = PriceBookHistory
        fields = (
            'id', 'price_book', 'price_book_code', 'price_book_item',
            'action', 'action_display', 'changes', 'change_summary',
            'base_price', 'selling_price', 'mrp', 'discount_percentage',
            'effective_from', 'effective_to', 'is_active', 'remarks',
            'created_on', 'created_by_type', 'created_by_identifier'
        )
        read_only_fields = (
            'id', 'price_book', 'price_book_code', 'price_book_item',
            'action', 'action_display', 'changes', 'change_summary',
            'base_price', 'selling_price', 'mrp', 'discount_percentage',
            'effective_from', 'effective_to', 'is_active', 'remarks',
            'created_on', 'created_by_type', 'created_by_identifier'
        )


# ============================================================================
# SALES ORDER SERIALIZERS MOVED TO Sales APP
# ============================================================================
# The SalesOrderSerializer, SalesOrderItemSerializer, SalesOrderListSerializer,
# and SalesOrderHistorySerializer have been moved to the Sales app.
# If you need to reference them, import from:
# from Sales.serializers import SalesOrderSerializer, SalesOrderItemSerializer, etc.
# ============================================================================

