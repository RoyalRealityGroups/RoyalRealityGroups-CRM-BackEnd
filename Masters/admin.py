from django.contrib import admin

# Register your models here.

from django.contrib import admin

from import_export.admin import ImportExportMixin

from Core.Core.utils.utils import ac_filter

from .resources import *
from .models import *


# ==================== Geographic Master Admin ====================

@admin.register(Country)
class CountryAdmin(ImportExportMixin, admin.ModelAdmin):
    resource_class = CountryResource
    fields = ['code', 'name']
    list_display = ('id', 'code', 'name', 'created_on', 'modified_on')
    search_fields = ['code', 'name']
    ordering = ('name',)
    list_per_page = 25
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(State)
class StateAdmin(ImportExportMixin, admin.ModelAdmin):
    resource_class = StateResource
    fields = ['code', 'name', 'gst_code', 'country']
    list_display = ('id', 'code', 'name', 'gst_code', 'country', 'created_on', 'modified_on')
    list_filter = ['country']
    search_fields = ['code', 'name', 'gst_code', 'country__name']
    ordering = ('name',)
    list_per_page = 25
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(District)
class DistrictAdmin(ImportExportMixin, admin.ModelAdmin):
    resource_class = DistrictResource
    fields = ['code', 'name', 'state']
    list_display = ('id', 'code', 'name', 'state', 'created_on', 'modified_on')
    list_filter = ['state', 'state__country']
    search_fields = ['code', 'name', 'state__name']
    ordering = ('name',)
    list_per_page = 25
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Mandal)
class MandalAdmin(ImportExportMixin, admin.ModelAdmin):
    resource_class = MandalResource
    fields = ['code', 'name', 'district', 'state']
    list_display = ('id', 'code', 'name', 'district', 'state', 'created_on', 'modified_on')
    list_filter = ['state', 'district']
    search_fields = ['code', 'name', 'district__name', 'state__name']
    ordering = ('name',)
    list_per_page = 25
    readonly_fields = []
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(City)
class CityAdmin(ImportExportMixin, admin.ModelAdmin):
    resource_class = CityResource
    fields = ['code', 'name', 'state', 'district', 'mandal', 'pincode']
    list_display = ('id', 'code', 'name', 'state', 'district', 'mandal', 'pincode', 'created_on', 'modified_on')
    list_filter = ['state', 'district', 'mandal']
    search_fields = ['code', 'name', 'state__name', 'district__name', 'pincode']
    ordering = ('name',)
    list_per_page = 25
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Area)
class AreaAdmin(ImportExportMixin, admin.ModelAdmin):
    resource_class = AreaResource
    fields = ['code', 'name', 'city', 'mandal', 'district', 'state', 'pincode']
    list_display = ('id', 'code', 'name', 'city', 'district', 'mandal', 'state', 'pincode', 'created_on', 'modified_on')
    list_filter = ['state', 'district', 'city']
    search_fields = ['code', 'name', 'city__name', 'district__name', 'pincode']
    ordering = ('name',)
    list_per_page = 25
    readonly_fields = []
    
    def has_delete_permission(self, request, obj=None):
        return False




@admin.register(ChannelPartnerConfiguration)
class ChannelPartnerConfigurationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'enable_superstockist', 'enable_distributor', 'enable_retailer', 
                    'enforce_channel_hierarchy', 'is_active', 'created_on')
    list_filter = ['is_active', 'enable_superstockist', 'enable_distributor', 'enable_retailer', 
                   'enforce_channel_hierarchy']
    search_fields = ['name']
    readonly_fields = ('created_on', 'modified_on')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'is_active')
        }),
        ('Channel Partner Types', {
            'fields': ('enable_superstockist', 'enable_distributor', 'enable_retailer')
        }),
        ('Hierarchy Settings', {
            'fields': ('enforce_channel_hierarchy',)
        }),
        ('Timestamps', {
            'fields': ('created_on', 'modified_on'),
            'classes': ('collapse',)
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of configurations
        return False


class UOMAdmin(ImportExportMixin,admin.ModelAdmin):

    fields = ['code', 'name', 'remarks']
    list_display = ('id','code','name','created_on','modified_on',)
    # resource_class = StateResource
    search_fields = ['name', 'code']

    ordering=('created_on',)
    list_per_page=25

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        obj.save()

        
admin.site.register(UOM, UOMAdmin)


@admin.register(Category)
class CategoryAdmin(ImportExportMixin, admin.ModelAdmin):
    fields = ['code', 'name', 'parent', 'description', 'is_active']
    resource_class = CategoryResource
    list_display = ('id', 'code', 'name', 'parent', 'is_active', 'created_on')
    list_filter = ['is_active', 'created_on']
    search_fields = ['code', 'name']
    ordering = ('name',)
    list_per_page = 25
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Brand)
class BrandAdmin(ImportExportMixin, admin.ModelAdmin):
    fields = ['code', 'name', 'description', 'is_active']
    resource_class = BrandResource
    list_display = ('id', 'code', 'name', 'is_active', 'created_on')
    list_filter = ['is_active', 'created_on']
    search_fields = ['code', 'name']
    ordering = ('name',)
    list_per_page = 25
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Tax)
class TaxAdmin(ImportExportMixin, admin.ModelAdmin):
    resource_class = TaxResource
    fields = ['code', 'name', 'tax_type', 'tax_rate', 'description', 'is_active']
    list_display = ('id', 'code', 'name', 'tax_type', 'tax_rate', 'is_active', 'created_on')
    list_filter = ['is_active', 'tax_type', 'created_on']
    search_fields = ['code', 'name', 'tax_type']
    ordering = ('tax_rate', 'name')
    list_per_page = 25
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Item)
class ItemAdmin(ImportExportMixin, admin.ModelAdmin):
    resource_class = ItemResource
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'description', 'short_name', 'barcode', 'sku')
        }),
        ('Classification', {
            'fields': ('item_type', 'product_type', 'parent', 'category', 'brand')
        }),
        ('Unit of Measurement', {
            'fields': ('base_uom',)
        }),
        ('Tax & Legal', {
            'fields': ('hsn_code', 'sac_code', 'tax_category', 'cess_applicable', 'cess_rate')
        }),
        ('Pricing', {
            'fields': ('cost_price', 'selling_price', 'mrp', 'min_price', 'price_includes_tax')
        }),
        ('Inventory', {
            'fields': ('is_stockable', 'track_inventory', 'min_stock_level', 'max_stock_level', 'reorder_level', 'reorder_quantity')
        }),
        ('Specifications', {
            'fields': ('weight', 'weight_unit', 'length', 'width', 'height'),
            'classes': ('collapse',)
        }),
        ('Images', {
            'fields': ('image', 'additional_images'),
            'classes': ('collapse',)
        }),
        ('Business Flags', {
            'fields': ('is_active', 'is_saleable', 'is_purchasable', 'is_featured', 'allow_discount', 'allow_negative_stock')
        }),
        ('Manufacturer & Warranty', {
            'fields': ('manufacturer', 'warranty_period', 'warranty_description'),
            'classes': ('collapse',)
        }),
        ('ERP Integration', {
            'fields': ('erp_code', 'erp_id', 'sync_with_erp'),
            'classes': ('collapse',)
        }),
        ('Additional', {
            'fields': ('tags', 'attributes_data', 'notes', 'specifications'),
            'classes': ('collapse',)
        }),
    )
    list_display = ('id', 'code', 'name', 'item_type', 'product_type', 'category', 'brand', 'selling_price', 'is_active', 'created_on')
    list_filter = ['is_active', 'item_type', 'product_type', 'category', 'brand', 'is_saleable', 'is_purchasable', 'created_on']
    search_fields = ['code', 'name', 'barcode', 'sku', 'hsn_code', 'manufacturer']
    ordering = ('-created_on',)
    list_per_page = 25
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ItemUOMConversion)
class ItemUOMConversionAdmin(admin.ModelAdmin):
    fields = ["item", "alternate_uom", "conversion_factor", "is_default_purchase", "is_default_sales", "barcode"]
    list_display = ("id", "item", "alternate_uom", "conversion_factor", "is_default_purchase", "is_default_sales", "created_on")
    list_filter = ["is_default_purchase", "is_default_sales", "created_on"]
    search_fields = ["item__name", "item__code", "alternate_uom__name", "barcode"]
    ordering = ("item__name", "alternate_uom__name")
    list_per_page = 25
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ItemFieldConfiguration)
class ItemFieldConfigurationAdmin(admin.ModelAdmin):
    fields = ['field_name', 'display_label', 'is_visible', 'is_required', 'is_readonly', 'display_order', 'section']
    list_display = ('id', 'field_name', 'display_label', 'is_visible', 'is_required', 'is_readonly', 'display_order', 'section')
    list_filter = ['is_visible', 'is_required', 'is_readonly', 'section']
    search_fields = ['field_name', 'display_label']
    ordering = ('section', 'display_order')
    list_per_page = 50


# ==================== Channel Partner Admin ====================

@admin.register(Superstockist)
class SuperstockistAdmin(ImportExportMixin, admin.ModelAdmin):
    fields = ['code', 'name', 'state', 'address', 'pincode', 'gstin', 'pan', 
              'credit_limit', 'credit_days', 'is_active', 'effective_from', 'effective_to',
              'erp_code', 'company']
    list_display = ('id', 'code', 'name', 'state', 'gstin', 'is_active', 'created_on')
    list_filter = ['is_active', 'state', 'created_on']
    search_fields = ['code', 'name', 'gstin']
    ordering = ('name',)
    list_per_page = 25
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SuperstockistLocation)
class SuperstockistLocationAdmin(admin.ModelAdmin):
    fields = ['superstockist', 'state', 'city', 'area']
    list_display = ('id', 'superstockist', 'state', 'city', 'area')
    list_filter = ['state', 'city']
    search_fields = ['superstockist__name', 'superstockist__code', 'state__name', 'city__name']
    ordering = ('superstockist', 'state')
    list_per_page = 25


@admin.register(Distributor)
class DistributorAdmin(ImportExportMixin, admin.ModelAdmin):
    fields = ['code', 'name', 'superstockist', 'state', 'address', 'pincode', 'gstin', 'pan',
              'credit_limit', 'credit_days', 'is_active', 'effective_from', 'effective_to',
              'erp_code', 'company']
    list_display = ('id', 'code', 'name', 'superstockist', 'state', 'gstin', 'is_active', 'created_on')
    list_filter = ['is_active', 'state', 'superstockist', 'created_on']
    search_fields = ['code', 'name', 'gstin']
    ordering = ('name',)
    list_per_page = 25
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DistributorLocation)
class DistributorLocationAdmin(admin.ModelAdmin):
    fields = ['distributor', 'state', 'city', 'area']
    list_display = ('id', 'distributor', 'state', 'city', 'area')
    list_filter = ['state', 'city']
    search_fields = ['distributor__name', 'distributor__code', 'state__name', 'city__name']
    ordering = ('distributor', 'state')
    list_per_page = 25


@admin.register(Retailer)
class RetailerAdmin(ImportExportMixin, admin.ModelAdmin):
    fields = ['code', 'name', 'distributor', 'state', 'address', 'pincode', 'outlet_type', 'outlet_size',
              'gstin', 'pan', 'credit_limit', 'credit_days', 
              'is_active', 'effective_from', 'effective_to',
              'erp_code', 'company']
    list_display = ('id', 'code', 'name', 'distributor', 'outlet_type', 'state', 'is_active', 'created_on')
    list_filter = ['is_active', 'outlet_type', 'outlet_size', 'state', 'distributor', 'created_on']
    search_fields = ['code', 'name', 'gstin', 'outlet_type']
    ordering = ('name',)
    list_per_page = 25
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RetailerLocation)
class RetailerLocationAdmin(admin.ModelAdmin):
    fields = ['retailer', 'state', 'city', 'area']
    list_display = ('id', 'retailer', 'state', 'city', 'area')
    list_filter = ['state', 'city']
    search_fields = ['retailer__name', 'retailer__code', 'state__name', 'city__name']
    ordering = ('retailer', 'state')
    list_per_page = 25


@admin.register(PriceBook)
class PriceBookAdmin(ImportExportMixin, admin.ModelAdmin):
    resource_class = PriceBookResource
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'company', 'item', 'price_type')
        }),
        ('Geographic Scope', {
            'fields': ('state', 'city', 'area'),
            'classes': ('collapse',),
        }),
        ('Channel Partner Scope', {
            'fields': ('superstockist', 'distributor', 'retailer'),
            'classes': ('collapse',),
        }),
        ('Pricing Details', {
            'fields': ('base_price', 'selling_price', 'mrp', 'discount_percentage')
        }),
        ('Validity', {
            'fields': ('effective_from', 'effective_to', 'is_active')
        }),
        ('Additional Info', {
            'fields': ('remarks', 'erp_code', 'erp_id'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_on', 'modified_on'),
            'classes': ('collapse',)
        }),
    )
    list_display = ('code', 'item', 'price_type', 'get_scope_display', 'selling_price', 
                    'mrp', 'effective_from', 'effective_to', 'is_active', 'created_on')
    list_filter = ['price_type', 'is_active', 'effective_from', 'state', 'city']
    search_fields = ['code', 'item__name', 'item__code']
    ordering = ('-created_on',)
    list_per_page = 25
    readonly_fields = ('created_on', 'modified_on')
    autocomplete_fields = ['item', 'superstockist', 'distributor', 'retailer']
    
    def has_delete_permission(self, request, obj=None):
        return False


class PriceBookHistoryInline(admin.TabularInline):
    model = PriceBookHistory
    extra = 0
    can_delete = False
    readonly_fields = ('action', 'base_price', 'selling_price', 'mrp', 'discount_percentage',
                      'effective_from', 'effective_to', 'is_active', 'created_on', 
                      'created_by_type', 'created_by_identifier', 'get_change_summary')
    fields = ('action', 'selling_price', 'mrp', 'created_on', 'created_by_identifier', 'get_change_summary')
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(PriceBookHistory)
class PriceBookHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'price_book', 'action', 'selling_price', 'mrp', 'created_on', 'created_by_identifier')
    list_filter = ['action', 'created_on', 'is_active']
    search_fields = ['price_book__code', 'price_book__item__name', 'created_by_identifier']
    ordering = ('-created_on',)
    list_per_page = 50
    readonly_fields = ('price_book', 'action', 'changes', 'base_price', 'selling_price', 'mrp',
                      'discount_percentage', 'effective_from', 'effective_to', 'is_active',
                      'remarks', 'created_on', 'created_by_type', 'created_by_identifier', 'get_change_summary')
    
    fieldsets = (
        ('Price Book', {
            'fields': ('price_book', 'action')
        }),
        ('Price Snapshot', {
            'fields': ('base_price', 'selling_price', 'mrp', 'discount_percentage')
        }),
        ('Validity', {
            'fields': ('effective_from', 'effective_to', 'is_active')
        }),
        ('Changes', {
            'fields': ('changes', 'get_change_summary', 'remarks')
        }),
        ('Audit', {
            'fields': ('created_on', 'created_by_type', 'created_by_identifier')
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

# ============================================================================
# SCHEME ADMIN CLASSES
# ============================================================================

class SchemeConditionInline(admin.TabularInline):
    """Inline admin for scheme conditions"""
    model = SchemeCondition
    extra = 1
    fields = ('condition_type', 'logical_operator', 'item', 'value_from', 'value_to', 'remarks')
    can_delete = True


class SchemeBenefitInline(admin.TabularInline):
    """Inline admin for scheme benefits"""
    model = SchemeBenefit
    extra = 1
    fields = ('benefit_type', 'value', 'apply_to_all', 'apply_to_item', 'apply_to_category', 'free_item', 'free_quantity', 'remarks')
    can_delete = True


class SchemeApplicabilityInline(admin.TabularInline):
    """Inline admin for scheme applicability"""
    model = SchemeApplicability
    extra = 1
    fields = ('channel_type', 'state', 'city', 'area', 'superstockist', 'distributor', 'retailer')
    can_delete = True


class SchemeItemInline(admin.TabularInline):
    """Inline admin for items included in scheme"""
    model = SchemeItem
    extra = 1
    fields = ('item', 'category', 'remarks')
    can_delete = True


@admin.register(Scheme)
class SchemeAdmin(admin.ModelAdmin):
    """Admin interface for managing schemes"""
    list_display = ('code', 'name', 'scheme_type', 'status', 'company', 'priority', 'effective_from', 'effective_to', 'is_stackable', 'created_on')
    list_filter = ('status', 'scheme_type', 'is_stackable', 'is_deleted', 'company', 'effective_from', 'effective_to')
    search_fields = ('code', 'name', 'description')
    readonly_fields = ('created_on', 'modified_on', 'code', 'created_by_type', 'created_by_identifier')
    
    fieldsets = (
        ('Scheme Identification', {
            'fields': ('code', 'name', 'description', 'company')
        }),
        ('Scheme Configuration', {
            'fields': ('scheme_type', 'status', 'priority', 'is_stackable')
        }),
        ('Validity Period', {
            'fields': ('effective_from', 'effective_to')
        }),
        ('Additional Info', {
            'fields': ('remarks',)
        }),
        ('Audit Trail', {
            'fields': ('created_on', 'modified_on', 'created_by_type', 'created_by_identifier'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [SchemeConditionInline, SchemeBenefitInline, SchemeApplicabilityInline, SchemeItemInline]
    actions = ['make_active', 'make_inactive', 'make_draft']
    
    def make_active(self, request, queryset):
        """Mark schemes as active"""
        updated = queryset.update(status='ACTIVE')
        self.message_user(request, f'{updated} scheme(s) marked as active')
    make_active.short_description = 'Mark selected schemes as ACTIVE'
    
    def make_inactive(self, request, queryset):
        """Mark schemes as inactive"""
        updated = queryset.update(status='INACTIVE')
        self.message_user(request, f'{updated} scheme(s) marked as inactive')
    make_inactive.short_description = 'Mark selected schemes as INACTIVE'
    
    def make_draft(self, request, queryset):
        """Mark schemes as draft"""
        updated = queryset.update(status='DRAFT')
        self.message_user(request, f'{updated} scheme(s) marked as DRAFT')
    make_draft.short_description = 'Mark selected schemes as DRAFT'


@admin.register(SchemeCondition)
class SchemeConditionAdmin(admin.ModelAdmin):
    """Admin interface for scheme conditions"""
    list_display = ('scheme', 'condition_type', 'logical_operator', 'value_from', 'value_to')
    list_filter = ('condition_type', 'logical_operator', 'scheme__company')
    search_fields = ('scheme__code', 'scheme__name')
    
    fieldsets = (
        ('Condition Details', {
            'fields': ('scheme', 'condition_type', 'logical_operator')
        }),
        ('Condition Values', {
            'fields': ('item', 'category', 'value_from', 'value_to')
        }),
    )


@admin.register(SchemeBenefit)
class SchemeBenefitAdmin(admin.ModelAdmin):
    """Admin interface for scheme benefits"""
    list_display = ('scheme', 'benefit_type', 'apply_to_all', 'apply_to_item', 'apply_to_category')
    list_filter = ('benefit_type', 'apply_to_all', 'scheme__company')
    search_fields = ('scheme__code', 'scheme__name')
    
    fieldsets = (
        ('Benefit Details', {
            'fields': ('scheme', 'benefit_type', 'discount_value', 'max_discount_amount')
        }),
        ('Apply To', {
            'fields': ('apply_to_all', 'apply_to_item', 'apply_to_category')
        }),
        ('Free Items/Quantity', {
            'fields': ('free_item', 'free_quantity')
        }),
    )


@admin.register(SchemeApplicability)
class SchemeApplicabilityAdmin(admin.ModelAdmin):
    """Admin interface for scheme applicability/targeting"""
    list_display = ('scheme', 'customer_type', 'state', 'city', 'area', 'get_customer_display')
    list_filter = ('customer_type', 'scheme__company', 'state', 'city', 'area')
    search_fields = ('scheme__code', 'scheme__name')
    readonly_fields = ()
    
    fieldsets = (
        ('Scheme & Channel', {
            'fields': ('scheme', 'customer_type')
        }),
        ('Geographic', {
            'fields': ('state', 'city', 'area')
        }),
        ('Channel Partners', {
            'fields': ('superstockist', 'distributor', 'retailer')
        }),
    )
    
    def get_customer_display(self, obj):
        """Get customer name based on channel type"""
        if obj.superstockist:
            return f"SST: {obj.superstockist.name}"
        elif obj.distributor:
            return f"Dist: {obj.distributor.name}"
        elif obj.retailer:
            return f"Ret: {obj.retailer.name}"
        return "All"
    get_customer_display.short_description = 'Customer'
    
    fieldsets = (
        ('Scheme & Channel', {
            'fields': ('scheme', 'channel_type')
        }),
        ('Geographic', {
            'fields': ('state', 'city', 'area')
        }),
        ('Channel Partners', {
            'fields': ('superstockist', 'distributor', 'retailer')
        }),
        ('Timestamps', {
            'fields': ('created_on', 'modified_on'),
            'classes': ('collapse',)
        }),
    )
    
    def get_customer_display(self, obj):
        """Get customer name based on channel type"""
        if obj.superstockist:
            return f"SST: {obj.superstockist.name}"
        elif obj.distributor:
            return f"Dist: {obj.distributor.name}"
        elif obj.retailer:
            return f"Ret: {obj.retailer.name}"
        return "All"
    get_customer_display.short_description = 'Customer'


@admin.register(SchemeItem)
class SchemeItemAdmin(admin.ModelAdmin):
    """Admin interface for items in scheme"""
    list_display = ('scheme', 'item', 'category', 'include_all_items')
    list_filter = ('scheme__company', 'category', 'include_all_items')
    search_fields = ('scheme__code', 'scheme__name', 'item__code', 'item__name')
    
    fieldsets = (
        ('Scheme & Item', {
            'fields': ('scheme', 'item', 'category', 'include_all_items')
        }),
    )


@admin.register(SchemeHistory)
class SchemeHistoryAdmin(admin.ModelAdmin):
    """Admin interface for scheme change history"""
    list_display = ('scheme', 'action', 'changed_by_type', 'changed_by_identifier', 'changed_at')
    list_filter = ('action', 'scheme__company', 'changed_at')
    search_fields = ('scheme__code', 'scheme__name', 'changes')
    readonly_fields = ('scheme', 'action', 'changes', 'changed_by_type', 'changed_by_identifier', 'changed_at', 'get_change_summary')
    
    fieldsets = (
        ('History Details', {
            'fields': ('scheme', 'action', 'changed_at')
        }),
        ('Changed By', {
            'fields': ('changed_by_type', 'changed_by_identifier')
        }),
        ('Changes', {
            'fields': ('changes', 'get_change_summary')
        }),
    )
    
    def has_add_permission(self, request):
        """History is auto-created, read-only in admin"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """History cannot be deleted"""
        return False

# ==================== Project Master Admin ====================

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'developer_name', 'project_type',
                    'approval_type', 'status', 'location', 'is_active', 'is_deleted',
                    'created_on')
    list_filter = ('status', 'project_type', 'approval_type', 'is_active', 'is_deleted')
    search_fields = ('code', 'name', 'developer_name', 'rera_number')
    ordering = ('name',)
    list_per_page = 25
    raw_id_fields = ('location',)
    readonly_fields = ('code', 'created_on', 'modified_on',
                      'created_by_identifier', 'modified_by_identifier')

    fieldsets = (
        ('Identification', {
            'fields': ('code', 'name', 'developer_name')
        }),
        ('Classification', {
            'fields': ('project_type', 'approval_type', 'status', 'is_active')
        }),
        ('Location', {
            'fields': ('location', 'address')
        }),
        ('Compliance', {
            'fields': ('rera_number', 'launch_date', 'possession_date')
        }),
        ('Size & Description', {
            'fields': ('total_area', 'description')
        }),
        ('Marketing Assets', {
            'fields': ('image_url', 'brochure_url', 'layout_plan_url', 'floor_plan_url'),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('is_deleted', 'created_by_identifier', 'created_on',
                       'modified_by_identifier', 'modified_on'),
            'classes': ('collapse',)
        }),
    )

    def has_delete_permission(self, request, obj=None):
        # Force users through the soft-delete path; hard delete via shell only
        return False


@admin.register(ProjectStatusHistory)
class ProjectStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('project', 'from_status', 'to_status', 'changed_by_identifier', 'created_on')
    list_filter = ('to_status',)
    search_fields = ('project__code', 'project__name', 'changed_by_identifier')
    readonly_fields = ('project', 'from_status', 'to_status', 'changed_by_identifier', 'remarks', 'created_on')
    ordering = ('-created_on',)
    list_per_page = 25

    def has_add_permission(self, request):
        return False  # History rows are auto-created

    def has_delete_permission(self, request, obj=None):
        return False
