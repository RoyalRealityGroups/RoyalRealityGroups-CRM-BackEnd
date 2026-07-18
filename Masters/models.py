from django.utils import timezone

from django.db import models
import uuid


from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError

from Core.Users.models import CodeModel, CoreModel, BaseModel, ChannelPartnerManager, DEVICE_ACCESS_CHOICES
from .validators import (
    validate_gst_number,
    DuplicateValidationMixin
)

User = get_user_model()


class ChannelPartnerConfiguration(BaseModel):
    """
    Organization-level configuration for channel partner features.
    This should be a singleton table with only one active record.
    """
    name = models.CharField(max_length=100, default='Default Configuration', help_text='Configuration name')
    enable_superstockist = models.BooleanField(default=False, help_text='Enable Superstockist Master')
    enable_distributor = models.BooleanField(default=False, help_text='Enable Distributor Master')
    enable_retailer = models.BooleanField(default=False, help_text='Enable Retailer Master')
    enforce_channel_hierarchy = models.BooleanField(
        default=False,
        help_text='Enforce Superstockist -> Distributor -> Retailer hierarchy'
    )
    is_active = models.BooleanField(default=True, help_text='Active configuration')

    class Meta:
        verbose_name = 'Channel Partner Configuration'
        verbose_name_plural = 'Channel Partner Configuration'
        ordering = ['-created_on']

    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"

    def save(self, *args, **kwargs):
        # Ensure only one active configuration exists
        if self.is_active:
            # Exclude current instance from the update to avoid issues
            ChannelPartnerConfiguration.objects.filter(
                is_active=True
            ).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class Country(DuplicateValidationMixin, CodeModel):
    name = models.CharField(max_length=100)
    CODE_PREFIX = 'CTRY'

    class Meta:
        ordering = ['name']
        verbose_name = 'Country'
        verbose_name_plural = 'Countries'

    def __str__(self): return str(self.name)


class State(DuplicateValidationMixin, CodeModel):
    name = models.CharField(max_length=100)
    gst_code = models.CharField(max_length=2, blank=True, null=True, help_text='GST State Code (e.g., 01, 02, 33)')
    country = models.ForeignKey(Country, related_name='states', on_delete=models.RESTRICT)
    CODE_PREFIX = 'STAT'

    class Meta:
        ordering = ['name']
        verbose_name = 'State'
        verbose_name_plural = 'States'

    def __str__(self): return str(self.name)


class District(DuplicateValidationMixin, CodeModel):
    CODE_PREFIX = 'DIST'
    name = models.CharField(max_length=100)
    state = models.ForeignKey(State, related_name='districts', on_delete=models.RESTRICT)

    class Meta:
        ordering = ['name']
        verbose_name = 'District'
        verbose_name_plural = 'Districts'
        unique_together = ('name', 'state')

    def __str__(self): return f"{self.name} ({self.state.name})"


class Mandal(DuplicateValidationMixin, CodeModel):
    CODE_PREFIX = 'MNDL'
    name = models.CharField(max_length=100)
    district = models.ForeignKey(District, related_name='mandals', on_delete=models.RESTRICT)
    state = models.ForeignKey(State, related_name='mandals', on_delete=models.RESTRICT)

    class Meta:
        ordering = ['name']
        verbose_name = 'Mandal'
        verbose_name_plural = 'Mandals'
        unique_together = ('name', 'district')

    def clean(self):
        super().clean()
        if self.district_id and self.state_id and self.district.state_id != self.state_id:
            raise ValidationError({'state': f'District "{self.district.name}" does not belong to state "{self.state.name}".'})

    def save(self, *args, **kwargs):
        if not self.state_id and self.district_id:
            self.state = self.district.state
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self): return f"{self.name} ({self.district.name})"


class City(DuplicateValidationMixin, CodeModel):
    CODE_PREFIX = 'CITY'
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, related_name='cities', on_delete=models.RESTRICT, null=True, blank=True)
    district = models.ForeignKey(District, related_name='cities', on_delete=models.RESTRICT, null=True, blank=True)
    mandal = models.ForeignKey(Mandal, related_name='cities', on_delete=models.RESTRICT, null=True, blank=True)
    state = models.ForeignKey(State, related_name='cities', on_delete=models.RESTRICT)
    pincode = models.CharField(max_length=10, blank=True, null=True, help_text='PIN Code')

    class Meta:
        ordering = ['name']
        verbose_name = 'City'
        verbose_name_plural = 'Cities'
        unique_together = ('name', 'state')

    def clean(self):
        super().clean()
        if self.district_id and self.state_id and self.district.state_id != self.state_id:
            raise ValidationError({'state': f'District "{self.district.name}" does not belong to state "{self.state.name}".'})
        if self.mandal_id and self.district_id and self.mandal.district_id != self.district_id:
            raise ValidationError({'mandal': f'Mandal "{self.mandal.name}" does not belong to district "{self.district.name}".'})

    def save(self, *args, **kwargs):
        # Auto-populate country and state from relationships
        if not self.country_id:
            if self.state_id:
                self.country = self.state.country
            elif self.mandal_id:
                self.country = self.mandal.state.country
            elif self.district_id:
                self.country = self.district.state.country
        
        if not self.state_id:
            if self.mandal_id:
                self.state = self.mandal.state
            elif self.district_id:
                self.state = self.district.state
        
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self): return str(self.name)


class Area(DuplicateValidationMixin, CodeModel):
    CODE_PREFIX = 'VT'
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, related_name='areas', on_delete=models.RESTRICT, null=True, blank=True)
    state = models.ForeignKey(State, related_name='areas', on_delete=models.RESTRICT)
    district = models.ForeignKey(District, related_name='areas', on_delete=models.RESTRICT, null=True, blank=True)
    mandal = models.ForeignKey(Mandal, related_name='areas', on_delete=models.RESTRICT, null=True, blank=True)
    city = models.ForeignKey(City, related_name='areas', on_delete=models.RESTRICT)
    pincode = models.CharField(max_length=10, blank=True, null=True, help_text='PIN Code')

    class Meta:
        unique_together = ('name', 'city')
        ordering = ['name']
        verbose_name = 'Village/Town'
        verbose_name_plural = 'Villages/Towns'

    def clean(self):
        super().clean()
        # Validate hierarchy consistency
        if self.country_id and self.state_id and self.state.country_id != self.country_id:
            raise ValidationError({'state': f'State "{self.state.name}" does not belong to country "{self.country.name}".'})
        if self.state_id and self.district_id and self.district.state_id != self.state_id:
            raise ValidationError({'district': f'District "{self.district.name}" does not belong to state "{self.state.name}".'})
        if self.district_id and self.mandal_id and self.mandal.district_id != self.district_id:
            raise ValidationError({'mandal': f'Mandal "{self.mandal.name}" does not belong to district "{self.district.name}".'})
        if self.mandal_id and self.city_id and self.city.mandal_id and self.mandal_id != self.city.mandal_id:
            raise ValidationError({'city': f'City "{self.city.name}" does not belong to mandal "{self.mandal.name}".'})

    def save(self, *args, **kwargs):
        # Auto-populate hierarchy from city if not provided
        if self.city_id:
            if not self.country_id and self.city.country_id:
                self.country = self.city.country
            if not self.state_id:
                self.state = self.city.state
            if not self.district_id and self.city.district_id:
                self.district = self.city.district
            if not self.mandal_id and self.city.mandal_id:
                self.mandal = self.city.mandal
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self): return str(self.name)





class Route(DuplicateValidationMixin, CodeModel):
    CODE_PREFIX = 'RTE'
    name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Route'
        verbose_name_plural = 'Routes'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return str(self.name)


class RouteCoverage(models.Model):
    route = models.ForeignKey(Route, related_name='coverages', on_delete=models.CASCADE)
    state = models.ForeignKey(State, related_name='route_coverages', on_delete=models.RESTRICT)
    city = models.ForeignKey(City, related_name='route_coverages', on_delete=models.RESTRICT)
    area = models.ForeignKey(Area, related_name='route_coverages', on_delete=models.RESTRICT)

    class Meta:
        db_table = 'route_coverages'
        unique_together = ('route', 'state', 'city', 'area')
        indexes = [
            models.Index(fields=['route', 'state', 'city']),
            models.Index(fields=['state', 'city', 'area']),
        ]

    def clean(self):
        super().clean()

        # During import dry-run, related objects can be attached later in the row lifecycle.
        # Skip cross-field checks until all required relations are present.
        if not self.route_id or not self.state_id or not self.city_id or not self.area_id:
            return

        if self.city and self.city.state_id != self.state_id:
            raise ValidationError({'city': 'Selected city does not belong to selected state.'})

        if self.area:
            if self.area.city_id != self.city_id:
                raise ValidationError({'area': 'Selected area does not belong to selected city.'})
            if self.area.state_id != self.state_id:
                raise ValidationError({'area': 'Selected area does not belong to selected state.'})

        conflict_qs = RouteCoverage.objects.filter(
            route__name__iexact=self.route.name,
            state_id=self.state_id,
            city_id=self.city_id,
            route__is_deleted=False,
        ).exclude(route_id=self.route_id)

        if conflict_qs.exists():
            raise ValidationError({
                'route': (
                    f'Route name "{self.route.name}" already exists for '
                    f'{self.state.name} - {self.city.name}.'
                )
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.route.name}: {self.state.name} - {self.city.name} - {self.area.name}'


class Company(DuplicateValidationMixin, CodeModel):
    CODE_PREFIX = 'COMP'
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    city = models.ForeignKey(City, related_name='companies', on_delete=models.RESTRICT, null=True, blank=True)
    state = models.ForeignKey(State, related_name='companies', on_delete=models.RESTRICT, null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    logo = models.FileField(upload_to='company_logos', blank=True, null=True)
    pan_number = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        unique=True,
        help_text='Company PAN Number (10 characters)'
    )
    gst_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        unique=True,
        validators=[validate_gst_number],
        help_text='Company GST Number (15 characters)'
    )

    def clean(self):
        """Validate PAN and GST"""
        super().clean()

        # Validate PAN format
        if self.pan_number:
            import re
            pan_pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]$'
            if not re.match(pan_pattern, self.pan_number):
                raise ValidationError({
                    'pan_number': 'Invalid PAN format. Must be 5 letters, 4 digits, 1 letter (e.g., ABCDE1234F)'
                })

        # Validate GST state matches selected state
        # if self.gst_number and self.state:
        #     gst_state_code = self.gst_number[:2]
        #     if gst_state_code != self.state.gst_code:
        #         raise ValidationError({
        #             'gst_number': (
        #                 f"GST state code ({gst_state_code}) does not match selected state "
        #                 f"({self.state.gst_code} - {self.state.name})"
        #             )
        #         })

    def save(self, *args, **kwargs):
        if self.pan_number:
            self.pan_number = self.pan_number.upper().strip()
        if self.gst_number:
            self.gst_number = self.gst_number.upper().strip()
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self): return str(self.name)


class Location(DuplicateValidationMixin, CodeModel):
    CODE_PREFIX = 'LOC'
    name = models.CharField(max_length=100)
    companies = models.ManyToManyField(Company, related_name='locations', blank=True)
    city = models.ForeignKey(City, related_name='locations', on_delete=models.RESTRICT)
    state = models.ForeignKey(State, related_name='locations', on_delete=models.RESTRICT)
    country = models.ForeignKey(Country, related_name='locations', on_delete=models.RESTRICT)
    address = models.TextField(blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    erp_code = models.CharField(max_length=50, blank=True, null=True)
    erp_id = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Location'
        verbose_name_plural = 'Locations'

    @property
    def company(self):
        """
        Backward-compatible accessor for legacy code paths that still expect
        a single company on Location.
        """
        return self.companies.first()

    def __str__(self): return str(self.name)


class LocationContact(BaseModel):
    location = models.ForeignKey(Location, related_name='contacts', on_delete=models.CASCADE)
    contact_person = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        db_table = 'location_contacts'
        ordering = ['-is_primary', 'contact_person']
        verbose_name = 'Location Contact'
        verbose_name_plural = 'Location Contacts'

    def __str__(self):
        return f"{self.location.name} - {self.contact_person}"


class WareHouse(DuplicateValidationMixin, CodeModel):
    CODE_PREFIX = 'WH'
    name = models.CharField(max_length=100)
    location = models.ForeignKey(Location, related_name='warehouses', on_delete=models.RESTRICT)
    erp_code = models.CharField(max_length=50, blank=True, null=True)
    erp_id = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Warehouse'
        verbose_name_plural = 'Warehouses'

    def __str__(self): return str(self.name)


class UOM(DuplicateValidationMixin, CodeModel):
    CODE_PREFIX = 'UOM'
    name = models.CharField(max_length=180, unique=True)
    remarks = models.TextField(default='', blank=True, null=True)
    erp_code = models.CharField(max_length=50, blank=True, null=True)
    erp_id = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self): return str(self.name)


class Category(DuplicateValidationMixin, CodeModel):
    CODE_PREFIX = 'CAT'
    name = models.CharField(max_length=180, unique=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subcategories')
    description = models.TextField(default='', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    erp_code = models.CharField(max_length=50, blank=True, null=True)
    erp_id = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self): return str(self.name)


class Brand(DuplicateValidationMixin, CodeModel):
    CODE_PREFIX = 'BRD'
    name = models.CharField(max_length=180, unique=True)
    description = models.TextField(default='', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    erp_code = models.CharField(max_length=50, blank=True, null=True)
    erp_id = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        ordering = ['name']

    def __str__(self): return str(self.name)


class Tax(DuplicateValidationMixin, CodeModel):
    """Tax Master - GST and CESS types"""
    CODE_PREFIX = 'TAX'

    TAX_TYPE_CHOICES = [
        ('GST', 'GST'),
        ('CESS', 'CESS'),
        ('COMPENSATION_CESS', 'Compensation CESS'),
    ]

    name = models.CharField(max_length=180, unique=True)
    tax_type = models.CharField(
        max_length=50,
        choices=TAX_TYPE_CHOICES,
        default='GST',
        help_text='GST will be split into CGST/SGST/IGST at transaction time'
    )
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text='Tax percentage')
    is_cess = models.BooleanField(default=False, editable=False, help_text='Auto-calculated based on tax_type')
    description = models.TextField(default='', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Taxes"
        ordering = ['tax_type', 'tax_rate', 'name']

    def save(self, *args, **kwargs):
        # Auto-set is_cess based on tax_type
        self.is_cess = 'CESS' in self.tax_type
        super().save(*args, **kwargs)

    def __str__(self): return f"{self.name} ({self.tax_rate}%)"


class Item(DuplicateValidationMixin, CodeModel):
    """Item/Product Master"""
    CODE_PREFIX = 'ITM'

    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    short_name = models.CharField(max_length=100, blank=True, null=True)
    barcode = models.CharField(max_length=50, blank=True, null=True, unique=True)
    sku = models.CharField(max_length=50, blank=True, null=True)
    company = models.ForeignKey(Company, related_name='items', on_delete=models.RESTRICT, null=True, blank=True)

    # Classification
    ITEM_TYPE_CHOICES = (
        (1, 'Material'),
        (2, 'Service'),
    )
    PRODUCT_TYPE_CHOICES = (
        (1, 'Group'),
        (2, 'Product'),
    )
    item_type = models.SmallIntegerField(choices=ITEM_TYPE_CHOICES, default=1)
    product_type = models.SmallIntegerField(choices=PRODUCT_TYPE_CHOICES, default=2)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    category = models.ForeignKey(Category, related_name='items', on_delete=models.RESTRICT, null=True, blank=True)
    brand = models.ForeignKey(Brand, related_name='items', on_delete=models.RESTRICT, null=True, blank=True)

    # Unit of Measurement
    base_uom = models.ForeignKey(UOM, related_name='items_base', on_delete=models.RESTRICT)
    bag_weight = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        help_text='Bag weight (in base UOM)')

    # Tax & Legal
    hsn_code = models.CharField(max_length=20, blank=True, null=True, help_text='HSN/SAC Code')
    sac_code = models.CharField(max_length=20, blank=True, null=True, help_text='Service Accounting Code')
    TAX_CATEGORY_CHOICES = (
        (1, 'Taxable'),
        (2, 'Exempt'),
        (3, 'Zero-rated'),
    )
    tax_category = models.SmallIntegerField(choices=TAX_CATEGORY_CHOICES, default=1)
    cess_applicable = models.BooleanField(default=False)
    cess_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Pricing
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    mrp = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text='Maximum Retail Price')
    min_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    price_includes_tax = models.BooleanField(default=False)

    # Inventory & Stock
    is_stockable = models.BooleanField(default=True)
    track_inventory = models.BooleanField(default=True)
    min_stock_level = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    max_stock_level = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    reorder_level = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    reorder_quantity = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)

    # Product Specifications
    weight = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    weight_unit = models.CharField(max_length=10, blank=True, null=True, help_text='KG, GM, LB, etc.')
    length = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Length in CM')
    width = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Width in CM')
    height = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Height in CM')

    # Images & Media
    image = models.FileField(upload_to='items/images/', blank=True, null=True)
    additional_images = models.JSONField(default=list, blank=True, help_text='Array of additional image URLs')

    # Business Flags
    is_active = models.BooleanField(default=True)
    is_saleable = models.BooleanField(default=True)
    is_purchasable = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    allow_discount = models.BooleanField(default=True)
    allow_negative_stock = models.BooleanField(default=False)

    # Supplier & Manufacturer
    manufacturer = models.CharField(max_length=255, blank=True, null=True)
    warranty_period = models.IntegerField(null=True, blank=True, help_text='Warranty in months')
    warranty_description = models.TextField(blank=True, null=True)

    # ERP Integration
    erp_code = models.CharField(max_length=50, blank=True, null=True)
    erp_id = models.CharField(max_length=50, blank=True, null=True)
    sync_with_erp = models.BooleanField(default=False)

    # Additional Information
    tags = models.JSONField(default=list, blank=True, help_text='Array of tags for search/filter')
    notes = models.TextField(blank=True, null=True, help_text='Internal notes')
    specifications = models.TextField(blank=True, null=True, help_text='Technical specifications')

    class Meta:
        ordering = ['-created_on']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['barcode']),
            models.Index(fields=['item_type', 'product_type']),
            models.Index(fields=['category', 'brand']),
        ]
        permissions = [
            ('import_item', 'Can import item'),
        ]

    @property
    def current_tax(self):
        """Get applicable tax for today (backward compatibility)"""
        from django.utils import timezone
        today = timezone.now().date()

        composition = self.tax_compositions.filter(
            effective_from__lte=today,
            composition_type='PRIMARY',
            is_deleted=False
        ).filter(
            models.Q(effective_to__isnull=True) | models.Q(effective_to__gte=today)
        ).first()

        return composition.tax if composition else None

    @property
    def current_tax_composition(self):
        """Returns all active tax compositions (GST + CESS) for current date"""
        from django.utils import timezone
        today = timezone.now().date()

        return self.tax_compositions.filter(
            effective_from__lte=today,
            is_deleted=False
        ).filter(
            models.Q(effective_to__isnull=True) | models.Q(effective_to__gte=today)
        ).select_related('tax').order_by('composition_type', 'tax__tax_type')

    @property
    def primary_tax_composition(self):
        """Returns the primary GST tax composition"""
        return self.current_tax_composition.filter(composition_type='PRIMARY').first()

    @property
    def cess_compositions(self):
        """Returns all CESS tax compositions"""
        return self.current_tax_composition.filter(composition_type='CESS')

    @property
    def total_tax_percentage(self):
        """Sum of all applicable taxes (GST + CESS)"""
        from decimal import Decimal
        return sum(
            comp.tax.tax_rate for comp in self.current_tax_composition
        ) or Decimal('0')

    @property
    def tax_breakdown(self):
        """Returns detailed tax breakdown for display"""
        breakdown = {
            'primary': None,
            'cess': [],
            'total_percentage': 0,
        }

        for comp in self.current_tax_composition:
            tax_info = {
                'name': comp.tax.name,
                'type': comp.tax.tax_type,
                'percentage': float(comp.tax.tax_rate),
            }

            if comp.composition_type == 'PRIMARY':
                breakdown['primary'] = tax_info
            elif comp.composition_type == 'CESS':
                breakdown['cess'].append(tax_info)

            breakdown['total_percentage'] += float(comp.tax.tax_rate)

        return breakdown

    def get_tax_on_date(self, date):
        """Get applicable tax for a specific date (for historical invoices)"""
        composition = self.tax_compositions.filter(
            effective_from__lte=date,
            composition_type='PRIMARY',
            is_deleted=False
        ).filter(
            models.Q(effective_to__isnull=True) | models.Q(effective_to__gte=date)
        ).first()

        return composition.tax if composition else None

    def save(self, *args, **kwargs):
        # Optimize image before saving
        if self.image and hasattr(self.image, 'file'):
            try:
                from Core.Core.utils.image_optimizer import optimize_image
                self.image = optimize_image(self.image)
            except Exception:
                pass  # Keep original if optimization fails

        # Convert empty barcode to None to avoid unique constraint issues
        if self.barcode == '':
            self.barcode = None
        super().save(*args, **kwargs)

    def __str__(self): return str(self.name)


class ItemTaxComposition(BaseModel):
    """
    Links items to taxes with effective date ranges.
    Supports primary GST + additional CESS taxes.
    """
    COMPOSITION_TYPE_CHOICES = [
        ('PRIMARY', 'Primary Tax (GST)'),
        ('CESS', 'CESS'),
    ]

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='tax_compositions')
    tax = models.ForeignKey(Tax, on_delete=models.PROTECT, related_name='item_compositions')
    composition_type = models.CharField(
        max_length=20,
        choices=COMPOSITION_TYPE_CHOICES,
        default='PRIMARY',
        help_text='PRIMARY for GST, CESS for additional CESS'
    )
    effective_from = models.DateField(help_text='Tax effective from this date')
    effective_to = models.DateField(null=True, blank=True, help_text='Tax effective until this date (NULL = ongoing)')

    class Meta:
        db_table = 'item_tax_composition'
        unique_together = [['item', 'tax', 'effective_from']]
        ordering = ['item', '-effective_from', 'composition_type']
        verbose_name = 'Item Tax Composition'
        verbose_name_plural = 'Item Tax Compositions'
        indexes = [
            models.Index(fields=['item', 'effective_from', 'effective_to', 'composition_type']),
            models.Index(fields=['effective_from', 'effective_to']),
        ]

    def clean(self):
        """Validate composition type matches tax type"""
        from datetime import date

        # Validate: PRIMARY must be GST type
        if self.composition_type == 'PRIMARY' and self.tax.is_cess:
            raise ValidationError({
                'composition_type': 'Primary tax must be GST type, not CESS'
            })

        # Validate: CESS must be CESS type
        if self.composition_type == 'CESS' and not self.tax.is_cess:
            raise ValidationError({
                'composition_type': 'CESS composition type must use a CESS tax'
            })

        # Validate: Only one PRIMARY tax per item per date range
        if self.composition_type == 'PRIMARY':
            overlapping = ItemTaxComposition.objects.filter(
                item=self.item,
                composition_type='PRIMARY',
                effective_from__lte=self.effective_to or date.max,
            ).filter(
                models.Q(effective_to__isnull=True) | models.Q(effective_to__gte=self.effective_from)
            ).exclude(pk=self.pk)

            if overlapping.exists():
                raise ValidationError({
                    'effective_from': 'Item already has a primary tax for this date range'
                })

    def __str__(self):
        return f"{self.item.name} - {self.tax.name} ({self.composition_type})"


class ItemUOMConversion(BaseModel):
    """Item UOM Conversion table - Stores alternate UOM conversions for items"""
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='uom_conversions')
    alternate_uom = models.ForeignKey(UOM, on_delete=models.RESTRICT, related_name='item_conversions')
    conversion_factor = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        help_text='Conversion factor: 1 Alternate UOM = X Base UOM'
    )
    is_default_purchase = models.BooleanField(default=False, help_text='Use this UOM for purchase by default')
    is_default_sales = models.BooleanField(default=False, help_text='Use this UOM for sales by default')
    barcode = models.CharField(max_length=50, blank=True, null=True, help_text='Barcode for this UOM variant')

    class Meta:
        db_table = 'item_uom_conversions'
        ordering = ['item', '-is_default_purchase', '-is_default_sales']
        unique_together = ('item', 'alternate_uom')
        indexes = [
            models.Index(fields=['item', 'alternate_uom']),
        ]

    def __str__(self):
        return f"{self.item.name} - 1 {self.alternate_uom.name} = {self.conversion_factor} {self.item.base_uom.name}"


class ItemFieldConfiguration(models.Model):
    """Configuration for Item Master fields - visibility, requirement, and read-only state"""
    field_name = models.CharField(max_length=100, unique=True, help_text='Field name from Item model')
    display_label = models.CharField(max_length=100, help_text='Display label for the field')
    is_visible = models.BooleanField(default=True, help_text='Whether field is visible in form')
    is_required = models.BooleanField(default=False, help_text='Whether field is mandatory')
    is_readonly = models.BooleanField(default=False, help_text='Whether field is read-only (not editable)')
    display_order = models.IntegerField(default=0, help_text='Order in which field appears')
    section = models.CharField(
        max_length=50,
        default='basic',
        help_text='Section: basic, classification, pricing, stock, settings')

    class Meta:
        db_table = 'item_field_configuration'
        ordering = ['section', 'display_order']
        verbose_name = 'Item Field Configuration'
        verbose_name_plural = 'Item Field Configurations'

    def __str__(self):
        return f"{self.display_label} ({self.field_name})"


# ==================== Channel Partner Models ====================

class Superstockist(DuplicateValidationMixin, CodeModel):
    """Superstockist Master - Top tier in channel partner hierarchy"""
    CODE_PREFIX = 'SST'

    name = models.CharField(max_length=200, help_text='Superstockist name')

    # Billing Address
    state = models.ForeignKey(
        State,
        related_name='superstockists',
        on_delete=models.RESTRICT,
        help_text='Billing state')
    city = models.ForeignKey(
        City,
        related_name='superstockists',
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        help_text='Billing city')
    area = models.ForeignKey(
        Area,
        related_name='superstockists',
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        help_text='Billing area')
    address = models.TextField(blank=True, null=True, help_text='Billing address')
    pincode = models.CharField(max_length=10, blank=True, null=True, help_text='Billing PIN code')

    # Shipping Address
    shipping_same_as_billing = models.BooleanField(default=True, help_text='Use billing address for shipping')
    shipping_state = models.ForeignKey(
        State,
        related_name='superstockists_shipping',
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        help_text='Shipping state')
    shipping_city = models.ForeignKey(
        City,
        related_name='superstockists_shipping',
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        help_text='Shipping city')
    shipping_area = models.ForeignKey(
        Area,
        related_name='superstockists_shipping',
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        help_text='Shipping area')
    shipping_address = models.TextField(blank=True, null=True, help_text='Shipping address')
    shipping_pincode = models.CharField(max_length=10, blank=True, null=True, help_text='Shipping PIN code')

    # Financial Information
    gstin = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        unique=True,
        validators=[validate_gst_number],
        help_text='GST Identification Number (15 characters)'
    )
    pan = models.CharField(max_length=10, blank=True, null=True, help_text='PAN Number')
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text='Credit limit amount')
    credit_days = models.IntegerField(default=0, help_text='Credit period in days')

    # Bank Details
    aadhar = models.CharField(max_length=12, blank=True, null=True, help_text='Aadhar Number (12 digits)')
    bank_account_number = models.CharField(max_length=50, blank=True, null=True, help_text='Bank account number')
    bank_name = models.CharField(max_length=200, blank=True, null=True, help_text='Bank name')
    bank_branch = models.CharField(max_length=200, blank=True, null=True, help_text='Bank branch')
    bank_ifsc = models.CharField(max_length=11, blank=True, null=True, help_text='IFSC code')
    bank_account_type = models.CharField(
        max_length=20,
        choices=[
            ('SAVINGS',
             'Savings'),
            ('CURRENT',
             'Current')],
        blank=True,
        null=True,
        help_text='Account type')
    google_location = models.TextField(blank=True, null=True, help_text='Google Maps location URL')

    # Status
    is_active = models.BooleanField(default=True, help_text='Active status')
    effective_from = models.DateField(blank=True, null=True, help_text='Effective from date')
    effective_to = models.DateField(blank=True, null=True, help_text='Effective to date')

    # ERP Integration
    erp_code = models.CharField(max_length=50, blank=True, null=True, help_text='ERP system code')

    # Organization Link
    company = models.ForeignKey(Company, related_name='superstockists', on_delete=models.RESTRICT)

    # Custom managers
    objects = models.Manager()  # Default manager
    filtered_objects = ChannelPartnerManager()  # Filtered manager

    class Meta:
        db_table = 'superstockists'
        verbose_name = 'Superstockist'
        verbose_name_plural = 'Superstockists'
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
            models.Index(fields=['state']),
        ]

    def clean(self):
        """Validate GST state matches selected state"""
        super().clean()
        if self.gstin and self.state:
            gst_state_code = self.gstin[:2]
            if gst_state_code != self.state.gst_code:
                raise ValidationError({'gstin': f'GST state code ({gst_state_code}) does not match selected state ({self.state.gst_code} - {self.state.name})'})

    def save(self, *args, **kwargs):
        if self.gstin:
            self.gstin = self.gstin.upper().strip()
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.name}"


class SuperstockistLocation(models.Model):
    """Location mapping for Superstockist - State/Cities/Areas coverage"""
    superstockist = models.ForeignKey(Superstockist, related_name='locations', on_delete=models.CASCADE)
    state = models.ForeignKey(State, related_name='superstockist_locations', on_delete=models.RESTRICT)
    city = models.ForeignKey(City, related_name='superstockist_locations',
                             on_delete=models.RESTRICT, null=True, blank=True)
    area = models.ForeignKey(Area, related_name='superstockist_locations',
                             on_delete=models.RESTRICT, null=True, blank=True)

    class Meta:
        db_table = 'superstockist_locations'
        unique_together = ('superstockist', 'state', 'city', 'area')
        indexes = [
            models.Index(fields=['superstockist', 'state']),
            models.Index(fields=['state', 'city', 'area']),
        ]

    def __str__(self):
        location = self.state.name
        if self.city:
            location += f" - {self.city.name}"
        if self.area:
            location += f" - {self.area.name}"
        return f"{self.superstockist.name}: {location}"


class SuperstockistContact(BaseModel):
    superstockist = models.ForeignKey(Superstockist, related_name='contacts', on_delete=models.CASCADE)
    contact_person = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        db_table = 'superstockist_contacts'
        ordering = ['-is_primary', 'contact_person']
        verbose_name = 'Superstockist Contact'
        verbose_name_plural = 'Superstockist Contacts'

    def __str__(self):
        return f"{self.superstockist.name} - {self.contact_person}"


class Distributor(DuplicateValidationMixin, CodeModel):
    """Distributor Master - Mid tier in channel partner hierarchy"""
    CODE_PREFIX = 'DST'

    name = models.CharField(max_length=200, help_text='Distributor name')

    # Hierarchy Link (optional based on enforce_channel_hierarchy flag)
    superstockist = models.ForeignKey(
        Superstockist,
        related_name='distributors',
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        help_text='Parent superstockist (required if hierarchy enforced)'
    )

    # User creation fields
    user_username = models.CharField(max_length=255, blank=True, null=True, help_text='Username for auto-created user')
    user_password = models.CharField(max_length=255, blank=True, null=True, help_text='Password for auto-created user')
    user_phone = models.CharField(max_length=15, blank=True, null=True, help_text='Phone number for auto-created user')
    user_device_access = models.SmallIntegerField(choices=DEVICE_ACCESS_CHOICES, blank=True, null=True, default=3, help_text='Device access for user')
    user_companies = models.ManyToManyField(Company, related_name='distributor_user_companies', blank=True, help_text='Companies for user access')
    user_has_all_companies = models.BooleanField(default=False, help_text='User has access to all companies')
    user_locations = models.ManyToManyField(Location, related_name='distributor_user_locations', blank=True, help_text='Locations for user access')
    user_has_all_locations = models.BooleanField(default=False, help_text='User has access to all locations')
    user_groups = models.ManyToManyField(Group, related_name='distributor_user_groups', blank=True, help_text='Groups for user')

    # Billing Address
    country = models.ForeignKey(Country, related_name='distributors', on_delete=models.RESTRICT, null=True, blank=True, help_text='Billing country')
    state = models.ForeignKey(State, related_name='distributors', on_delete=models.RESTRICT, help_text='Billing state')
    district = models.ForeignKey(
        District,
        related_name='distributors',
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        help_text='Billing district')
    mandal = models.ForeignKey(
        Mandal,
        related_name='distributors',
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        help_text='Billing mandal')
    city = models.ForeignKey(
        City,
        related_name='distributors',
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        help_text='Billing city')
    area = models.ForeignKey(
        Area,
        related_name='distributors',
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        help_text='Billing village/town')
    street = models.CharField(max_length=200, blank=True, null=True, help_text='Billing street')
    address = models.TextField(blank=True, null=True, help_text='Billing address')
    pincode = models.CharField(max_length=10, blank=True, null=True, help_text='Billing PIN code')

    # Shipping Address
    shipping_same_as_billing = models.BooleanField(default=True, help_text='Use billing address for shipping')
    shipping_country = models.ForeignKey(
        Country,
        related_name='distributors_shipping',
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        help_text='Shipping country')
    shipping_state = models.ForeignKey(
        State,
        related_name='distributors_shipping',
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        help_text='Shipping state')
    shipping_district = models.ForeignKey(
        District,
        related_name='distributors_shipping',
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        help_text='Shipping district')
    shipping_mandal = models.ForeignKey(
        Mandal,
        related_name='distributors_shipping',
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        help_text='Shipping mandal')
    shipping_city = models.ForeignKey(
        City,
        related_name='distributors_shipping',
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        help_text='Shipping city')
    shipping_area = models.ForeignKey(
        Area,
        related_name='distributors_shipping',
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        help_text='Shipping village/town')
    shipping_street = models.CharField(max_length=200, blank=True, null=True, help_text='Shipping street')
    shipping_address = models.TextField(blank=True, null=True, help_text='Shipping address')
    shipping_pincode = models.CharField(max_length=10, blank=True, null=True, help_text='Shipping PIN code')

    # Financial Information
    gstin = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        unique=True,
        validators=[validate_gst_number],
        help_text='GST Identification Number (15 characters)'
    )
    pan = models.CharField(max_length=10, blank=True, null=True, help_text='PAN Number')
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text='Credit limit amount')
    credit_days = models.IntegerField(default=0, help_text='Credit period in days')

    # Bank Details
    aadhar = models.CharField(max_length=12, blank=True, null=True, help_text='Aadhar Number (12 digits)')
    bank_account_number = models.CharField(max_length=50, blank=True, null=True, help_text='Bank account number')
    bank_name = models.CharField(max_length=200, blank=True, null=True, help_text='Bank name')
    bank_branch = models.CharField(max_length=200, blank=True, null=True, help_text='Bank branch')
    bank_ifsc = models.CharField(max_length=11, blank=True, null=True, help_text='IFSC code')
    bank_account_type = models.CharField(
        max_length=20,
        choices=[
            ('SAVINGS',
             'Savings'),
            ('CURRENT',
             'Current')],
        blank=True,
        null=True,
        help_text='Account type')
    google_location = models.TextField(blank=True, null=True, help_text='Google Maps location URL')

    # Status
    is_active = models.BooleanField(default=True, help_text='Active status')
    effective_from = models.DateField(blank=True, null=True, help_text='Effective from date')
    effective_to = models.DateField(blank=True, null=True, help_text='Effective to date')

    agent = models.ForeignKey(
        'Agent',
        related_name='distributors',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Tagged agent/broker'
    )

    # ERP Integration
    erp_code = models.CharField(max_length=50, blank=True, null=True, help_text='ERP system code')

    # Organization Link
    company = models.ForeignKey(Company, related_name='distributors', on_delete=models.RESTRICT)

    # Custom managers
    objects = models.Manager()  # Default manager
    filtered_objects = ChannelPartnerManager()  # Filtered manager

    class Meta:
        db_table = 'distributors'
        verbose_name = 'Distributor'
        verbose_name_plural = 'Distributors'
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
            models.Index(fields=['state']),
            models.Index(fields=['superstockist']),
        ]

    # def clean(self):
    #     """Validate GST state matches selected state"""
    #     super().clean()
    #     if self.gstin and self.state:
    #         gst_state_code = self.gstin[:2]
    #         if gst_state_code != self.state.gst_code:
    #             raise ValidationError({'gstin': f'GST state code ({gst_state_code}) does not match selected state ({self.state.gst_code} - {self.state.name})'})

    def save(self, *args, **kwargs):
        if self.gstin:
            self.gstin = self.gstin.upper().strip()
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.name}"


class DistributorLocation(models.Model):
    """Location mapping for Distributor - State/District/Mandal/City/Area coverage"""
    distributor = models.ForeignKey(Distributor, related_name='locations', on_delete=models.CASCADE)
    state = models.ForeignKey(State, related_name='distributor_locations', on_delete=models.RESTRICT)
    district = models.ForeignKey(District, related_name='distributor_locations',
                                 on_delete=models.RESTRICT, null=True, blank=True)
    mandal = models.ForeignKey(Mandal, related_name='distributor_locations',
                               on_delete=models.RESTRICT, null=True, blank=True)
    city = models.ForeignKey(City, related_name='distributor_locations',
                             on_delete=models.RESTRICT, null=True, blank=True)
    area = models.ForeignKey(Area, related_name='distributor_locations',
                             on_delete=models.RESTRICT, null=True, blank=True)

    class Meta:
        db_table = 'distributor_locations'
        unique_together = ('distributor', 'state', 'district', 'mandal', 'city', 'area')
        indexes = [
            models.Index(fields=['distributor', 'state']),
            models.Index(fields=['state', 'district', 'mandal', 'city', 'area']),
        ]

    def __str__(self):
        location = self.state.name
        if self.district:
            location += f" - {self.district.name}"
        if self.mandal:
            location += f" - {self.mandal.name}"
        if self.city:
            location += f" - {self.city.name}"
        if self.area:
            location += f" - {self.area.name}"
        return f"{self.distributor.name}: {location}"


class DistributorContact(BaseModel):
    distributor = models.ForeignKey(Distributor, related_name='contacts', on_delete=models.CASCADE)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        db_table = 'distributor_contacts'
        ordering = ['-is_primary', 'contact_person']
        verbose_name = 'Distributor Contact'
        verbose_name_plural = 'Distributor Contacts'

    def __str__(self):
        return f"{self.distributor.name} - {self.contact_person}"


class Retailer(DuplicateValidationMixin, CodeModel):
    """Retailer Master - Bottom tier in channel partner hierarchy"""
    CODE_PREFIX = 'RTL'

    name = models.CharField(max_length=200, help_text='Retailer name')

    # Hierarchy Link (optional based on enforce_channel_hierarchy flag)
    distributor = models.ForeignKey(
        Distributor,
        related_name='retailers',
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        help_text='Parent distributor (required if hierarchy enforced)'
    )

    # User creation fields
    user_username = models.CharField(max_length=255, blank=True, null=True, help_text='Username for auto-created user')
    user_password = models.CharField(max_length=255, blank=True, null=True, help_text='Password for auto-created user')
    user_phone = models.CharField(max_length=15, blank=True, null=True, help_text='Phone number for auto-created user')
    user_device_access = models.SmallIntegerField(choices=DEVICE_ACCESS_CHOICES, blank=True, null=True, default=3, help_text='Device access for user')
    user_companies = models.ManyToManyField(Company, related_name='retailer_user_companies', blank=True, help_text='Companies for user access')
    user_has_all_companies = models.BooleanField(default=False, help_text='User has access to all companies')
    user_locations = models.ManyToManyField(Location, related_name='retailer_user_locations', blank=True, help_text='Locations for user access')
    user_has_all_locations = models.BooleanField(default=False, help_text='User has access to all locations')
    user_groups = models.ManyToManyField(Group, related_name='retailer_user_groups', blank=True, help_text='Groups for user')

    # Billing Address
    state = models.ForeignKey(State, related_name='retailers', on_delete=models.RESTRICT, help_text='Billing state')
    city = models.ForeignKey(
        City,
        related_name='retailers',
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        help_text='Billing city')
    area = models.ForeignKey(
        Area,
        related_name='retailers',
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        help_text='Billing area')
    address = models.TextField(blank=True, null=True, help_text='Billing address')
    pincode = models.CharField(max_length=10, blank=True, null=True, help_text='Billing PIN code')

    # Shipping Address
    shipping_same_as_billing = models.BooleanField(default=True, help_text='Use billing address for shipping')
    shipping_state = models.ForeignKey(
        State,
        related_name='retailers_shipping',
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        help_text='Shipping state')
    shipping_city = models.ForeignKey(
        City,
        related_name='retailers_shipping',
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        help_text='Shipping city')
    shipping_area = models.ForeignKey(
        Area,
        related_name='retailers_shipping',
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        help_text='Shipping area')
    shipping_address = models.TextField(blank=True, null=True, help_text='Shipping address')
    shipping_pincode = models.CharField(max_length=10, blank=True, null=True, help_text='Shipping PIN code')

    # Retailer Specific
    outlet_type = models.ForeignKey(
        'OutletType',
        related_name='retailers',
        on_delete=models.RESTRICT,
        null=True,  # Temporary for migration
        blank=True,  # Temporary for migration
        help_text='Type of outlet (e.g., Pharmacy, Kirana, Medical Store)'
    )
    outlet_size = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text='Size category (e.g., Small, Medium, Large)'
    )

    # Financial Information
    gstin = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        unique=True,
        validators=[validate_gst_number],
        help_text='GST Identification Number (15 characters)'
    )
    pan = models.CharField(max_length=10, blank=True, null=True, help_text='PAN Number')
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text='Credit limit amount')
    credit_days = models.IntegerField(default=0, help_text='Credit period in days')

    # Bank Details
    aadhar = models.CharField(max_length=12, blank=True, null=True, help_text='Aadhar Number (12 digits)')
    bank_account_number = models.CharField(max_length=50, blank=True, null=True, help_text='Bank account number')
    bank_name = models.CharField(max_length=200, blank=True, null=True, help_text='Bank name')
    bank_branch = models.CharField(max_length=200, blank=True, null=True, help_text='Bank branch')
    bank_ifsc = models.CharField(max_length=11, blank=True, null=True, help_text='IFSC code')
    bank_account_type = models.CharField(
        max_length=20,
        choices=[
            ('SAVINGS',
             'Savings'),
            ('CURRENT',
             'Current')],
        blank=True,
        null=True,
        help_text='Account type')
    google_location = models.TextField(blank=True, null=True, help_text='Google Maps location URL')

    # Status
    is_active = models.BooleanField(default=True, help_text='Active status')
    effective_from = models.DateField(blank=True, null=True, help_text='Effective from date')
    effective_to = models.DateField(blank=True, null=True, help_text='Effective to date')

    # ERP Integration
    erp_code = models.CharField(max_length=50, blank=True, null=True, help_text='ERP system code')

    # Organization Link
    company = models.ForeignKey(Company, related_name='retailers', on_delete=models.RESTRICT)

    # Custom managers
    objects = models.Manager()  # Default manager
    filtered_objects = ChannelPartnerManager()  # Filtered manager

    class Meta:
        db_table = 'retailers'
        verbose_name = 'Retailer'
        verbose_name_plural = 'Retailers'
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
            models.Index(fields=['state']),
            models.Index(fields=['distributor']),
        ]

    # def clean(self):
    #     """Validate GST state matches selected state"""
    #     super().clean()
    #     if self.gstin and self.state:
    #         gst_state_code = self.gstin[:2]
    #         if gst_state_code != self.state.gst_code:
    #             raise ValidationError({'gstin': f'GST state code ({gst_state_code}) does not match selected state ({self.state.gst_code} - {self.state.name})'})

    def save(self, *args, **kwargs):
        if self.gstin:
            self.gstin = self.gstin.upper().strip()
        else:
            # Convert empty string to None to avoid unique constraint issues
            self.gstin = None
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.name}"


class RetailerLocation(models.Model):
    """Location mapping for Retailer - State/Cities/Areas coverage"""
    retailer = models.ForeignKey(Retailer, related_name='locations', on_delete=models.CASCADE)
    state = models.ForeignKey(State, related_name='retailer_locations', on_delete=models.RESTRICT)
    city = models.ForeignKey(City, related_name='retailer_locations', on_delete=models.RESTRICT, null=True, blank=True)
    area = models.ForeignKey(Area, related_name='retailer_locations', on_delete=models.RESTRICT, null=True, blank=True)

    class Meta:
        db_table = 'retailer_locations'
        unique_together = ('retailer', 'state', 'city', 'area')
        indexes = [
            models.Index(fields=['retailer', 'state']),
            models.Index(fields=['state', 'city', 'area']),
        ]

    def __str__(self):
        location = self.state.name
        if self.city:
            location += f" - {self.city.name}"
        if self.area:
            location += f" - {self.area.name}"
        return f"{self.retailer.name}: {location}"


class RetailerContact(BaseModel):
    retailer = models.ForeignKey(Retailer, related_name='contacts', on_delete=models.CASCADE)
    contact_person = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        db_table = 'retailer_contacts'
        ordering = ['-is_primary', 'contact_person']
        verbose_name = 'Retailer Contact'
        verbose_name_plural = 'Retailer Contacts'

    def __str__(self):
        return f"{self.retailer.name} - {self.contact_person}"


class OutletType(DuplicateValidationMixin, CodeModel):
    """Outlet Type Master - Defines different types of outlets (e.g., General Store, Medical Store, etc.)"""
    CODE_PREFIX = 'OUT'

    name = models.CharField(max_length=180, unique=True)
    erp_code = models.CharField(max_length=50, blank=True, null=True)
    erp_id = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Outlet Type'
        verbose_name_plural = 'Outlet Types'

    def __str__(self): return str(self.name)


class PriceBookDocument(CoreModel):
    """
    Master document for bulk price book entries
    Stores header information for each price book transaction
    """

    CODE_PREFIX = 'PBD'

    class LocationType(models.TextChoices):
        BASE = 'BASE', 'Base'
        STATE = 'STATE', 'State'
        CITY = 'CITY', 'City'
        AREA = 'AREA', 'Area'
        SUPERSTOCKIST = 'SUPERSTOCKIST', 'Superstockist'
        DISTRIBUTOR = 'DISTRIBUTOR', 'Distributor'
        RETAILER = 'RETAILER', 'Retailer'

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        ACTIVE = 'ACTIVE', 'Active'
        CLOSED = 'CLOSED', 'Closed'

    document_number = models.CharField(
        max_length=50,
        unique=True,
        help_text='Auto-generated document number (e.g., PB-25-26-1)'
    )
    document_date = models.DateField(help_text='Document date')
    location_type = models.CharField(
        max_length=20,
        choices=LocationType.choices,
        help_text='Type of location for this price book'
    )
    cp_filter_state = models.ForeignKey(
        State,
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        help_text='Optional state filter when selecting channel partners'
    )
    cp_filter_city = models.ForeignKey(
        City,
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        help_text='Optional city filter when selecting channel partners'
    )
    cp_filter_area = models.ForeignKey(
        Area,
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        help_text='Optional area filter when selecting channel partners'
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
        help_text='Document status (DRAFT, ACTIVE, CLOSED)'
    )
    effective_from = models.DateField(help_text='Price effective from date')
    effective_to = models.DateField(
        null=True,
        blank=True,
        help_text='Price effective until date (blank for indefinite)'
    )
    total_entries = models.IntegerField(default=0, help_text='Total number of price entries')
    remarks = models.TextField(blank=True, help_text='Remarks or notes')
    selected_categories = models.JSONField(
        default=list,
        blank=True,
        help_text='List of selected category IDs for filtering items'
    )
    selected_brands = models.JSONField(
        default=list,
        blank=True,
        help_text='List of selected brand IDs for filtering items'
    )

    class Meta:
        db_table = 'price_book_document'
        ordering = ['-document_date', '-created_on']
        verbose_name = 'Price Book Document'
        verbose_name_plural = 'Price Book Documents'
        indexes = [
            models.Index(fields=['document_number']),
            models.Index(fields=['document_date']),
            models.Index(fields=['location_type']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.document_number} - {self.document_date} ({self.get_location_type_display()}) [{self.get_status_display()}]"

    def clean(self):
        """Validate business rules"""
        from django.core.exceptions import ValidationError

        # Only one draft per location_type is allowed
        # if self.status == self.Status.DRAFT:
        #     existing_drafts = PriceBookDocument.objects.filter(
        #         location_type=self.location_type,
        #         status=self.Status.DRAFT,
        #         is_deleted=False
        #     )
        #     if self.pk:
        #         existing_drafts = existing_drafts.exclude(pk=self.pk)

        #     if existing_drafts.exists():
        #         raise ValidationError({
        #             'status': (
        #                 f"A draft already exists for {self.get_location_type_display()}. "
        #                 "Please finalize or delete it first."
        #             )
        #         })

    def save(self, *args, **kwargs):
        # self.full_clean()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_document_number():
        """
        Generate next document number in format: PB-FY-INCREMENT
        Example: PB-25-26-1
        Atomic operation to prevent race conditions.
        """
        from datetime import date
        from django.db import transaction
        import re

        today = date.today()

        # Calculate financial year (April to March)
        if today.month >= 4:  # April to December
            fy_start = today.year % 100
            fy_end = (today.year + 1) % 100
        else:  # January to March
            fy_start = (today.year - 1) % 100
            fy_end = today.year % 100

        fy_string = f"{fy_start:02d}-{fy_end:02d}"
        prefix = f"PB-{fy_string}"

        # Use atomic transaction with SELECT FOR UPDATE to prevent race conditions
        with transaction.atomic():
            # Compute max numeric suffix for this FY
            doc_numbers = PriceBookDocument.objects.filter(
                document_number__startswith=prefix
            ).select_for_update().values_list('document_number', flat=True)

            max_suffix = 0
            for dn in doc_numbers:
                match = re.search(r'-(\d+)$', dn or '')
                if match:
                    try:
                        max_suffix = max(max_suffix, int(match.group(1)))
                    except ValueError:
                        continue

            return f"{prefix}-{max_suffix + 1}"


class PriceBook(DuplicateValidationMixin, CodeModel):
    """
    Flexible price book supporting multiple price determination strategies
    Based on location hierarchy (State > City > Area) and channel partners
    """
    CODE_PREFIX = 'PB'

    class PriceType(models.TextChoices):
        BASE = 'BASE', 'Base Price'
        GEOGRAPHIC = 'GEOGRAPHIC', 'Geographic Price'
        CHANNEL_PARTNER = 'CHANNEL_PARTNER', 'Channel Partner Price'

    # Core Fields
    document = models.ForeignKey(
        PriceBookDocument,
        on_delete=models.CASCADE,
        related_name='price_entries',
        null=True,
        blank=True,
        help_text='Reference to price book document'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='price_books',
        help_text='Company this price belongs to'
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='prices',
        help_text='Item for which price is defined'
    )
    price_type = models.CharField(
        max_length=20,
        choices=PriceType.choices,
        default=PriceType.BASE,
        help_text='Type of pricing strategy'
    )

    # Geographic Fields (nullable - for GEOGRAPHIC type)
    state = models.ForeignKey(
        State,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='price_books',
        help_text='State for geographic pricing'
    )
    city = models.ForeignKey(
        City,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='price_books',
        help_text='City for geographic pricing'
    )
    area = models.ForeignKey(
        Area,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='price_books',
        help_text='Area for geographic pricing'
    )

    # Channel Partner Fields (nullable - for CHANNEL_PARTNER type)
    superstockist = models.ForeignKey(
        Superstockist,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='price_books',
        help_text='Superstockist-specific pricing'
    )
    distributor = models.ForeignKey(
        Distributor,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='price_books',
        help_text='Distributor-specific pricing'
    )
    retailer = models.ForeignKey(
        Retailer,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='price_books',
        help_text='Retailer-specific pricing'
    )

    # Price Fields
    base_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Base/Cost price (optional)'
    )
    selling_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Selling price to customer'
    )
    mrp = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Maximum Retail Price (optional)'
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text='Discount percentage from MRP'
    )

    # Validity Period
    effective_from = models.DateField(help_text='Price effective from date')
    effective_to = models.DateField(
        null=True,
        blank=True,
        help_text='Price effective until date (blank for indefinite)'
    )
    is_active = models.BooleanField(default=True, help_text='Is this price active')

    # ERP Integration
    erp_code = models.CharField(max_length=100, blank=True, help_text='ERP price code')
    erp_id = models.CharField(max_length=100, blank=True, help_text='ERP price ID')

    # Audit fields
    remarks = models.TextField(blank=True, help_text='Remarks or notes about this price')

    class Meta:
        db_table = 'price_book'
        ordering = ['-created_on']
        verbose_name = 'Price Book'
        verbose_name_plural = 'Price Books'
        indexes = [
            models.Index(fields=['company', 'item', 'is_active']),
            models.Index(fields=['price_type', 'is_active']),
            models.Index(fields=['effective_from', 'effective_to']),
            models.Index(fields=['code']),
        ]
        constraints = [
            # Ensure only one active price per exact combination
            models.UniqueConstraint(
                fields=['company', 'item', 'state', 'city', 'area',
                        'superstockist', 'distributor', 'retailer'],
                condition=models.Q(is_active=True, is_deleted=False),
                name='unique_active_price_combination'
            )
        ]

    def __str__(self):
        return f"{self.code} - {self.item.name} - {self.get_price_type_display()}"

    def clean(self):
        from django.core.exceptions import ValidationError
        errors = {}

        # Validate price relationships
        if self.base_price and self.selling_price and self.base_price > self.selling_price:
            errors['selling_price'] = 'Selling price must be greater than or equal to base price'

        if self.selling_price and self.mrp and self.selling_price > self.mrp:
            errors['mrp'] = 'MRP must be greater than or equal to selling price'

        # Validate discount percentage
        if self.discount_percentage < 0 or self.discount_percentage > 100:
            errors['discount_percentage'] = 'Discount percentage must be between 0 and 100'

        # Validate date range
        if self.effective_from and self.effective_to:
            if self.effective_from > self.effective_to:
                errors['effective_to'] = 'Effective to date must be after effective from date'

        # Validate price type specific fields
        if self.price_type == self.PriceType.BASE:
            # Base price should not have any location or partner fields
            if any([self.state, self.city, self.area, self.superstockist, self.distributor, self.retailer]):
                errors['price_type'] = 'Base price cannot have location or partner specific fields'

        elif self.price_type == self.PriceType.GEOGRAPHIC:
            # Geographic price must have at least one location field
            if not any([self.state, self.city, self.area]):
                errors['price_type'] = 'Geographic price must have at least one location field (state, city, or area)'

            # Validate location hierarchy
            if self.area and not self.city:
                errors['area'] = 'Area requires city to be selected'
            if self.city and not self.state:
                errors['city'] = 'City requires state to be selected'

            # Geographic price should not have partner fields
            if any([self.superstockist, self.distributor, self.retailer]):
                errors['price_type'] = 'Geographic price cannot have channel partner fields'

        elif self.price_type == self.PriceType.CHANNEL_PARTNER:
            # Channel partner price must have at least one partner field
            if not any([self.superstockist, self.distributor, self.retailer]):
                errors['price_type'] = 'Channel partner price must have at least one partner field'

            # Channel partner price should not have location fields
            if any([self.state, self.city, self.area]):
                errors['price_type'] = 'Channel partner price cannot have location fields'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Auto-uppercase code
        if self.code:
            self.code = self.code.upper()

        # Capture old instance for history tracking
        old_instance = None
        if self.pk:
            try:
                old_instance = PriceBook.objects.get(pk=self.pk)
            except PriceBook.DoesNotExist:
                pass

        # Run validation
        self.full_clean()

        # Save the instance
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Create history record
        self._create_history_record(old_instance, is_new)

    def _create_history_record(self, old_instance, is_new):
        """Create a history record tracking changes"""
        action = 'CREATE' if is_new else 'UPDATE'
        changes = {}

        if not is_new and old_instance:
            # Track what changed
            tracked_fields = [
                'base_price', 'selling_price', 'mrp', 'discount_percentage',
                'effective_from', 'effective_to', 'is_active', 'price_type',
                'state_id', 'city_id', 'area_id',
                'superstockist_id', 'distributor_id', 'retailer_id'
            ]

            for field in tracked_fields:
                old_value = getattr(old_instance, field, None)
                new_value = getattr(self, field, None)
                if old_value != new_value:
                    changes[field] = {
                        'old': str(old_value) if old_value is not None else None,
                        'new': str(new_value) if new_value is not None else None
                    }

        # Create history record
        PriceBookHistory.objects.create(
            price_book=self,
            action=action,
            changes=changes,
            base_price=self.base_price,
            selling_price=self.selling_price,
            mrp=self.mrp,
            discount_percentage=self.discount_percentage,
            effective_from=self.effective_from,
            effective_to=self.effective_to,
            is_active=self.is_active,
            remarks=self.remarks,
            created_by_type=self.created_by_type,
            created_by_identifier=self.created_by_identifier
        )

    def get_scope_display(self):
        """Return human-readable scope of this price"""
        if self.price_type == self.PriceType.BASE:
            return 'Company-wide'
        elif self.price_type == self.PriceType.GEOGRAPHIC:
            parts = []
            if self.area:
                parts.append(self.area.name)
            if self.city:
                parts.append(self.city.name)
            if self.state:
                parts.append(self.state.name)
            return ', '.join(parts) if parts else 'N/A'
        elif self.price_type == self.PriceType.CHANNEL_PARTNER:
            if self.retailer:
                return f'Retailer: {self.retailer.name}'
            elif self.distributor:
                return f'Distributor: {self.distributor.name}'
            elif self.superstockist:
                return f'Superstockist: {self.superstockist.name}'
        return 'N/A'

    def get_margin_percentage(self):
        """Calculate margin percentage"""
        if self.base_price and self.selling_price and self.base_price > 0:
            margin = ((self.selling_price - self.base_price) / self.base_price) * 100
            return round(margin, 2)
        return 0


class PriceBookHistory(models.Model):
    """
    Audit trail for Price Book changes
    Tracks all create, update, and delete operations
    """

    class Action(models.TextChoices):
        CREATE = 'CREATE', 'Created'
        UPDATE = 'UPDATE', 'Updated'
        DELETE = 'DELETE', 'Deleted'

    # Link to price book
    price_book = models.ForeignKey(
        PriceBook,
        on_delete=models.CASCADE,
        related_name='history',
        help_text='Price book this history belongs to'
    )

    # Action details
    action = models.CharField(
        max_length=10,
        choices=Action.choices,
        help_text='Type of action performed'
    )
    changes = models.JSONField(
        default=dict,
        blank=True,
        help_text='JSON of field changes {field: {old: value, new: value}}'
    )

    # Snapshot of prices at this point
    base_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2)
    mrp = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField()
    remarks = models.TextField(blank=True)

    # Audit information
    created_on = models.DateTimeField(auto_now_add=True)
    created_by_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text='Type of user/system that created'
    )
    created_by_identifier = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Identifier of creator'
    )

    class Meta:
        db_table = 'price_book_history'
        ordering = ['-created_on']
        verbose_name = 'Price Book History'
        verbose_name_plural = 'Price Book History'
        indexes = [
            models.Index(fields=['price_book', '-created_on']),
            models.Index(fields=['action', '-created_on']),
        ]

    def __str__(self):
        return f"{self.price_book.code} - {self.get_action_display()} - {self.created_on}"

    def get_change_summary(self):
        """Get human-readable summary of changes"""
        if not self.changes:
            return f"Price book {self.get_action_display().lower()}"

        summary = []
        for field, change in self.changes.items():
            field_name = field.replace('_', ' ').title()
            summary.append(f"{field_name}: {change['old']} → {change['new']}")

        return ', '.join(summary)


# ============================================================================
# SCHEMES MODULE - PROMOTIONS & INCENTIVES
# ============================================================================

class Scheme(CoreModel):
    """
    Master table for schemes/promotions
    Defines conditions and benefits for promotional offers
    """

    class SchemeType(models.TextChoices):
        QUANTITY = 'QUANTITY', 'Quantity Based'
        VALUE = 'VALUE', 'Value Based'
        COMBO = 'COMBO', 'Combo Offer'
        SLAB = 'SLAB', 'Slab Based'
        FLAT = 'FLAT', 'Flat Discount'

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE = 'INACTIVE', 'Inactive'
        EXPIRED = 'EXPIRED', 'Expired'

    CODE_PREFIX = 'SCH'

    # Basic Info
    code = models.CharField(max_length=50, unique=True, help_text='Unique scheme code')
    name = models.CharField(max_length=255, help_text='Scheme name')
    description = models.TextField(blank=True, help_text='Detailed scheme description')
    scheme_type = models.CharField(
        max_length=20,
        choices=SchemeType.choices,
        help_text='Type of scheme'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        help_text='Scheme status'
    )

    # Priority & Stacking
    priority = models.IntegerField(
        default=0,
        help_text='Higher number = Higher Priority (0-100)'
    )
    is_stackable = models.BooleanField(
        default=False,
        help_text='Can combine with other schemes'
    )
    max_applications = models.IntegerField(
        null=True,
        blank=True,
        help_text='Max times scheme can apply in single order'
    )

    # Validity
    effective_from = models.DateField(help_text='Scheme effective from date')
    effective_to = models.DateField(
        null=True,
        blank=True,
        help_text='Scheme effective to date (null = no end date)'
    )

    # Company
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        related_name='schemes',
        null=True,
        blank=True,
        help_text='Company this scheme belongs to'
    )

    # Limits
    max_discount_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Maximum discount amount for this scheme'
    )
    # Approval
    requires_approval = models.BooleanField(
        default=False,
        help_text='Scheme requires approval to activate'
    )
    approved_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='approved_schemes'
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When scheme was approved'
    )

    class Meta:
        db_table = 'scheme'
        ordering = ['-priority', '-created_on']
        verbose_name = 'Scheme'
        verbose_name_plural = 'Schemes'
        indexes = [
            models.Index(fields=['status', 'effective_from', 'effective_to']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['scheme_type', 'status']),
        ]
        permissions = (
            ("can_cancel_scheme", "Can cancel scheme"),
        )


    def __str__(self):
        return f"{self.code} - {self.name} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        today = timezone.now().date()
        if self.status == self.Status.EXPIRED and self.effective_to and self.effective_to >= today:
            self.status = self.Status.ACTIVE
        super().save(*args, **kwargs)


class SchemeCondition(models.Model):
    """
    Conditions that must be met for scheme to apply
    """

    class ConditionType(models.TextChoices):
        MIN_QUANTITY = 'MIN_QUANTITY', 'Minimum Quantity'
        MIN_VALUE = 'MIN_VALUE', 'Minimum Value'
        MAX_QUANTITY = 'MAX_QUANTITY', 'Maximum Quantity'
        MAX_VALUE = 'MAX_VALUE', 'Maximum Value'
        EXACT_QUANTITY = 'EXACT_QUANTITY', 'Exact Quantity'
        QUANTITY_RANGE = 'QUANTITY_RANGE', 'Quantity Range'
        VALUE_RANGE = 'VALUE_RANGE', 'Value Range'
        ITEM_COMBO = 'ITEM_COMBO', 'Item Combination'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scheme = models.ForeignKey(
        'Scheme',
        on_delete=models.CASCADE,
        related_name='conditions'
    )
    condition_type = models.CharField(
        max_length=30,
        choices=ConditionType.choices,
        help_text='Type of condition'
    )

    # Numeric conditions (for MIN, RANGE, EXACT)
    value_from = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Minimum value or range start'
    )
    value_to = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Maximum value (for range conditions)'
    )

    # Item/Category conditions
    item = models.ForeignKey(
        'Item',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        help_text='Item for item-specific conditions'
    )
    category = models.ForeignKey(
        'Category',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        help_text='Category for category-specific conditions'
    )

    # Multiple items for ITEM_COMBO condition
    items = models.JSONField(
        default=list,
        blank=True,
        help_text='List of item IDs required for ITEM_COMBO condition'
    )

    # Logical operator for multiple conditions
    logical_operator = models.CharField(
        max_length=3,
        choices=[('AND', 'AND'), ('OR', 'OR')],
        default='AND',
        help_text='Logical operator for multiple conditions'
    )

    class Meta:
        db_table = 'scheme_condition'
        ordering = ['id']
        verbose_name = 'Scheme Condition'
        verbose_name_plural = 'Scheme Conditions'

    def __str__(self):
        return f"{self.scheme.code} - {self.get_condition_type_display()}"


class SchemeBenefit(models.Model):
    """
    Benefits provided by the scheme
    """

    class BenefitType(models.TextChoices):
        DISCOUNT_PERCENTAGE = 'DISCOUNT_PERCENTAGE', 'Discount %'
        DISCOUNT_AMOUNT = 'DISCOUNT_AMOUNT', 'Discount Amount'
        FREE_ITEM = 'FREE_ITEM', 'Free Product'
        FREE_QUANTITY = 'FREE_QUANTITY', 'Free Quantity'
        CASHBACK = 'CASHBACK', 'Cashback'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scheme = models.ForeignKey(
        'Scheme',
        on_delete=models.CASCADE,
        related_name='benefits'
    )
    benefit_type = models.CharField(
        max_length=30,
        choices=BenefitType.choices,
        help_text='Type of benefit'
    )

    # Discount benefits
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Discount % or amount depending on type'
    )
    max_discount_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Maximum discount for this benefit'
    )

    # Free item benefits
    free_item = models.ForeignKey(
        'Item',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='scheme_free_items'
    )
    free_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        help_text='Quantity of free item'
    )

    # Apply to (which items get the benefit)
    apply_to_item = models.ForeignKey(
        'Item',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='benefit_targets'
    )
    apply_to_category = models.ForeignKey(
        'Category',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='benefit_targets'
    )
    apply_to_all = models.BooleanField(
        default=False,
        help_text='Apply benefit to all items in order'
    )

    class Meta:
        db_table = 'scheme_benefit'
        ordering = ['id']
        verbose_name = 'Scheme Benefit'
        verbose_name_plural = 'Scheme Benefits'

    def __str__(self):
        return f"{self.scheme.code} - {self.get_benefit_type_display()}"


class SchemeApplicability(models.Model):
    """
    Defines which customers/geography scheme applies to
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scheme = models.ForeignKey(
        'Scheme',
        on_delete=models.CASCADE,
        related_name='applicability'
    )

    # Geography
    state = models.ForeignKey(
        'State',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        help_text='State for geographic targeting'
    )
    city = models.ForeignKey(
        'City',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        help_text='City for geographic targeting'
    )
    area = models.ForeignKey(
        'Area',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        help_text='Area for geographic targeting'
    )

    # Channel Partners
    customer_type = models.CharField(
        max_length=20,
        choices=[
            ('ALL', 'All'),
            ('RETAILER', 'Retailer'),
            ('DISTRIBUTOR', 'Distributor'),
            ('SUPERSTOCKIST', 'Superstockist'),
        ],
        default='ALL',
        help_text='Type of customer'
    )

    retailer = models.ForeignKey(
        'Retailer',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        help_text='Specific retailer'
    )
    distributor = models.ForeignKey(
        'Distributor',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        help_text='Specific distributor'
    )
    superstockist = models.ForeignKey(
        'Superstockist',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        help_text='Specific superstockist'
    )

    # Apply to all flag
    apply_to_all = models.BooleanField(
        default=True,
        help_text='Apply to all matching customers'
    )

    class Meta:
        db_table = 'scheme_applicability'
        ordering = ['id']
        verbose_name = 'Scheme Applicability'
        verbose_name_plural = 'Scheme Applicability'

    def __str__(self):
        return f"{self.scheme.code} - {self.get_customer_type_display()}"


class SchemeItem(models.Model):
    """
    Items included in scheme (for item/category targeting)
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scheme = models.ForeignKey(
        'Scheme',
        on_delete=models.CASCADE,
        related_name='items'
    )
    item = models.ForeignKey(
        'Item',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        help_text='Item included in scheme'
    )
    category = models.ForeignKey(
        'Category',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        help_text='Category included in scheme'
    )
    include_all_items = models.BooleanField(
        default=False,
        help_text='Scheme applies to all items'
    )

    class Meta:
        db_table = 'scheme_item'
        ordering = ['id']
        verbose_name = 'Scheme Item'
        verbose_name_plural = 'Scheme Items'
        unique_together = [['scheme', 'item']]

    def __str__(self):
        if self.include_all_items:
            return f"{self.scheme.code} - All Items"
        return f"{self.scheme.code} - {self.item.code if self.item else self.category.code}"


class SchemeHistory(models.Model):
    """
    Audit trail for scheme changes
    """

    class Action(models.TextChoices):
        CREATED = 'CREATED', 'Created'
        UPDATED = 'UPDATED', 'Updated'
        ACTIVATED = 'ACTIVATED', 'Activated'
        DEACTIVATED = 'DEACTIVATED', 'Deactivated'
        DELETED = 'DELETED', 'Deleted'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scheme = models.ForeignKey(
        'Scheme',
        on_delete=models.CASCADE,
        related_name='history'
    )
    action = models.CharField(
        max_length=20,
        choices=Action.choices,
        help_text='Action performed'
    )
    changes = models.JSONField(
        default=dict,
        blank=True,
        help_text='JSON of changes made'
    )
    changed_by_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text='Type of user/system'
    )
    changed_by_identifier = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Identifier of who made change'
    )
    changed_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When change was made'
    )

    class Meta:
        db_table = 'scheme_history'
        ordering = ['-changed_at']
        verbose_name = 'Scheme History'
        verbose_name_plural = 'Scheme History'
        indexes = [
            models.Index(fields=['scheme', '-changed_at']),
            models.Index(fields=['action', '-changed_at']),
        ]

    def __str__(self):
        return f"{self.scheme.code} - {self.get_action_display()} - {self.changed_at}"

    def get_change_summary(self):
        """Get human-readable summary of changes"""
        if not self.changes:
            return f"Scheme {self.get_action_display().lower()}"

        summary = []
        for field, change in self.changes.items():
            field_name = field.replace('_', ' ').title()
            if isinstance(change, dict):
                old_val = change.get('old', 'N/A')
                new_val = change.get('new', 'N/A')
            else:
                old_val = 'N/A'
                new_val = change
            summary.append(f"{field_name}: {old_val} → {new_val}")

        return ', '.join(summary)


# ============================================================================
# AGENT / BROKER MASTER
# ============================================================================

class Agent(DuplicateValidationMixin, CodeModel):
    """Agent/Broker Master - Can be tagged to Distributors"""
    CODE_PREFIX = 'AGT'

    name = models.CharField(max_length=200, help_text='Agent/Broker name')
    phone = models.CharField(max_length=15, help_text='Phone number')
    email = models.EmailField(max_length=100, blank=True, null=True, help_text='Email address (optional)')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'agents'
        ordering = ['code']
        verbose_name = 'Agent'
        verbose_name_plural = 'Agents'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


# ============================================================================
# SALES ORDER MODELS - MOVED TO Sales APP
# ============================================================================

# ============================================================================
# SALES ORDER MODELS MOVED TO Sales APP
# ============================================================================
# The SalesOrder, SalesOrderItem, and SalesOrderHistory models have been
# moved to the Sales app. If you need to reference them, import from:
# from Sales.models import SalesOrder, SalesOrderItem, SalesOrderHistory
# ============================================================================


# ============================================================================
# PROJECT MASTER — SRS Module 6 (Real Estate Project Management)
# ============================================================================

class Project(DuplicateValidationMixin, CoreModel):
    """
    Real Estate Project Master.
    Stores projects (Plot/Flat developments) that Leads → Site Visits → Bookings hang off.
    """
    CODE_PREFIX = 'PROJ'

    PROJECT_STATUS_CHOICES = [
        ('UPCOMING', 'Upcoming'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('SOLD_OUT', 'Sold Out'),
    ]

    PROJECT_TYPE_CHOICES = [
        ('PLOT', 'Plot'),
        ('FLAT', 'Flat'),
        ('VILLA', 'Villa'),
        ('MIXED', 'Mixed'),
    ]

    APPROVAL_TYPE_CHOICES = [
        ('GVMC', 'GVMC'),
        ('VMRDA', 'VMRDA'),
        ('DTCP', 'DTCP'),
        ('HMDA', 'HMDA'),
        ('PANCHAYAT', 'Panchayat'),
        ('PENDING', 'Pending'),
        ('NA', 'N/A'),
    ]

    name = models.CharField(max_length=200, db_index=True)
    developer_name = models.CharField(max_length=200, blank=True, null=True)
    project_type = models.CharField(
        max_length=20, choices=PROJECT_TYPE_CHOICES, default='PLOT', db_index=True,
    )
    location = models.CharField(
        max_length=255, blank=True, null=True,
        help_text='Project location (free text)',
    )
    approval_type = models.CharField(
        max_length=20, choices=APPROVAL_TYPE_CHOICES, default='PENDING',
    )

    status = models.CharField(
        max_length=20, choices=PROJECT_STATUS_CHOICES, default='UPCOMING', db_index=True,
    )
    sub = models.ImageField(upload_to='projects/', null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['project_type']),
            models.Index(fields=['is_active']),
        ]
        permissions = [
            ("export_project", "Can export projects"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def delete(self, *args, **kwargs):
        """Soft-delete: flip is_deleted instead of removing the row."""
        from django.utils import timezone
        self.is_deleted = True
        self.modified_on = timezone.now()
        self.save(update_fields=['is_deleted', 'modified_on'])

    def hard_delete(self, *args, **kwargs):
        """Force a real DELETE — bypass soft-delete."""
        super().delete(*args, **kwargs)


class ProjectStatusHistory(BaseModel):
    """
    Audit trail for Project status changes.
    Mirrors the LeadStatusHistory pattern from the Lead app.
    """
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='status_history',
    )
    from_status = models.CharField(
        max_length=20, choices=Project.PROJECT_STATUS_CHOICES,
        blank=True, null=True,
    )
    to_status = models.CharField(
        max_length=20, choices=Project.PROJECT_STATUS_CHOICES,
    )
    changed_by_identifier = models.CharField(max_length=255, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_on']
        verbose_name = 'Project Status History'
        verbose_name_plural = 'Project Status History'
        indexes = [
            models.Index(fields=['project', '-created_on']),
        ]

    def __str__(self):
        return f"{self.project.code}: {self.from_status or 'NEW'} → {self.to_status}"
