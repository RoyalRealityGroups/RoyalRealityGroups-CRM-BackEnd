
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from Core.Core.permissions.permissions import GetPermission
from Core.Reports.import_export_models import register_report_models
from Core.Users.admin import DeviceResource
from Core.Users.models import Device
from Masters.views import AreaFilter, BrandFilter, CategoryFilter, CityFilter, DistrictFilter, MandalFilter, DistributorFilter, ItemFilter, ItemTaxCompositionFilter, LocationFilter, PriceBookFilter, RetailerFilter, RouteFilter, StateFilter, SuperstockistFilter, TaxFilter, WareHouseFilter
from Users.resources import UserResource
from Users.views import UserFilter
from django.contrib.auth import get_user_model
# Delivery / POD imports
from Delivery.models import ProofOfDelivery
from Delivery.resources import ProofOfDeliveryResource
from Delivery.views import ProofOfDeliveryReportFilter
from utils import apply_company_location_filter

# Receipts imports
from Receipts.models import Receipt
from Receipts.resources import ReceiptResource
from Receipts.views import ReceiptExportFilter

# Import Master models and resources
from Masters.models import (
    UOM, Country, ItemTaxComposition, OutletType, Route, RouteCoverage, State, District, Mandal, City, Location, Tax, WareHouse, Area, Category, Brand, Item,
    Superstockist, Distributor, Retailer, Company, Agent,
    SuperstockistLocation, DistributorLocation, RetailerLocation,
    PriceBook
)
from Masters.resources import (
    CompanyResource, CountryResource, ItemTaxCompositionResource, OutletTypeResource, RouteResource, StateResource, DistrictResource, MandalResource, CityResource, AreaResource,
    LocationResource, TaxResource, UOMResource, WareHouseResource, CategoryResource, BrandResource, ItemResource,
    SuperstockistResource, DistributorResource, RetailerResource,
    SuperstockistLocationResource, DistributorLocationResource, RetailerLocationResource,
    PriceBookResource,
    AgentResource
)

User = get_user_model()

def dict_to_list_of_dicts(data: dict):
    """Convert {'A': val1, 'B': val2} → [{'A': val1}, {'B': val2}]"""
    return [{k: v} for k, v in data.items()]


# ==================== Import Models Configuration ====================
# These models can be imported from CSV/Excel files
 
only_import_models = {
    'Country': {
        'model_class': Country,
        'resource_class': CountryResource, 
        'queryset': Country.objects.all(),
        'search_fields': ['code', 'name'],
        'ordering_fields': ['code', 'name'],
    },
    'State': {
        'model_class': State,
        'resource_class': StateResource,
        'queryset': State.objects.all(),
        'search_fields': ['code', 'name', 'gst_code'],
        'ordering_fields': ['code', 'name'],
    },
    'District': {
        'model_class': District,
        'resource_class': DistrictResource,
        'queryset': District.objects.filter(is_deleted=False),
        'search_fields': ['code', 'name'],
        'ordering_fields': ['code', 'name'],
    },
    'Mandal': {
        'model_class': Mandal,
        'resource_class': MandalResource,
        'queryset': Mandal.objects.filter(is_deleted=False),
        'search_fields': ['code', 'name'],
        'ordering_fields': ['code', 'name'],
    },
    'City': {
        'model_class': City,
        'resource_class': CityResource,
        'queryset': City.objects.all(),
        'search_fields': ['code', 'name'],
        'ordering_fields': ['code', 'name'],
    },
    'Area': {
        'model_class': Area,
        'resource_class': AreaResource,
        'queryset': Area.objects.all(),
        'search_fields': ['code', 'name'],
        'ordering_fields': ['code', 'name'],
    },
    'Location': {
        'model_class': Location,
        'resource_class': LocationResource,
        'queryset': Location.objects.all(),
        'search_fields': ['code', 'name'],
        'ordering_fields': ['code', 'name'],
    },
    'WareHouse': {
        'model_class': WareHouse,
        'resource_class': WareHouseResource,
        'queryset': WareHouse.objects.all(),
        'search_fields': ['code', 'name'],
        'ordering_fields': ['code', 'name'],
    },
    'Category': {
        'model_class': Category,
        'resource_class': CategoryResource,
        'queryset': Category.objects.all(),
        'search_fields': ['code', 'name'],
        'ordering_fields': ['code', 'name'],
    },
    'Brand': {
        'model_class': Brand,
        'resource_class': BrandResource,
        'queryset': Brand.objects.all(),
        'search_fields': ['code', 'name'],
        'ordering_fields': ['code', 'name'],
    },
    'Item': {
        'model_class': Item,
        'resource_class': ItemResource,
        'queryset': Item.objects.all(),
        'search_fields': ['code', 'name', 'sku', 'barcode'],
        'ordering_fields': ['code', 'name'],
    },
    'Superstockist': {
        'model_class': Superstockist,
        'resource_class': SuperstockistResource,
        'queryset': Superstockist.objects.all(),
        'search_fields': ['code', 'name', 'gstin', 'pan'],
        'ordering_fields': ['code', 'name'],
    },
    'SuperstockistLocation': {
        'model_class': SuperstockistLocation,
        'resource_class': SuperstockistLocationResource,
        'queryset': SuperstockistLocation.objects.all(),
        'search_fields': ['superstockist__code', 'superstockist__name', 'state__code', 'city__code', 'area__code'],
        'ordering_fields': ['superstockist__code', 'state__code'],
    },
    'Distributor': {
        'model_class': Distributor,
        'resource_class': DistributorResource,
        'queryset': Distributor.objects.all(),
        'search_fields': ['code', 'name', 'gstin', 'pan'],
        'ordering_fields': ['code', 'name'],
    },
    'DistributorLocation': {
        'model_class': DistributorLocation,
        'resource_class': DistributorLocationResource,
        'queryset': DistributorLocation.objects.all(),
        'search_fields': ['distributor__code', 'distributor__name', 'state__code', 'city__code', 'area__code'],
        'ordering_fields': ['distributor__code', 'state__code'],
    },
    'Retailer': {
        'model_class': Retailer,
        'resource_class': RetailerResource,
        'queryset': Retailer.objects.all(),
        'search_fields': ['code', 'name', 'gstin', 'pan'],
        'ordering_fields': ['code', 'name'],
    },
    'RetailerLocation': {
        'model_class': RetailerLocation,
        'resource_class': RetailerLocationResource,
        'queryset': RetailerLocation.objects.all(),
        'search_fields': ['retailer__code', 'retailer__name', 'state__code', 'city__code', 'area__code'],
        'ordering_fields': ['retailer__code', 'state__code'],
    },
    'PriceBook': {
        'model_class': PriceBook,
        'resource_class': PriceBookResource,
        'queryset': PriceBook.objects.all(),
        'search_fields': ['code', 'item__code', 'item__name'],
        'ordering_fields': ['code', 'effective_from'],
    },
    'Agent': {
        'model_class': Agent,
        'resource_class': AgentResource,
        'queryset': Agent.objects.filter(is_deleted=False, is_active=True),
        'search_fields': ['code', 'name'],
        'ordering_fields': ['code', 'name'],
    },
}

# ==================== Export Models Configuration ====================

only_export_models = {
    # 'User': {
    #     'model_class': User,
    #     'resource_class': UserResource,
    #     'filter_backends': [DjangoFilterBackend, SearchFilter, OrderingFilter],
    #     'queryset': User.objects.filter(is_active=True).order_by('-created_at'),
    #     'filterset_class': UserFilter,
    #     'search_fields': ['username', 'email', 'phone', 'first_name', 'last_name', 'pincode', 'groups__name'],
    #     'ordering_fields': ['username'],
    #     'permissions': [GetPermission('System.view_report')],
    # },
    # 'Device': {
    #     'model_class': Device,
    #     'resource_class': DeviceResource,
    #     'queryset': Device.objects.filter(is_active=False),
    # },
    'Country': {
        'model_class': Country,
        'resource_class': CountryResource,
        'queryset': Country.objects.filter(is_deleted=False),
        'filter_backends': [DjangoFilterBackend, SearchFilter, OrderingFilter],
        # 'filterset_class': CountryFilter,
        'search_fields': ['code', 'name'],
        'ordering_fields': ['code', 'name'],
        # 'permissions': [GetPermission('System.view_report')],
    },
    'State': {
        'model_class': State,
        'resource_class': StateResource,
        'queryset': State.objects.filter(is_deleted=False),
        'filter_backends': [DjangoFilterBackend, SearchFilter, OrderingFilter],
        'filterset_class': StateFilter,
        'search_fields': ['code', 'name', 'gst_code'],
        'ordering_fields': ['code', 'name'],
    },
    'District': {
        'model_class': District,
        'resource_class': DistrictResource,
        'queryset': District.objects.filter(is_deleted=False),
        'filter_backends': [DjangoFilterBackend, SearchFilter, OrderingFilter],
        'filterset_class': DistrictFilter,
        'search_fields': ['code', 'name'],
        'ordering_fields': ['code', 'name'],
    },
    'Mandal': {
        'model_class': Mandal,
        'resource_class': MandalResource,
        'queryset': Mandal.objects.filter(is_deleted=False),
        'filter_backends': [DjangoFilterBackend, SearchFilter, OrderingFilter],
        'filterset_class': MandalFilter,
        'search_fields': ['code', 'name'],
        'ordering_fields': ['code', 'name'],
    },
    'City': {
        'model_class': City,
        'resource_class': CityResource,
        'queryset': City.objects.filter(is_deleted=False),
        'filter_backends': [DjangoFilterBackend, SearchFilter, OrderingFilter],
        'filterset_class': CityFilter,
        'search_fields': ['code', 'name'],
        'ordering_fields': ['code', 'name'],
    },
    'Area': {
        'model_class': Area,
        'resource_class': AreaResource,
        'queryset': Area.objects.filter(is_deleted=False),
        'filter_backends': [DjangoFilterBackend, SearchFilter, OrderingFilter],
        'filterset_class': AreaFilter,
        'search_fields': ['code', 'name'],
        'ordering_fields': ['code', 'name'],
    },
    'Company': {
        'model_class': Company,
        'resource_class': CompanyResource,
        'queryset': Company.objects.filter(is_deleted=False),
        'filter_backends': [DjangoFilterBackend, SearchFilter, OrderingFilter],
        # 'filterset_class': CompanyFilter,
        'search_fields': ['code', 'name'],
        'ordering_fields': ['code', 'name'],
    },
    'Location': {
        'model_class': Location,
        'resource_class': LocationResource,
        'queryset': Location.objects.filter(is_deleted=False),
        'filter_backends': [DjangoFilterBackend, SearchFilter, OrderingFilter],
        'filterset_class': LocationFilter,
        'search_fields': ['code', 'name'],
        'ordering_fields': ['code', 'name'],
    },
    'WareHouse': {
        'model_class': WareHouse,
        'resource_class': WareHouseResource,
        'queryset': WareHouse.objects.filter(is_deleted=False),
        'filter_backends': [DjangoFilterBackend, SearchFilter, OrderingFilter],
        'filterset_class': WareHouseFilter,
        'search_fields': ['code', 'name'],
        'ordering_fields': ['code', 'name'],
    },
    'UOM': {
        'model_class': UOM,
        'resource_class': UOMResource,
        'queryset': UOM.objects.filter(is_deleted=False),
        'filter_backends': [DjangoFilterBackend, SearchFilter, OrderingFilter],
        # 'filterset_class': UOMFilter,
        'search_fields': ['code', 'name'],
        'ordering_fields': ['code', 'name'],
    },
    'Category': {
        'model_class': Category,
        'resource_class': CategoryResource,
        'queryset': Category.objects.filter(is_deleted=False),
        'filter_backends': [DjangoFilterBackend, SearchFilter, OrderingFilter],
        'filterset_class': CategoryFilter,
        'search_fields': ['code', 'name'],
        'ordering_fields': ['code', 'name'],
    },
    'Brand': {
        'model_class': Brand,
        'resource_class': BrandResource,
        'queryset': Brand.objects.filter(is_deleted=False),
        'filter_backends': [DjangoFilterBackend, SearchFilter, OrderingFilter],
        'filterset_class': BrandFilter,
        'search_fields': ['code', 'name'],
        'ordering_fields': ['code', 'name'],
    },
    'Tax': {
        'model_class': Tax,
        'resource_class': TaxResource,
        'queryset': Tax.objects.filter(is_deleted=False),
        'filter_backends': [DjangoFilterBackend, SearchFilter, OrderingFilter],
        'filterset_class': TaxFilter,
        'search_fields': ['code', 'name'],
        'ordering_fields': ['code', 'name'],
    },
    'Item': {
        'model_class': Item,
        'resource_class': ItemResource,
        'queryset': Item.objects.filter(is_deleted=False),
        'filter_backends': [DjangoFilterBackend, SearchFilter, OrderingFilter],
        'filterset_class': ItemFilter,
        'search_fields': ['code', 'name', 'sku', 'barcode'],
        'ordering_fields': ['code', 'name'],
    },
    'ItemTaxComposition': {
        'model_class': ItemTaxComposition,
        'resource_class': ItemTaxCompositionResource,
        'queryset': ItemTaxComposition.objects.filter(is_deleted=False),
        'filter_backends': [DjangoFilterBackend, SearchFilter, OrderingFilter],
        'filterset_class': ItemTaxCompositionFilter,
        'search_fields': ['code', 'name', 'gstin', 'pan'],
        'ordering_fields': ['code', 'name'],
    },
    'ItemTaxComposition': {
        'model_class': ItemTaxComposition,
        'resource_class': ItemTaxCompositionResource,
        'queryset': ItemTaxComposition.objects.filter(is_deleted=False),
        'filter_backends': [DjangoFilterBackend, SearchFilter, OrderingFilter],
        'filterset_class': ItemTaxCompositionFilter,
        'search_fields': ['code', 'name', 'gstin', 'pan'],
        'ordering_fields': ['code', 'name'],
    },
    'OutletType': {
        'model_class': OutletType,
        'resource_class': OutletTypeResource,
        'queryset': OutletType.objects.filter(is_deleted=False),
        'filter_backends': [DjangoFilterBackend, SearchFilter, OrderingFilter],
        # 'filterset_class': OutletTypeFilter,
        'search_fields': ['code', 'name',],
        'ordering_fields': ['code', 'name'],
    },
    # 'SuperstockistLocation': {
    #     'model_class': SuperstockistLocation,
    #     'resource_class': SuperstockistLocationResource,
    #     'queryset': SuperstockistLocation.objects.all(),
    #     'filter_backends': [DjangoFilterBackend, SearchFilter, OrderingFilter],
    #     # 'filterset_class': SuperstockistLocationFilter,
    #     'search_fields': ['superstockist__code', 'superstockist__name', 'state__code', 'city__code', 'area__code'],
    #     'ordering_fields': ['superstockist__code', 'state__code'],
    # },
    'Distributor': {
        'model_class': Distributor,
        'resource_class': DistributorResource,
        'queryset': Distributor.objects.filter(is_deleted=False),
        'filter_backends': [DjangoFilterBackend, SearchFilter, OrderingFilter],
        'filterset_class': DistributorFilter,
        'search_fields': ['code', 'name', 'gstin', 'pan'],
        'ordering_fields': ['code', 'name'],
    },
    # 'DistributorLocation': {
    #     'model_class': DistributorLocation,
    #     'resource_class': DistributorLocationResource,
    #     'queryset': DistributorLocation.objects.all(),
    #     'filter_backends': [DjangoFilterBackend, SearchFilter, OrderingFilter],
    #     # 'filterset_class': DistributorLocationFilter,
    #     'search_fields': ['distributor__code', 'distributor__name', 'state__code', 'city__code', 'area__code'],
    #     'ordering_fields': ['distributor__code', 'state__code'],
    # },
    'Retailer': {
        'model_class': Retailer,
        'resource_class': RetailerResource,
        'queryset': Retailer.objects.filter(is_deleted=False),
        'filter_backends': [DjangoFilterBackend, SearchFilter, OrderingFilter],
        'filterset_class': RetailerFilter,
        'search_fields': ['code', 'name', 'gstin', 'pan'],
        'ordering_fields': ['code', 'name'],
    },
    # 'RetailerLocation': {
    #     'model_class': RetailerLocation,
    #     'resource_class': RetailerLocationResource,
    #     'queryset': RetailerLocation.objects.all(),
    #     'filter_backends': [DjangoFilterBackend, SearchFilter, OrderingFilter],
    #     # 'filterset_class': RetailerLocationFilter,
    #     'search_fields': ['retailer__code', 'retailer__name', 'state__code', 'city__code', 'area__code'],
    #     'ordering_fields': ['retailer__code', 'state__code'],
    # },
    'Route': {
        'model_class': RouteCoverage,
        'resource_class': RouteResource,
        'queryset': RouteCoverage.objects.filter(route__is_deleted=False),
        'filter_backends': [DjangoFilterBackend, SearchFilter, OrderingFilter],
        'search_fields': ['route__code', 'route__name'],
        'ordering_fields': ['route__code'],
    },
    'PriceBook': {
        'model_class': PriceBook,
        'resource_class': PriceBookResource,
        'queryset': PriceBook.objects.filter(is_deleted=False),
        'filter_backends': [DjangoFilterBackend, SearchFilter, OrderingFilter],
        'filterset_class': PriceBookFilter,
        'search_fields': ['code', 'item__code', 'item__name'],
        'ordering_fields': ['code', 'effective_from'],
    },
      'ProofOfDelivery': {
        'model_class': ProofOfDelivery,
        'resource_class': ProofOfDeliveryResource,
        'queryset': ProofOfDelivery.objects.filter(is_deleted=False).select_related(
            'invoice', 'invoice__company',
            'sales_order', 'sales_order__retailer',
            'sales_order__distributor', 'sales_order__distributor__agent',
            'sales_order__superstockist',
        ),
        'filter_backends': [DjangoFilterBackend, SearchFilter, OrderingFilter],
        'filterset_class': ProofOfDeliveryReportFilter,
        'search_fields': ['pod_number', 'invoice__invoice_number', 'sales_order__order_number', 'receiver_name', 'delivered_by'],
        'ordering_fields': ['pod_date', 'delivered_date', 'invoice__invoice_number', 'pod_number', 'status', 'customer_type', 'created_on'],
        'request_filters': [lambda request, qs: apply_company_location_filter(qs, request.user, company_field='invoice__company', location_field='invoice__location')],
        'permissions': [GetPermission('Delivery.reports_proofofdelivery')],
 
    },
    'Receipt': {
        'model_class': Receipt,
        'resource_class': ReceiptResource,
        'queryset': Receipt.objects.filter(is_deleted=False).select_related(
            'company', 'location',
            'retailer', 'distributor', 'distributor__agent', 'superstockist',
        ),
        'filter_backends': [DjangoFilterBackend, SearchFilter, OrderingFilter],
        'filterset_class': ReceiptExportFilter,
        'search_fields': ['receipt_number', 'reference_number', 'bank_name', 'retailer__name', 'distributor__name', 'superstockist__name', 'company__name', 'location__name'],
        'ordering_fields': ['receipt_date', 'receipt_number', 'total_amount', 'payment_date', 'authorized_status'],
        'request_filters': [lambda request, qs: apply_company_location_filter(qs, request.user, company_field='company', location_field='location')],
        'permissions': [GetPermission('Receipts Management.reports_receipt'),],
    },
}

export_import_models = {
    'User': {
        'model_class': User,
        'resource_class': UserResource,
        'filter_backends': [DjangoFilterBackend, SearchFilter, OrderingFilter],
        'queryset': User.objects.filter(is_active=True).order_by('-created_at'),
        'filterset_class': UserFilter,
        'search_fields': ['username', 'email', 'phone', 'first_name', 'last_name', 'pincode', 'groups__name'],
        'ordering_fields': ['username'],
        'permissions': [GetPermission('System.view_report')],
    }
}


def get_export_models():
    """Get all models available for export."""
    merged = {**export_import_models, **only_export_models}
    return dict_to_list_of_dicts(merged)

def get_import_models():
    """Get all models available for import."""
    merged = {**export_import_models, **only_import_models}
    return dict_to_list_of_dicts(merged)


# Register models for import/export
register_report_models(
    only_exports=get_export_models(),
    only_imports=get_import_models()
)