
from .attachment_views import AttachmentListView, AttachmentUploadView, AttachmentDeleteView
from drf_spectacular.utils import extend_schema, OpenApiParameter
import django_filters
from General.models import GeneralSettings
from django.shortcuts import get_object_or_404
from django.http import Http404
from utils import apply_company_location_filter, apply_channel_partner_company_location_filter
from Masters.scheme_constraints import get_scheme_type_constraints
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework import status
from Masters.field_config_defaults import upsert_item_field_configurations
from Masters.models import (
    UOM, Country, State, District, Mandal, City, Area, Route, RouteCoverage, Company, Location, LocationContact, WareHouse,
    Category, Brand, Tax,
    Item, ItemUOMConversion, ItemFieldConfiguration, ItemTaxComposition,
    Superstockist, SuperstockistLocation, SuperstockistContact,
    Distributor, DistributorLocation, DistributorContact,
    Retailer, RetailerLocation, RetailerContact,
    ChannelPartnerConfiguration,
    PriceBook, PriceBookDocument, PriceBookHistory,
    Scheme, SchemeHistory, SchemeCondition, SchemeBenefit,
    Agent,
    Project,
)
from Masters.attachment_views import ChannelPartnerAttachmentMixin
from django_filters.filters import Filter
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from django_filters import CharFilter, BooleanFilter, DateFilter, DateTimeFilter
from rest_framework import filters
import uuid
from datetime import timedelta, date, datetime

from rest_framework.response import Response
from rest_framework import generics, permissions
from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from django.db.models import Q

from Masters.serializers import (
    AreaMiniSerializer, AreaSerializer, RouteMiniSerializer, RouteSerializer, BrandMiniSerializer, BrandSerializer,
    CategoryMiniSerializer, CategorySerializer, CityMiniSerializer, CitySerializer,
    CompanyMiniSerializer, CompanySerializer, CountryMiniSerializer, CountrySerializer,
    DistrictSerializer, MandalSerializer,
    LocationMiniSerializer, LocationSerializer, LocationContactSerializer, SuperstockistContactSerializer,
    DistributorContactSerializer, RetailerContactSerializer, StateMiniSerializer, StateSerializer,
    UOMMiniSerializer, UOMSerializer, WareHouseMiniSerializer, WareHouseSerializer,
    TaxMiniSerializer, TaxSerializer, ItemMiniSerializer, ItemListSerializer, ItemSerializer,
    ItemUOMConversionSerializer, ItemTaxCompositionSerializer, ItemTaxCompositionCreateSerializer,
    ItemFieldConfigurationSerializer,
    SuperstockistSerializer, SuperstockistMiniSerializer, SuperstockistLocationSerializer,
    DistributorSerializer, DistributorMiniSerializer, DistributorLocationSerializer,
    RetailerSerializer, RetailerMiniSerializer, RetailerLocationSerializer,
    ChannelPartnerConfigurationSerializer,
    OutletTypeMiniSerializer, OutletTypeSerializer,
    PriceBookSerializer, PriceBookMiniSerializer, PriceBookHistorySerializer,
    PriceBookDocumentSerializer, PriceBookDocumentDetailSerializer,
    SchemeSerializer, SchemeMiniSerializer, SchemeHistorySerializer,
    AgentSerializer, AgentMiniSerializer,
    ProjectSerializer, ProjectMiniSerializer,
)
# from thirdparty.FocusAPI import *
User = get_user_model()

def _auto_expire_schemes():
    """Mark active schemes as expired if effective_to < today."""
    today = timezone.now().date()
    Scheme.objects.filter(
        status='ACTIVE',
        is_deleted=False,
        effective_to__isnull=False,
        effective_to__lt=today,
    ).update(status='EXPIRED')


def _set_draft_authorization(instance):
    """Keep draft records in pending state."""
    instance.authorized_status = 1
    instance.current_authorized_status = 1
    instance.authorized_level = 0
    instance.current_authorized_level = 0
    instance.authorized_by_type = None
    instance.authorized_by_identifier = None
    instance.authorized_on = None
    instance.current_authorized_by_type = None
    instance.current_authorized_by_identifier = None
    instance.current_authorized_on = None
    instance.save(update_fields=[
        'authorized_status', 'current_authorized_status',
        'authorized_level', 'current_authorized_level',
        'authorized_by_type', 'authorized_by_identifier', 'authorized_on',
        'current_authorized_by_type', 'current_authorized_by_identifier', 'current_authorized_on',
    ])


def _deleted_suffix_value(instance, field_name):
    """Return a unique deleted marker value, respecting max_length when present."""
    current_value = getattr(instance, field_name, None)
    if current_value in (None, ""):
        return current_value

    suffix = f"_DEL_{uuid.uuid4().hex[:8]}"
    field = instance._meta.get_field(field_name)
    max_length = getattr(field, "max_length", None)
    base_value = str(current_value)

    if not max_length:
        return f"{base_value}{suffix}"

    allowed_base_length = max_length - len(suffix)
    if allowed_base_length < 1:
        return suffix[-max_length:]

    return f"{base_value[:allowed_base_length]}{suffix}"


class ListFilter(Filter):
    def filter(self, qs, value):
        if not value:
            return qs

        self.lookup_expr = 'in'
        values = value.split(',')
        return super(ListFilter, self).filter(qs, values)

# class StateMini(generics.ListAPIView):
#     permission_classes = [permissions.AllowAny]
#     serializer_class = StateMiniSerializer
#     model = serializer_class.Meta.model
#     queryset = model.objects.filter(is_deleted=False).only('id','name',).order_by('name')
#     filter_backends = [filters.SearchFilter, ]
#     search_fields = ['name','code', ]
#     ordering_fields = ['code',]


# class StateMiniList(generics.ListAPIView):
#     permission_classes = [permissions.AllowAny]
#     pagination_class = None
#     serializer_class = StateMiniSerializer
#     model = serializer_class.Meta.model
#     filter_backends = [filters.SearchFilter, ]
#     search_fields = ['name','code', ]
#     ordering_fields = ['code',]

#     def get_queryset(self):
#         return self.serializer_class.Meta.model.objects.filter(is_deleted=False).only('id', 'name').order_by('name')

#     def list(self, request, *args, **kwargs):
#         queryset = self.get_queryset()
#         search_query = self.request.query_params.get('search', None)
#         if search_query:
#             queryset = self.filter_queryset(queryset)
#         serializer = self.get_serializer(queryset, many=True)
#         return Response({'count': queryset.count(), 'results': serializer.data})


# class StateList(generics.ListCreateAPIView):
#     # permission_classes = [GetPermission('Masters.View')]
#     serializer_class = StateSerializer
#     model = serializer_class.Meta.model
#     queryset = model.objects.filter(is_deleted=False ).order_by('-id')
#     filter_backends = [filters.SearchFilter, ]
#     search_fields = ['name','code', ]
#     ordering_fields = ['code',]


#     def perform_create(self, serializer):
#         serializer.save()


# class StateDetail(generics.RetrieveUpdateDestroyAPIView):
#     serializer_class = StateSerializer
#     model = serializer_class.Meta.model
#     queryset = model.objects.all()

#     def perform_update(self, serializer):
#         serializer.save()

#     def perform_destroy(self, instance):
#         instance.is_deleted=True
#         instance.
#         instance.save()


# class LocationFilter(FilterSet):
#     class Meta:
#         model = Location
#         fields = ['state']

# class LocationList(generics.ListCreateAPIView):
#     permission_classes = [permissions.AllowAny]
#     serializer_class = LocationExampleSerializer
#     model = serializer_class.Meta.model
#     queryset = model.objects.filter(is_deleted=False ).order_by('-id')
#     filter_backends = [filters.SearchFilter,DjangoFilterBackend,]
#     # filterset_class = LocationFilter
#     search_fields = ['name','code',]
#     ordering_fields = ['code',]

#     def get_queryset(self):

#         user = self.request.user
#         model_path = f"{State._meta.app_label}.{State._meta.model_name}"
#         print('usertrrr',user)
#         locations = Location.objects.filter(get_permitted_class(user, model_path, 'state_id', screen_type = 'view'))
#         print('locations', locations)
#         return locations


class UOMMini(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UOMMiniSerializer
    pagination_class = None
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_deleted=False).only('id', 'name').order_by('-created_on')
    ordering_fields = ['code', 'created_on']


class UOMList(generics.ListCreateAPIView):
    serializer_class = UOMSerializer
    model = serializer_class.Meta.model
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    queryset = model.objects.filter(is_deleted=False).order_by('-created_on')
    search_fields = ['code', 'name']
    ordering_fields = ['code', 'created_on']

    def perform_create(self, serializer):
        serializer.save()


class UOMDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UOMSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_deleted=False)

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        if Item.objects.filter(base_uom=instance, is_deleted=False).exists():
            raise DRFValidationError({'detail': f'Cannot delete UOM "{instance.name}" because it is used by items.'})
        instance.name = _deleted_suffix_value(instance, "name")
        instance.code = _deleted_suffix_value(instance, "code")
        instance.is_deleted = True
        instance.save()


class CategoryFilter(FilterSet):
    class Meta:
        model = Category
        fields = ['is_active', 'parent']


class CategoryMini(generics.ListAPIView):
    queryset = Category.objects.filter(is_deleted=False, is_active=True).order_by('name')
    serializer_class = CategoryMiniSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None


class CategoryList(generics.ListCreateAPIView):
    queryset = Category.objects.filter(is_deleted=False)
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CategoryFilter
    search_fields = ['code', 'name']
    ordering_fields = ['created_on', 'code', 'name']
    ordering = ['-created_on']


class CategoryDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.filter(is_deleted=False)
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_destroy(self, instance):
        if Item.objects.filter(category=instance, is_deleted=False).exists():
            raise DRFValidationError({'detail': f'Cannot delete category "{instance.name}" because it has associated items.'})
        instance.name = _deleted_suffix_value(instance, "name")
        instance.code = _deleted_suffix_value(instance, "code")
        instance.is_deleted = True
        instance.save()


class BrandFilter(FilterSet):
    class Meta:
        model = Brand
        fields = ['is_active']


class BrandMini(generics.ListAPIView):
    queryset = Brand.objects.filter(is_deleted=False, is_active=True).order_by('name')
    serializer_class = BrandMiniSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None


class BrandList(generics.ListCreateAPIView):
    queryset = Brand.objects.filter(is_deleted=False)
    serializer_class = BrandSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = BrandFilter
    search_fields = ['code', 'name']
    ordering_fields = ['code', 'name', 'created_on']
    ordering = ['-created_on']


class BrandDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Brand.objects.filter(is_deleted=False)
    serializer_class = BrandSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_destroy(self, instance):
        if Item.objects.filter(brand=instance, is_deleted=False).exists():
            raise DRFValidationError({'detail': f'Cannot delete brand "{instance.name}" because it has associated items.'})
        instance.name = _deleted_suffix_value(instance, "name")
        instance.code = _deleted_suffix_value(instance, "code")
        instance.is_deleted = True
        instance.save()


class StateFilter(FilterSet):
    class Meta:
        model = State
        fields = ['country']


class CityFilter(FilterSet):
    state = CharFilter(method='filter_state')
    district = CharFilter(method='filter_district')
    mandal = CharFilter(method='filter_mandal')
    country = CharFilter(method='filter_country')

    def filter_state(self, queryset, name, value):
        if ',' in value:
            # Handle comma-separated values
            state_ids = [s.strip() for s in value.split(',')]
            return queryset.filter(state__id__in=state_ids)
        return queryset.filter(state__id=value)

    def filter_district(self, queryset, name, value):
        if ',' in value:
            # Handle comma-separated values
            district_ids = [d.strip() for d in value.split(',')]
            return queryset.filter(district__id__in=district_ids)
        return queryset.filter(district__id=value)

    def filter_mandal(self, queryset, name, value):
        if ',' in value:
            # Handle comma-separated values
            mandal_ids = [m.strip() for m in value.split(',')]
            return queryset.filter(mandal__id__in=mandal_ids)
        return queryset.filter(mandal__id=value)

    def filter_country(self, queryset, name, value):
        if ',' in value:
            # Handle comma-separated values
            country_ids = [c.strip() for c in value.split(',')]
            return queryset.filter(country__id__in=country_ids)
        return queryset.filter(country__id=value)

    class Meta:
        model = City
        fields = ['state', 'district', 'mandal', 'country']


class AreaFilter(FilterSet):
    city = CharFilter(method='filter_city')

    def filter_city(self, queryset, name, value):
        if ',' in value:
            # Handle comma-separated values
            city_ids = [c.strip() for c in value.split(',')]
            return queryset.filter(city__id__in=city_ids)
        return queryset.filter(city__id=value)

    class Meta:
        model = Area
        fields = ['state', 'city']


class RouteFilter(FilterSet):
    state = django_filters.UUIDFilter(field_name='coverages__state__id')
    city = django_filters.UUIDFilter(field_name='coverages__city__id')
    area = django_filters.UUIDFilter(field_name='coverages__area__id')

    class Meta:
        model = Route
        fields = ['is_active', 'state', 'city', 'area']


class CompanyFilter(FilterSet):
    class Meta:
        model = Company
        fields = ['state', 'city']


class LocationFilter(FilterSet):
    company = CharFilter(method='filter_company')

    def filter_company(self, queryset, name, value):
        if not value:
            return queryset
        if ',' in value:
            company_ids = [c.strip() for c in value.split(',') if c.strip()]
            return queryset.filter(companies__id__in=company_ids).distinct()
        return queryset.filter(companies__id=value).distinct()

    class Meta:
        model = Location
        fields = ['company', 'state', 'country', 'city']


class StateMiniList(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = StateMiniSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_class = StateFilter
    search_fields = ['name', 'code', 'country__name']
    ordering_fields = ['name', 'code']
    pagination_class = None

    def get_queryset(self):
        return State.objects.filter(is_deleted=False).only('id', 'name', 'code').order_by('name')


class CountryMiniList(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CountryMiniSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'code']
    pagination_class = None

    def get_queryset(self):
        return Country.objects.filter(is_deleted=False).only('id', 'name', 'code').order_by('name')


class CityMiniList(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CityMiniSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_class = CityFilter
    search_fields = ['name', 'code', 'state__name', 'country__name']
    ordering_fields = ['name', 'code']
    pagination_class = None

    def get_queryset(self):
        return City.objects.filter(is_deleted=False).only('id', 'name').order_by('name')


class LocationMiniList(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = LocationMiniSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_class = LocationFilter
    search_fields = ['name', 'code', 'state__name', 'country__name', 'city__name']
    ordering_fields = ['name', 'code']
    pagination_class = None

    def get_queryset(self):
        return Location.objects.filter(is_deleted=False).only('id', 'name').order_by('name')


class WareHouseMiniList(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = WareHouseMiniSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'code']
    pagination_class = None

    def get_queryset(self):
        return WareHouse.objects.filter(is_deleted=False).only('id', 'name').order_by('name')

# Country Views


class CountryList(generics.ListCreateAPIView):
    serializer_class = CountrySerializer
    queryset = Country.objects.filter(is_deleted=False).order_by('-created_on')
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code', 'name']
    ordering_fields = ['name', 'code', 'created_on']


class CountryDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CountrySerializer
    queryset = Country.objects.filter(is_deleted=False)

    def perform_destroy(self, instance):
        # Check if any states are linked to this country
        if State.objects.filter(country=instance, is_deleted=False).exists():
            raise DRFValidationError({
                'detail': (
                    f'Cannot delete country "{instance.name}" because it has associated states. '
                    'Please delete or reassign the states first.'
                )
            })
        # Append UUID to code and name so they can be reused
        instance.code = _deleted_suffix_value(instance, "code")
        instance.name = _deleted_suffix_value(instance, "name")
        instance.is_deleted = True
        instance.save()

# State Views


class StateList(generics.ListCreateAPIView):
    serializer_class = StateSerializer
    queryset = State.objects.filter(is_deleted=False).order_by('-created_on')
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_class = StateFilter
    search_fields = ['code', 'name', 'country__name', 'gst_code']
    ordering_fields = ['name', 'code', 'created_on']


class StateDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = StateSerializer
    queryset = State.objects.filter(is_deleted=False)

    def perform_destroy(self, instance):
        linked = []
        if City.objects.filter(state=instance, is_deleted=False).exists():
            linked.append('cities')
        if Area.objects.filter(state=instance, is_deleted=False).exists():
            linked.append('areas')
        if District.objects.filter(state=instance, is_deleted=False).exists():
            linked.append('districts')
        if linked:
            raise DRFValidationError({
                'detail': (
                    f'Cannot delete state "{instance.name}" because it has associated {", ".join(linked)}. '
                    'Please delete or reassign them first.'
                )
            })
        instance.code = _deleted_suffix_value(instance, "code")
        instance.name = _deleted_suffix_value(instance, "name")
        instance.is_deleted = True
        instance.save()


# District Views
class DistrictFilter(FilterSet):
    state = CharFilter(method='filter_state')

    def filter_state(self, queryset, name, value):
        if ',' in value:
            state_ids = [s.strip() for s in value.split(',')]
            return queryset.filter(state__id__in=state_ids)
        return queryset.filter(state__id=value)

    class Meta:
        model = District
        fields = ['state']


class DistrictMiniList(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = DistrictSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_class = DistrictFilter
    search_fields = ['name', 'code', 'state__name']
    ordering_fields = ['name', 'code']
    pagination_class = None

    def get_queryset(self):
        return District.objects.filter(is_deleted=False).only('id', 'name', 'code').order_by('name')


class DistrictList(generics.ListCreateAPIView):
    serializer_class = DistrictSerializer
    queryset = District.objects.filter(is_deleted=False).order_by('-created_on')
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_class = DistrictFilter
    search_fields = ['code', 'name', 'state__name']
    ordering_fields = ['name', 'code', 'created_on']


class DistrictDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DistrictSerializer
    queryset = District.objects.filter(is_deleted=False)

    def perform_destroy(self, instance):
        linked = []
        if Mandal.objects.filter(district=instance, is_deleted=False).exists():
            linked.append('mandals')
        if City.objects.filter(district=instance, is_deleted=False).exists():
            linked.append('cities')
        if linked:
            raise DRFValidationError({
                'detail': (
                    f'Cannot delete district "{instance.name}" because it has associated {", ".join(linked)}. '
                    'Please delete or reassign them first.'
                )
            })
        if instance.code:
            instance.code = _deleted_suffix_value(instance, "code")
        instance.name = _deleted_suffix_value(instance, "name")
        instance.is_deleted = True
        instance.save()


# Mandal Views
class MandalFilter(FilterSet):
    state = CharFilter(method='filter_state')
    district = CharFilter(method='filter_district')

    def filter_state(self, queryset, name, value):
        if ',' in value:
            state_ids = [s.strip() for s in value.split(',')]
            return queryset.filter(state__id__in=state_ids)
        return queryset.filter(state__id=value)

    def filter_district(self, queryset, name, value):
        if ',' in value:
            district_ids = [d.strip() for d in value.split(',')]
            return queryset.filter(district__id__in=district_ids)
        return queryset.filter(district__id=value)

    class Meta:
        model = Mandal
        fields = ['state', 'district']


class MandalMiniList(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = MandalSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_class = MandalFilter
    search_fields = ['name', 'code', 'district__name', 'state__name']
    ordering_fields = ['name', 'code']
    pagination_class = None

    def get_queryset(self):
        return Mandal.objects.filter(is_deleted=False).only('id', 'name', 'code').order_by('name')


class MandalList(generics.ListCreateAPIView):
    serializer_class = MandalSerializer
    queryset = Mandal.objects.filter(is_deleted=False).order_by('-created_on')
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_class = MandalFilter
    search_fields = ['code', 'name', 'district__name', 'state__name']
    ordering_fields = ['name', 'code', 'created_on']


class MandalDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MandalSerializer
    queryset = Mandal.objects.filter(is_deleted=False)

    def perform_destroy(self, instance):
        linked = []
        if City.objects.filter(mandal=instance, is_deleted=False).exists():
            linked.append('cities')
        if Area.objects.filter(mandal=instance, is_deleted=False).exists():
            linked.append('areas')
        if linked:
            raise DRFValidationError({
                'detail': (
                    f'Cannot delete mandal "{instance.name}" because it has associated {", ".join(linked)}. '
                    'Please delete or reassign them first.'
                )
            })
        if instance.code:
            instance.code = _deleted_suffix_value(instance, "code")
        instance.name = _deleted_suffix_value(instance, "name")
        instance.is_deleted = True
        instance.save()

# City Views


class CityList(generics.ListCreateAPIView):
    serializer_class = CitySerializer
    queryset = City.objects.filter(is_deleted=False).order_by('-created_on')
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_class = CityFilter
    search_fields = ['code', 'name', 'state__name', 'country__name']
    ordering_fields = ['name', 'code', 'created_on']


class CityDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CitySerializer
    queryset = City.objects.filter(is_deleted=False)

    def perform_destroy(self, instance):
        # Check if any locations or areas are linked to this city
        if Location.objects.filter(city=instance, is_deleted=False).exists():
            raise DRFValidationError({
                'detail': (
                    f'Cannot delete city "{instance.name}" because it has associated locations. '
                    'Please delete or reassign the locations first.'
                )
            })
        if Area.objects.filter(city=instance, is_deleted=False).exists():
            raise DRFValidationError({
                'detail': (
                    f'Cannot delete city "{instance.name}" because it has associated areas. '
                    'Please delete or reassign the areas first.'
                )
            })
        # Append UUID to code and name so they can be reused
        if instance.code:
            instance.code = _deleted_suffix_value(instance, "code")
        instance.name = _deleted_suffix_value(instance, "name")
        instance.is_deleted = True
        instance.save()

# Area Views


class AreaList(generics.ListCreateAPIView):
    serializer_class = AreaSerializer
    queryset = Area.objects.filter(is_deleted=False).order_by('-created_on')
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_class = AreaFilter
    search_fields = ['name', 'code', 'city__name', 'state__name']
    ordering_fields = ['created_on','name']


class AreaMiniList(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = AreaMiniSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_class = AreaFilter
    search_fields = ['name']
    ordering_fields = ['name']
    pagination_class = None

    def get_queryset(self):
        return Area.objects.filter(is_deleted=False).only('id', 'name').order_by('-created_on')


class AreaDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AreaSerializer
    queryset = Area.objects.filter(is_deleted=False)

    def perform_destroy(self, instance):
        linked = []
        if RouteCoverage.objects.filter(area=instance).exists():
            linked.append('routes')
        if Superstockist.objects.filter(area=instance, is_deleted=False).exists():
            linked.append('superstockists')
        if Distributor.objects.filter(area=instance, is_deleted=False).exists():
            linked.append('distributors')
        if Retailer.objects.filter(area=instance, is_deleted=False).exists():
            linked.append('retailers')
        if linked:
            raise DRFValidationError({
                'detail': (
                    f'Cannot delete area "{instance.name}" because it has associated {", ".join(linked)}. '
                    'Please delete or reassign them first.'
                )
            })
        if instance.code:
            instance.code = _deleted_suffix_value(instance, "code")
        instance.name = _deleted_suffix_value(instance, "name")
        instance.is_deleted = True
        instance.save()










class RouteList(generics.ListCreateAPIView):
    serializer_class = RouteSerializer
    queryset = Route.objects.filter(is_deleted=False).order_by('-created_on')
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_class = RouteFilter
    search_fields = ['name', 'code', 'coverages__state__name', 'coverages__city__name', 'coverages__area__name']
    ordering_fields = ['name', 'code', 'created_on']

    def get_queryset(self):
        return Route.objects.filter(is_deleted=False).distinct().order_by('-created_on')


class RouteMiniList(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RouteMiniSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_class = RouteFilter
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'code']
    pagination_class = None

    def get_queryset(self):
        queryset = Route.objects.filter(is_deleted=False)
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            normalized = is_active.lower()
            if normalized in ('true', '1', 'yes'):
                queryset = queryset.filter(is_active=True)
            elif normalized in ('false', '0', 'no'):
                queryset = queryset.filter(is_active=False)
        return queryset.only('id', 'name').order_by('name')


class RouteDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RouteSerializer
    queryset = Route.objects.filter(is_deleted=False)

    def perform_destroy(self, instance):
        instance.code = _deleted_suffix_value(instance, "code")
        instance.name = _deleted_suffix_value(instance, "name")
        instance.is_deleted = True
        instance.save()


# Channel Partner Configuration Views
class ChannelPartnerConfigurationView(generics.GenericAPIView):
    """
    GET: Retrieve active channel partner configuration
    PATCH: Update active configuration
    """
    serializer_class = ChannelPartnerConfigurationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Get active configuration (do not auto-create)"""
        config = ChannelPartnerConfiguration.objects.filter(
            is_active=True,
            is_deleted=False
        ).first()

        # If no config exists, check for any non-deleted config
        if not config:
            config = ChannelPartnerConfiguration.objects.filter(
                is_deleted=False
            ).first()

        # Only create if absolutely no configuration exists and this is a PATCH request
        # For GET requests, return None to indicate no configuration
        if not config and self.request.method == 'PATCH':
            config = ChannelPartnerConfiguration.objects.create(
                name='Default Configuration',
                is_active=True
            )

        return config

    def get(self, request):
        """Retrieve active configuration"""
        config = self.get_object()
        if not config:
            # Return default values if no configuration exists yet
            return Response({
                'enable_superstockist': False,
                'enable_distributor': False,
                'enable_retailer': False,
                'enforce_channel_hierarchy': False,
                'is_active': True,
                'name': 'Default Configuration'
            })
        serializer = self.get_serializer(config)
        return Response(serializer.data)

    def patch(self, request):
        """Update active configuration"""
        config = self.get_object()
        serializer = self.get_serializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# Company Views
class CompanyList(generics.ListCreateAPIView):
    serializer_class = CompanySerializer
    queryset = Company.objects.filter(is_deleted=False).order_by('-created_on')
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_class = CompanyFilter
    search_fields = ['code', 'name', 'email', 'phone', 'gst_number', 'pan_number', 'state__name', 'city__name']
    ordering_fields = ['created_on', 'name', 'code']


class CompanyMiniList(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CompanyMiniSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_class = CompanyFilter
    search_fields = ['name']
    ordering_fields = ['name']
    pagination_class = None

    def get_queryset(self):
        return Company.objects.filter(is_deleted=False).only('id', 'name').order_by('-created_on')


class CompanyDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CompanySerializer
    queryset = Company.objects.filter(is_deleted=False)

    def perform_destroy(self, instance):
        # Append UUID to code and name so they can be reused
        # Clear unique identifiers to allow reuse after soft delete
        instance.name = _deleted_suffix_value(instance, "name")
        instance.code = _deleted_suffix_value(instance, "code")
        instance.pan_number = None
        instance.gst_number = None
        instance.is_deleted = True
        instance.save()


# Location Views
class LocationList(generics.ListCreateAPIView):
    serializer_class = LocationSerializer
    queryset = Location.objects.filter(is_deleted=False).order_by('-created_on').distinct()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_class = LocationFilter
    search_fields = ['code', 'name', 'companies__name', 'state__name', 'city__name']
    ordering_fields = ['name', 'code', 'created_on']


class LocationDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LocationSerializer
    queryset = Location.objects.filter(is_deleted=False)

    def perform_destroy(self, instance):
        # Check if any warehouses are linked to this location
        if WareHouse.objects.filter(location=instance, is_deleted=False).exists():
            raise DRFValidationError({
                'detail': (
                    f'Cannot delete location "{instance.name}" because it has associated warehouses. '
                    'Please delete or reassign the warehouses first.'
                )
            })
        # Append UUID to code and name so they can be reused
        instance.name = _deleted_suffix_value(instance, "name")
        instance.code = _deleted_suffix_value(instance, "code")
        instance.is_deleted = True
        instance.save()


class LocationContactList(generics.ListCreateAPIView):
    serializer_class = LocationContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        location_id = self.kwargs.get('location_id')
        return LocationContact.objects.filter(
            location_id=location_id, is_deleted=False).order_by(
            '-is_primary', 'contact_person')

    def perform_create(self, serializer):
        location_id = self.kwargs.get('location_id')
        location = get_object_or_404(Location, id=location_id, is_deleted=False)
        serializer.save(location=location)


class LocationContactDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LocationContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        location_id = self.kwargs.get('location_id')
        return LocationContact.objects.filter(location_id=location_id, is_deleted=False)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()

# WareHouse Views


class WareHouseFilter(FilterSet):
    location = django_filters.ModelChoiceFilter(queryset=Location.objects.all())

    class Meta:
        model = WareHouse
        fields = ['location']


class WareHouseList(generics.ListCreateAPIView):
    serializer_class = WareHouseSerializer
    queryset = WareHouse.objects.filter(is_deleted=False).order_by('-created_on')
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_class = WareHouseFilter
    search_fields = ['code', 'name', 'erp_code', 'erp_id', 'location__name', 'location__code']
    ordering_fields = ['created_on', 'name', 'code']


class WareHouseDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = WareHouseSerializer
    queryset = WareHouse.objects.filter(is_deleted=False)

    def perform_destroy(self, instance):
        # Append UUID to code and name so they can be reused
        instance.name = _deleted_suffix_value(instance, "name")
        instance.code = _deleted_suffix_value(instance, "code")
        instance.is_deleted = True
        instance.save()


class ExampleGETAPI(GenericAPIView):
    serializer_class = UOMSerializer
    queryset = UOM.objects.filter(is_deleted=False)

    @extend_schema(
        summary="List UOMs with filters",
        parameters=[
            OpenApiParameter(
                name='ordering',
                description='Which field to use when ordering the results.',
                required=False,
                type=str,
                location=OpenApiParameter.QUERY),
            OpenApiParameter(
                name='page',
                description='A page number within the paginated result set.',
                required=False,
                type=int,
                location=OpenApiParameter.QUERY),
            OpenApiParameter(
                name='page_size',
                description='Number of results to return per page.',
                required=False,
                type=int,
                location=OpenApiParameter.QUERY),
            OpenApiParameter(
                name='search',
                description='A search term.',
                required=False,
                type=str,
                location=OpenApiParameter.QUERY),
        ],
        responses={
            200: UOMSerializer(
                many=True)})
    def get(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Tax Views
class TaxFilter(FilterSet):
    class Meta:
        model = Tax
        fields = ['is_active', 'tax_type']


class TaxMini(generics.ListAPIView):
    queryset = Tax.objects.filter(is_deleted=False, is_active=True).order_by('name')
    serializer_class = TaxMiniSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code']


class TaxList(generics.ListCreateAPIView):
    queryset = Tax.objects.filter(is_deleted=False)
    serializer_class = TaxSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TaxFilter
    search_fields = ['code', 'name', 'tax_type']
    ordering_fields = ['code', 'name', 'tax_rate', 'created_on']
    ordering = ['-created_on']


class TaxDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Tax.objects.filter(is_deleted=False)
    serializer_class = TaxSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_destroy(self, instance):
        if ItemTaxComposition.objects.filter(tax=instance, is_deleted=False).exists():
            raise DRFValidationError({'detail': f'Cannot delete tax "{instance.name}" because it is used by item tax compositions.'})
        instance.name = _deleted_suffix_value(instance, "name")
        instance.code = _deleted_suffix_value(instance, "code")
        instance.is_deleted = True
        instance.save()


# ItemTaxComposition Views
class ItemTaxCompositionFilter(FilterSet):
    item = CharFilter(field_name='item__id', lookup_expr='exact')
    composition_type = CharFilter(field_name='composition_type', lookup_expr='exact')
    effective_date = DateFilter(method='filter_by_effective_date')

    class Meta:
        model = ItemTaxComposition
        fields = ['item', 'composition_type', 'effective_date']

    def filter_by_effective_date(self, queryset, name, value):
        """Filter by effective date range"""
        return queryset.filter(
            effective_from__lte=value
        ).filter(
            Q(effective_to__gte=value) | Q(effective_to__isnull=True)
        )


class ItemTaxCompositionList(generics.ListCreateAPIView):
    """List and create Item Tax Compositions"""
    queryset = ItemTaxComposition.objects.all().select_related('item', 'tax')
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ItemTaxCompositionFilter
    search_fields = ['item__name', 'item__code', 'tax__name']
    ordering_fields = ['item__name', 'composition_type', 'effective_from', 'created_on']
    ordering = ['-created_on']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ItemTaxCompositionCreateSerializer
        return ItemTaxCompositionSerializer


class ItemTaxCompositionDetail(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete an Item Tax Composition"""
    queryset = ItemTaxComposition.objects.all().select_related('item', 'tax')
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ItemTaxCompositionCreateSerializer
        return ItemTaxCompositionSerializer


class ItemCurrentTaxComposition(generics.ListAPIView):
    """Get current tax composition for an item (PRIMARY + CESS)"""
    serializer_class = ItemTaxCompositionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        item_id = self.kwargs.get('item_id')
        today = date.today()

        # Get all current tax compositions
        return ItemTaxComposition.objects.filter(
            item_id=item_id,
            effective_from__lte=today
        ).filter(
            Q(effective_to__gte=today) | Q(effective_to__isnull=True)
        ).select_related('item', 'tax').order_by('composition_type', 'tax__name')


# OutletType Views
class OutletTypeMini(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OutletTypeMiniSerializer
    pagination_class = None
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_deleted=False).only('id', 'name').order_by('name')
    ordering_fields = ['code', 'created_on']


class OutletTypeList(generics.ListCreateAPIView):
    serializer_class = OutletTypeSerializer
    model = serializer_class.Meta.model
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    queryset = model.objects.filter(is_deleted=False).order_by('-created_on')
    search_fields = ['code', 'name']
    ordering_fields = ['code', 'created_on']

    def perform_create(self, serializer):
        serializer.save()


class OutletTypeDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OutletTypeSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_deleted=False)

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        if Retailer.objects.filter(outlet_type=instance, is_deleted=False).exists():
            raise DRFValidationError({'detail': f'Cannot delete outlet type "{instance.name}" because it is used by retailers.'})
        instance.name = _deleted_suffix_value(instance, "name")
        instance.code = _deleted_suffix_value(instance, "code")
        instance.is_deleted = True
        instance.save()


# Agent/Broker Views
class AgentFilter(FilterSet):
    class Meta:
        model = Agent
        fields = ['is_active']


class AgentMini(generics.ListAPIView):
    queryset = Agent.objects.filter(is_deleted=False, is_active=True).order_by('name')
    serializer_class = AgentMiniSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    filter_backends = [filters.SearchFilter]
    search_fields = ['code', 'name']


class AgentList(generics.ListCreateAPIView):
    serializer_class = AgentSerializer
    queryset = Agent.objects.filter(is_deleted=False).order_by('-created_on')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AgentFilter
    search_fields = ['code', 'name', 'phone', 'email']
    ordering_fields = ['code', 'name', 'created_on']
    ordering = ['-created_on']


class AgentDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AgentSerializer
    queryset = Agent.objects.filter(is_deleted=False)

    def perform_destroy(self, instance):
        if Distributor.objects.filter(agent=instance, is_deleted=False).exists():
            raise DRFValidationError({'detail': f'Cannot delete agent "{instance.name}" because it is tagged to distributors.'})
        instance.name = _deleted_suffix_value(instance, "name")
        instance.code = _deleted_suffix_value(instance, "code")
        instance.is_deleted = True
        instance.save()


# Item Views
class ItemFilter(FilterSet):
    # Support multiple category and brand filtering (comma-separated IDs)
    category = CharFilter(field_name='category__id', method='filter_category_multiple')
    brand = CharFilter(field_name='brand__id', method='filter_brand_multiple')
    
    def filter_category_multiple(self, queryset, name, value):
        """Filter by multiple category IDs (comma-separated)"""
        if not value:
            return queryset
        category_ids = [id.strip() for id in value.split(',') if id.strip()]
        if category_ids:
            return queryset.filter(category__id__in=category_ids)
        return queryset
    
    def filter_brand_multiple(self, queryset, name, value):
        """Filter by multiple brand IDs (comma-separated)"""
        if not value:
            return queryset
        brand_ids = [id.strip() for id in value.split(',') if id.strip()]
        if brand_ids:
            return queryset.filter(brand__id__in=brand_ids)
        return queryset
    
    class Meta:
        model = Item
        fields = [
            'is_active',
            'item_type',
            'product_type',
            'category',
            'brand',
            'is_saleable',
            'is_purchasable',
            'is_featured']


class ItemMini(generics.ListAPIView):
    serializer_class = ItemMiniSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = ItemFilter
    search_fields = ['code', 'name', 'barcode']

    def get_queryset(self):
        queryset = Item.objects.filter(is_deleted=False, is_active=True).order_by('name')

        if GeneralSettings.is_company_scoped_item_enforcement_enabled():
            company_id = self.request.query_params.get('company') or self.request.query_params.get('company_id')
            if company_id:
                queryset = queryset.filter(company_id=company_id)
            else:
                # Restrict new selection until company is chosen in header.
                queryset = queryset.none()

        return queryset


class ItemList(generics.ListCreateAPIView):
    queryset = Item.objects.filter(is_deleted=False)
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ItemFilter
    search_fields = ['code', 'name', 'barcode', 'sku', 'hsn_code', 'manufacturer', 'category__name', 'brand__name']
    ordering_fields = ['code', 'name', 'created_on', 'selling_price']
    ordering = ['-created_on']

    def get_serializer_class(self):
        # Use optimized serializer for list, full serializer for create
        if self.request.method == 'GET':
            return ItemListSerializer
        return ItemSerializer


class ItemDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Item.objects.filter(is_deleted=False)
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_destroy(self, instance):
        from Sales.models import SalesOrderItem
        linked = []
        if PriceBook.objects.filter(item=instance, is_deleted=False).exists():
            linked.append('price books')
        if SalesOrderItem.objects.filter(item=instance, is_deleted=False).exists():
            linked.append('sales orders')
        if linked:
            raise DRFValidationError({'detail': f'Cannot delete item "{instance.name}" because it has associated {", ".join(linked)}.'})
        instance.name = _deleted_suffix_value(instance, "name")
        instance.code = _deleted_suffix_value(instance, "code")
        instance.barcode = None
        instance.is_deleted = True
        instance.save()


class ItemBarcodeSearch(APIView):
    """
    Search for an item by barcode

    GET /api/masters/items/barcode-search/?barcode=<barcode>&company_id=<company_id>

    Returns item details with UOM conversions if found
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        barcode = request.query_params.get('barcode')
        company_id = request.query_params.get('company_id')
        enforce_company_scope = GeneralSettings.is_company_scoped_item_enforcement_enabled()

        if not barcode:
            return Response(
                {'error': 'barcode parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if enforce_company_scope and not company_id:
            return Response(
                {'error': 'company_id parameter is required when company scoping is enabled'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # First, try to find item by main barcode
        item_query = Item.objects.filter(
            barcode=barcode,
            is_deleted=False,
            is_active=True,
            is_saleable=True
        )

        # Apply company filter if company_id is provided
        if company_id:
            item_query = item_query.filter(company_id=company_id)

        item = item_query.first()

        # If not found by main barcode, try UOM conversion barcodes
        if not item:
            uom_conversion_query = ItemUOMConversion.objects.filter(
                barcode=barcode,
                is_deleted=False,
                item__is_deleted=False,
                item__is_active=True,
                item__is_saleable=True
            ).select_related('item')

            # Apply company filter if company_id is provided
            if company_id:
                uom_conversion_query = uom_conversion_query.filter(item__company_id=company_id)

            # Check for multiple matches to avoid ambiguity
            uom_conversion_count = uom_conversion_query.count()
            
            if uom_conversion_count > 1:
                # Multiple items share the same UOM barcode - this is a data integrity issue
                matching_items = list(uom_conversion_query.values_list('item__code', 'item__name'))
                item_details = [f"{code} ({name})" for code, name in matching_items]
                raise DRFValidationError({
                    'error': 'Ambiguous barcode',
                    'detail': f'Barcode "{barcode}" matches multiple items: {", ".join(item_details)}. Please contact administrator to resolve duplicate barcodes.'
                })
                
            uom_conversion = uom_conversion_query.first()

            if uom_conversion:
                item = uom_conversion.item
                # Return item with specific UOM info
                serializer = ItemSerializer(item)
                data = serializer.data
                data['matched_uom'] = {
                    'id': str(uom_conversion.alternate_uom.id),
                    'name': uom_conversion.alternate_uom.name,
                    'factor': float(uom_conversion.conversion_factor)
                }
                return Response(data)

        if not item:
            return Response(
                {'error': 'No item found with this barcode'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Return item details
        serializer = ItemSerializer(item)
        return Response(serializer.data)



# Item Tax Composition Views (replacing old ItemTaxMapping views)
# The ItemTaxMapping views have been replaced with ItemTaxComposition views above


# Bulk Tax Update View (updated to use ItemTaxComposition)
class BulkTaxUpdateView(APIView):
    """
    Update tax for multiple items at once using ItemTaxComposition

    POST /masters/items/bulk-tax-update/
    Body:
    {
        "item_ids": [1, 2, 3],
        "new_tax_id": 5,
        "composition_type": "PRIMARY",
        "effective_from": "2024-01-01"
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        item_ids = request.data.get('item_ids', [])
        new_tax_id = request.data.get('new_tax_id')
        composition_type = request.data.get('composition_type', 'PRIMARY')
        effective_from_str = request.data.get('effective_from')

        if not item_ids or not new_tax_id or not effective_from_str:
            return Response(
                {'error': 'item_ids, new_tax_id, and effective_from are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            effective_from = date.fromisoformat(effective_from_str)
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Close old compositions
        previous_day = effective_from - timedelta(days=1)
        ItemTaxComposition.objects.filter(
            item_id__in=item_ids,
            composition_type=composition_type,
            effective_to__isnull=True
        ).update(effective_to=previous_day)

        # Create new compositions
        new_compositions = [
            ItemTaxComposition(
                item_id=item_id,
                tax_id=new_tax_id,
                composition_type=composition_type,
                effective_from=effective_from
            )
            for item_id in item_ids
        ]
        ItemTaxComposition.objects.bulk_create(new_compositions)

        return Response({
            'message': f'Tax updated for {len(item_ids)} items',
            'items_updated': len(item_ids)
        }, status=status.HTTP_200_OK)


# Import Tax Compositions View (updated from ItemTaxMapping)
class ImportTaxCompositionsView(APIView):
    """
    Import tax compositions from CSV/Excel file using django-import-export

    POST /masters/item-tax-compositions/import/
    Body: multipart/form-data with 'file' field

    Expected CSV/Excel format:
    Item Code,Tax Code,Composition Type,Effective From,Effective To
    ITEM001,TAX01,PRIMARY,2026-01-01,
    ITEM002,TAX02,CESS,2026-01-01,2026-12-31
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from tablib import Dataset

        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file uploaded'},
                status=status.HTTP_400_BAD_REQUEST
            )

        file = request.FILES['file']
        file_extension = file.name.split('.')[-1].lower()

        try:
            # Read file into dataset
            dataset = Dataset()

            if file_extension == 'csv':
                dataset.load(file.read().decode('utf-8'), format='csv')
            elif file_extension in ['xlsx', 'xls']:
                dataset.load(file.read(), format='xlsx' if file_extension == 'xlsx' else 'xls')
            else:
                return Response(
                    {'error': 'Unsupported file format. Use CSV or Excel (.xlsx, .xls)'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Process the data manually since we don't have a resource for ItemTaxComposition yet
            created_count = 0
            errors = []

            for row_num, row in enumerate(dataset.dict, 1):
                try:
                    # Create ItemTaxComposition from row data
                    serializer = ItemTaxCompositionCreateSerializer(data={
                        'item': row.get('Item Code'),  # This would need to be resolved to item ID
                        'tax': row.get('Tax Code'),    # This would need to be resolved to tax ID
                        'composition_type': row.get('Composition Type', 'PRIMARY'),
                        'effective_from': row.get('Effective From'),
                        'effective_to': row.get('Effective To') or None,
                    })

                    if serializer.is_valid():
                        serializer.save()
                        created_count += 1
                    else:
                        errors.append({
                            'row': row_num,
                            'errors': serializer.errors
                        })
                except Exception as e:
                    errors.append({
                        'row': row_num,
                        'error': str(e)
                    })

            response_data = {
                'message': f'Successfully imported {created_count} row(s)',
                'total_rows': len(dataset),
                'created_count': created_count,
                'error_count': len(errors),
            }

            if errors:
                response_data['errors'] = errors

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': f'Failed to process file: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Item UOM Conversion Views
class ItemUOMConversionList(generics.ListCreateAPIView):
    serializer_class = ItemUOMConversionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        item_id = self.request.query_params.get('item_id')
        if item_id:
            return ItemUOMConversion.objects.filter(item_id=item_id, is_deleted=False)
        return ItemUOMConversion.objects.filter(is_deleted=False)


class ItemUOMConversionDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = ItemUOMConversion.objects.filter(is_deleted=False)
    serializer_class = ItemUOMConversionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()

    @extend_schema(
        summary="Create a new UOM",
        request=UOMSerializer,
        responses={201: UOMSerializer}
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ItemFieldConfigurationListAPIView(generics.ListAPIView):
    """Get all Item field configurations"""
    queryset = ItemFieldConfiguration.objects.all().order_by('section', 'display_order', 'id')
    serializer_class = ItemFieldConfigurationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # Disable pagination to return all configs

    def get_queryset(self):
        queryset = ItemFieldConfiguration.objects.all().order_by('section', 'display_order', 'id')

        # Seed defaults if table is empty so the UI always has something to render
        if not queryset.exists():
            upsert_item_field_configurations()
            queryset = ItemFieldConfiguration.objects.all().order_by('section', 'display_order', 'id')

        return queryset


class ItemFieldConfigurationBulkUpdateAPIView(APIView):
    """Update multiple Item field configurations at once"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Check if user has permission or is superuser
        if not (request.user.is_superuser or request.user.has_perm('Masters.change_itemfieldconfiguration')):
            return Response(
                {'error': 'You do not have permission to change field configurations'},
                status=status.HTTP_403_FORBIDDEN
            )

        configurations = request.data.get('configurations', [])
        if not configurations:
            return Response(
                {'error': 'No configurations provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        updated_configs = []
        for config_data in configurations:
            field_name = config_data.get('field_name')
            if not field_name:
                continue
            defaults = {
                'display_label': config_data.get('display_label', field_name),
                'is_visible': config_data.get('is_visible', True),
                'is_required': config_data.get('is_required', False),
                'is_readonly': config_data.get('is_readonly', False),
                'display_order': config_data.get('display_order', 0),
                'section': config_data.get('section', 'basic'),
            }

            config, _ = ItemFieldConfiguration.objects.update_or_create(
                field_name=field_name,
                defaults=defaults,
            )
            updated_configs.append(config)

        serialized = ItemFieldConfigurationSerializer(updated_configs, many=True)
        return Response(serialized.data, status=status.HTTP_200_OK)


# ==================== Channel Partner Views ====================

class SuperstockistFilter(FilterSet):
    state = django_filters.UUIDFilter(field_name='state__id')
    city = django_filters.UUIDFilter(method='filter_by_city')
    area = django_filters.UUIDFilter(method='filter_by_area')

    def filter_by_city(self, queryset, name, value):
        """
        Filter superstockists by their coverage city.
        Returns superstockists that cover this city (with or without specific areas).
        """
        from django.db.models import Q
        return queryset.filter(
            Q(locations__city__id=value) | Q(locations__city__id=value, locations__area__isnull=True)
        ).distinct()

    def filter_by_area(self, queryset, name, value):
        """
        Filter superstockists by their coverage area.
        Returns superstockists that:
        1. Specifically cover this area, OR
        2. Cover the parent city without specific area restrictions (city-wide coverage)
        """
        from django.db.models import Q
        from Masters.models import Area

        try:
            area = Area.objects.get(id=value)
            return queryset.filter(
                Q(locations__area__id=value) |  # Specific area coverage
                Q(locations__city__id=area.city_id, locations__area__isnull=True)  # City-wide coverage
            ).distinct()
        except Area.DoesNotExist:
            return queryset.none()

    class Meta:
        model = Superstockist
        fields = ['is_active', 'state', 'city', 'area']


class SuperstockistMini(generics.ListAPIView):
    serializer_class = SuperstockistMiniSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = SuperstockistFilter
    search_fields = ['code', 'name']

    def get_queryset(self):
        queryset = Superstockist.filtered_objects.get_qs(
            user=self.request.user,
            is_active=True
        )
        queryset = apply_channel_partner_company_location_filter(
            queryset,
            self.request.user,
            company_field='company',
            state_field='state',
            city_field='city',
            coverage_relation='locations'
        )
        return queryset.order_by('name').distinct()


class SuperstockistList(ChannelPartnerAttachmentMixin, generics.ListCreateAPIView):
    serializer_class = SuperstockistSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = SuperstockistFilter
    search_fields = [
        'code',
        'name',
        'gstin',
        'pan',
        'state__name',
        'city__name',
        'area__name']
    ordering_fields = ['code', 'name', 'created_on']
    ordering = ['-created_on']

    def create(self, request, *args, **kwargs):
        """Override create to handle FormData with attachments"""
        import json

        # If 'data' field exists, it means FormData is being sent with attachments
        if 'data' in request.data:
            # Parse the JSON data from the 'data' field
            data = json.loads(request.data['data'])
            serializer = self.get_serializer(data=data)
        else:
            # Regular JSON request
            serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_queryset(self):
        queryset = Superstockist.filtered_objects.get_qs(
            user=self.request.user
        )
        queryset = apply_channel_partner_company_location_filter(
            queryset,
            self.request.user,
            company_field='company',
            state_field='state',
            city_field='city',
            coverage_relation='locations'
        )
        return queryset.select_related('state', 'company').prefetch_related('contacts').distinct()

    def perform_create(self, serializer):
        from Masters.models import Company
        user = self.request.user
        company = user.company if hasattr(user, 'company') else None
        if company is None:
            company = Company.objects.filter(is_deleted=False).first()

        instance = serializer.save(company=company)
        self.handle_attachments(instance, self.request)


class SuperstockistDetail(ChannelPartnerAttachmentMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SuperstockistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Superstockist.filtered_objects.get_qs(
            user=self.request.user
        )
        queryset = apply_channel_partner_company_location_filter(
            queryset,
            self.request.user,
            company_field='company',
            state_field='state',
            city_field='city',
            coverage_relation='locations'
        )
        return queryset.select_related('state', 'company').prefetch_related('locations').distinct()

    def perform_update(self, serializer):
        instance = serializer.save()
        self.handle_attachments(instance, self.request)

    def perform_destroy(self, instance):
        from Sales.models import SalesOrder
        linked = []
        if Distributor.objects.filter(superstockist=instance, is_deleted=False).exists():
            linked.append('distributors')
        if SalesOrder.objects.filter(superstockist=instance, is_deleted=False).exists():
            linked.append('sales orders')
        if linked:
            raise DRFValidationError({'detail': f'Cannot delete superstockist "{instance.name}" because it has associated {", ".join(linked)}.'})
        instance.name = _deleted_suffix_value(instance, "name")
        instance.code = _deleted_suffix_value(instance, "code")
        instance.gstin = None
        instance.is_deleted = True
        instance.save()


class SuperstockistLocationList(generics.ListCreateAPIView):
    serializer_class = SuperstockistLocationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        superstockist_id = self.kwargs.get('superstockist_id')
        return SuperstockistLocation.objects.filter(
            superstockist_id=superstockist_id
        ).select_related('state', 'city', 'area')

    def perform_create(self, serializer):
        superstockist_id = self.kwargs.get('superstockist_id')
        superstockist = get_object_or_404(Superstockist, id=superstockist_id, is_deleted=False)
        serializer.save(superstockist=superstockist)


class SuperstockistLocationDetail(generics.RetrieveDestroyAPIView):
    serializer_class = SuperstockistLocationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        superstockist_id = self.kwargs.get('superstockist_id')
        return SuperstockistLocation.objects.filter(
            superstockist_id=superstockist_id
        ).select_related('state', 'city', 'area')


class SuperstockistLocationBulk(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, superstockist_id):
        """Bulk create/replace locations for a superstockist"""
        superstockist = get_object_or_404(Superstockist, id=superstockist_id, is_deleted=False)

        # Get selected items from request
        selected_states = request.data.get('states', [])  # List of state IDs
        selected_cities = request.data.get('cities', [])  # List of city IDs
        selected_areas = request.data.get('areas', [])    # List of area IDs

        # Clear existing locations if replace=True
        if request.data.get('replace', True):
            SuperstockistLocation.objects.filter(superstockist=superstockist).delete()

        # Expand selections to create location records
        locations_to_create = []

        # If areas are selected, create those specific combinations
        if selected_areas:
            for area_id in selected_areas:
                area = Area.objects.filter(id=area_id, is_deleted=False).select_related('city__state').first()
                if area:
                    locations_to_create.append(
                        SuperstockistLocation(
                            superstockist=superstockist,
                            state=area.city.state,
                            city=area.city,
                            area=area
                        )
                    )

        # If cities are selected (but not all areas), create city-level entries
        elif selected_cities:
            for city_id in selected_cities:
                city = City.objects.filter(id=city_id, is_deleted=False).select_related('state').first()
                if city:
                    # Get all areas for this city
                    areas = Area.objects.filter(city=city, is_deleted=False)
                    for area in areas:
                        locations_to_create.append(
                            SuperstockistLocation(
                                superstockist=superstockist,
                                state=city.state,
                                city=city,
                                area=area
                            )
                        )

        # If only states are selected, create state-level entries with all cities and areas
        elif selected_states:
            for state_id in selected_states:
                state = State.objects.filter(id=state_id, is_deleted=False).first()
                if state:
                    # Get all cities for this state
                    cities = City.objects.filter(state=state, is_deleted=False)
                    for city in cities:
                        # Get all areas for this city
                        areas = Area.objects.filter(city=city, is_deleted=False)
                        for area in areas:
                            locations_to_create.append(
                                SuperstockistLocation(
                                    superstockist=superstockist,
                                    state=state,
                                    city=city,
                                    area=area
                                )
                            )

        # Bulk create all locations
        if locations_to_create:
            SuperstockistLocation.objects.bulk_create(locations_to_create, ignore_conflicts=True)

        # Return summary
        total_locations = SuperstockistLocation.objects.filter(superstockist=superstockist).count()
        states_count = SuperstockistLocation.objects.filter(
            superstockist=superstockist).values('state').distinct().count()
        cities_count = SuperstockistLocation.objects.filter(
            superstockist=superstockist).values('city').distinct().count()
        areas_count = total_locations

        return Response({
            'message': 'Locations updated successfully',
            'summary': {
                'states': states_count,
                'cities': cities_count,
                'areas': areas_count,
                'total_records': total_locations
            }
        }, status=status.HTTP_200_OK)

    def get(self, request, superstockist_id):
        """Get location summary for a superstockist"""
        superstockist = get_object_or_404(Superstockist, id=superstockist_id, is_deleted=False)

        total_locations = SuperstockistLocation.objects.filter(superstockist=superstockist).count()
        states_count = SuperstockistLocation.objects.filter(
            superstockist=superstockist).values('state').distinct().count()
        cities_count = SuperstockistLocation.objects.filter(
            superstockist=superstockist).values('city').distinct().count()
        areas_count = total_locations

        # Get detailed list grouped by state
        locations = SuperstockistLocation.objects.filter(
            superstockist=superstockist
        ).select_related('state', 'city', 'area').order_by('state__name', 'city__name', 'area__name')

        return Response({
            'summary': {
                'states': states_count,
                'cities': cities_count,
                'areas': areas_count,
                'total_records': total_locations
            },
            'locations': SuperstockistLocationSerializer(locations, many=True).data
        }, status=status.HTTP_200_OK)


class DistributorFilter(FilterSet):
    state = django_filters.UUIDFilter(field_name='state__id')
    superstockist = django_filters.UUIDFilter(field_name='superstockist__id')
    city = django_filters.UUIDFilter(method='filter_by_city')
    area = django_filters.UUIDFilter(method='filter_by_area')

    def filter_by_city(self, queryset, name, value):
        """
        Filter distributors by their coverage city.
        Returns distributors that cover this city (with or without specific areas).
        """
        from django.db.models import Q
        return queryset.filter(
            Q(locations__city__id=value) | Q(locations__city__id=value, locations__area__isnull=True)
        ).distinct()

    def filter_by_area(self, queryset, name, value):
        """
        Filter distributors by their coverage area.
        Returns distributors that:
        1. Specifically cover this area, OR
        2. Cover the parent city without specific area restrictions (city-wide coverage)
        """
        from django.db.models import Q
        from Masters.models import Area

        try:
            area = Area.objects.get(id=value)
            return queryset.filter(
                Q(locations__area__id=value) |  # Specific area coverage
                Q(locations__city__id=area.city_id, locations__area__isnull=True)  # City-wide coverage
            ).distinct()
        except Area.DoesNotExist:
            return queryset.none()

    class Meta:
        model = Distributor
        fields = ['is_active', 'state', 'superstockist', 'city', 'area']


class DistributorMini(generics.ListAPIView):
    serializer_class = DistributorMiniSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = DistributorFilter
    search_fields = ['code', 'name']

    def get_queryset(self):
        queryset = Distributor.filtered_objects.get_qs(
            user=self.request.user,
            is_active=True
        )
        queryset = apply_channel_partner_company_location_filter(
            queryset,
            self.request.user,
            company_field='company',
            state_field='state',
            city_field='city',
            coverage_relation='locations'
        )
        return queryset.order_by('name').distinct()


class DistributorList(ChannelPartnerAttachmentMixin, generics.ListCreateAPIView):
    serializer_class = DistributorSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DistributorFilter
    search_fields = [
        'code',
        'name',
        'gstin',
        'pan',
        'superstockist__name',
        'state__name',
        'city__name',
        'area__name']
    ordering_fields = ['code', 'name', 'created_on']
    ordering = ['-created_on']

    def create(self, request, *args, **kwargs):
        """Override create to handle FormData with attachments"""
        import json

        # If 'data' field exists, it means FormData is being sent with attachments
        if 'data' in request.data:
            # Parse the JSON data from the 'data' field
            data = json.loads(request.data['data'])
            serializer = self.get_serializer(data=data)
        else:
            # Regular JSON request
            serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_queryset(self):
        queryset = Distributor.filtered_objects.get_qs(
            user=self.request.user
        )
        queryset = apply_channel_partner_company_location_filter(
            queryset,
            self.request.user,
            company_field='company',
            state_field='state',
            city_field='city',
            coverage_relation='locations'
        )
        return queryset.select_related('state', 'superstockist', 'company').prefetch_related('contacts').distinct()

    def perform_create(self, serializer):
        instance = serializer.save()
        self.handle_attachments(instance, self.request)


class DistributorDetail(ChannelPartnerAttachmentMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DistributorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Distributor.filtered_objects.get_qs(
            user=self.request.user
        )
        queryset = apply_channel_partner_company_location_filter(
            queryset,
            self.request.user,
            company_field='company',
            state_field='state',
            city_field='city',
            coverage_relation='locations'
        )
        return queryset.select_related('state', 'superstockist', 'company').prefetch_related('locations').distinct()
    
    def get_object(self):
        """Override to provide better error message for channel partner users"""
        try:
            return super().get_object()
        except Http404:
            # Provide helpful error for channel partner users without proper assignment
            if hasattr(self.request.user, 'channel_partner_type'):
                if self.request.user.channel_partner_type == 'DISTRIBUTOR' and not self.request.user.distributor:
                    from rest_framework.exceptions import PermissionDenied
                    raise PermissionDenied(
                        "Your user account is not properly linked to a distributor. "
                        "Please contact your administrator to assign a distributor to your account."
                    )
            raise

    def perform_update(self, serializer):
        instance = serializer.save()
        self.handle_attachments(instance, self.request)

    def perform_destroy(self, instance):
        from Sales.models import SalesOrder
        linked = []
        if Retailer.objects.filter(distributor=instance, is_deleted=False).exists():
            linked.append('retailers')
        if SalesOrder.objects.filter(distributor=instance, is_deleted=False).exists():
            linked.append('sales orders')
        if linked:
            raise DRFValidationError({'detail': f'Cannot delete distributor "{instance.name}" because it has associated {", ".join(linked)}.'})
        instance.name = _deleted_suffix_value(instance, "name")
        instance.code = _deleted_suffix_value(instance, "code")
        instance.gstin = None
        instance.is_deleted = True
        instance.save()


class DistributorLocationList(generics.ListCreateAPIView):
    serializer_class = DistributorLocationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        distributor_id = self.kwargs.get('distributor_id')
        return DistributorLocation.objects.filter(
            distributor_id=distributor_id
        ).select_related('state', 'city', 'area')

    def perform_create(self, serializer):
        distributor_id = self.kwargs.get('distributor_id')
        distributor = get_object_or_404(Distributor, id=distributor_id, is_deleted=False)
        serializer.save(distributor=distributor)


class DistributorLocationDetail(generics.RetrieveDestroyAPIView):
    serializer_class = DistributorLocationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        distributor_id = self.kwargs.get('distributor_id')
        return DistributorLocation.objects.filter(
            distributor_id=distributor_id
        ).select_related('state', 'city', 'area')


class DistributorLocationBulk(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, distributor_id):
        """Bulk create/replace locations for a distributor"""
        distributor = get_object_or_404(Distributor, id=distributor_id, is_deleted=False)

        # Get selected items from request
        selected_states = request.data.get('states', [])
        selected_cities = request.data.get('cities', [])
        selected_areas = request.data.get('areas', [])

        # Clear existing locations if replace=True
        if request.data.get('replace', True):
            DistributorLocation.objects.filter(distributor=distributor).delete()

        # Expand selections to create location records
        locations_to_create = []

        # If areas are selected, create those specific combinations
        if selected_areas:
            for area_id in selected_areas:
                area = Area.objects.filter(id=area_id, is_deleted=False).select_related('city__state').first()
                if area:
                    locations_to_create.append(
                        DistributorLocation(
                            distributor=distributor,
                            state=area.city.state,
                            city=area.city,
                            area=area
                        )
                    )

        # If cities are selected (but not all areas), create city-level entries
        elif selected_cities:
            for city_id in selected_cities:
                city = City.objects.filter(id=city_id, is_deleted=False).select_related('state').first()
                if city:
                    # Get all areas for this city
                    areas = Area.objects.filter(city=city, is_deleted=False)
                    for area in areas:
                        locations_to_create.append(
                            DistributorLocation(
                                distributor=distributor,
                                state=city.state,
                                city=city,
                                area=area
                            )
                        )

        # If only states are selected, create state-level entries with all cities and areas
        elif selected_states:
            for state_id in selected_states:
                state = State.objects.filter(id=state_id, is_deleted=False).first()
                if state:
                    # Get all cities for this state
                    cities = City.objects.filter(state=state, is_deleted=False)
                    for city in cities:
                        # Get all areas for this city
                        areas = Area.objects.filter(city=city, is_deleted=False)
                        for area in areas:
                            locations_to_create.append(
                                DistributorLocation(
                                    distributor=distributor,
                                    state=state,
                                    city=city,
                                    area=area
                                )
                            )

        # Bulk create all locations
        if locations_to_create:
            DistributorLocation.objects.bulk_create(locations_to_create, ignore_conflicts=True)

        # Return summary
        total_locations = DistributorLocation.objects.filter(distributor=distributor).count()
        states_count = DistributorLocation.objects.filter(distributor=distributor).values('state').distinct().count()
        cities_count = DistributorLocation.objects.filter(distributor=distributor).values('city').distinct().count()
        areas_count = total_locations

        return Response({
            'message': 'Locations updated successfully',
            'summary': {
                'states': states_count,
                'cities': cities_count,
                'areas': areas_count,
                'total_records': total_locations
            }
        }, status=status.HTTP_200_OK)

    def get(self, request, distributor_id):
        """Get location summary for a distributor"""
        distributor = get_object_or_404(Distributor, id=distributor_id, is_deleted=False)

        total_locations = DistributorLocation.objects.filter(distributor=distributor).count()
        states_count = DistributorLocation.objects.filter(distributor=distributor).values('state').distinct().count()
        cities_count = DistributorLocation.objects.filter(distributor=distributor).values('city').distinct().count()
        areas_count = total_locations

        # Get detailed list grouped by state
        locations = DistributorLocation.objects.filter(
            distributor=distributor
        ).select_related('state', 'city', 'area').order_by('state__name', 'city__name', 'area__name')

        return Response({
            'summary': {
                'states': states_count,
                'cities': cities_count,
                'areas': areas_count,
                'total_records': total_locations
            },
            'locations': DistributorLocationSerializer(locations, many=True).data
        }, status=status.HTTP_200_OK)


class RetailerFilter(FilterSet):
    state = django_filters.UUIDFilter(field_name='state__id')
    city = django_filters.UUIDFilter(field_name='city__id')
    area = django_filters.UUIDFilter(field_name='area__id')
    distributor = django_filters.UUIDFilter(field_name='distributor__id')
    outlet_type = django_filters.UUIDFilter(field_name='outlet_type__id')

    class Meta:
        model = Retailer
        fields = ['is_active', 'state', 'city', 'area', 'distributor', 'outlet_type']


class RetailerMini(generics.ListAPIView):
    serializer_class = RetailerMiniSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = RetailerFilter
    search_fields = ['code', 'name']

    def get_queryset(self):
        queryset = Retailer.filtered_objects.get_qs(
            user=self.request.user,
            is_active=True
        )
        queryset = apply_channel_partner_company_location_filter(
            queryset,
            self.request.user,
            company_field='company',
            state_field='state',
            city_field='city',
            coverage_relation='locations'
        )
        return queryset.order_by('name').distinct()


class RetailerList(ChannelPartnerAttachmentMixin, generics.ListCreateAPIView):
    serializer_class = RetailerSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = RetailerFilter
    search_fields = [
        'code',
        'name',
        'gstin',
        'pan',
        'distributor__name',
        'outlet_type__name',
        'state__name',
        'city__name',
        'area__name']
    ordering_fields = ['code', 'name', 'created_on']
    ordering = ['-created_on']

    def create(self, request, *args, **kwargs):
        """Override create to handle FormData with attachments"""
        import json

        # If 'data' field exists, it means FormData is being sent with attachments
        if 'data' in request.data:
            # Parse the JSON data from the 'data' field
            data = json.loads(request.data['data'])
            serializer = self.get_serializer(data=data)
        else:
            # Regular JSON request
            serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_queryset(self):
        queryset = Retailer.filtered_objects.get_qs(
            user=self.request.user
        )
        queryset = apply_channel_partner_company_location_filter(
            queryset,
            self.request.user,
            company_field='company',
            state_field='state',
            city_field='city',
            coverage_relation='locations'
        )
        return queryset.select_related('state', 'distributor', 'outlet_type',
                                       'company').prefetch_related('contacts').distinct()

    def perform_create(self, serializer):
        from Masters.models import Company
        user = self.request.user
        company = user.company if hasattr(user, 'company') else None
        if company is None:
            company = Company.objects.filter(is_deleted=False).first()

        instance = serializer.save(company=company)
        self.handle_attachments(instance, self.request)


class RetailerDetail(ChannelPartnerAttachmentMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RetailerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Retailer.filtered_objects.get_qs(
            user=self.request.user
        )
        queryset = apply_channel_partner_company_location_filter(
            queryset,
            self.request.user,
            company_field='company',
            state_field='state',
            city_field='city',
            coverage_relation='locations'
        )
        return queryset.select_related('state', 'distributor', 'outlet_type',
                                       'company').prefetch_related('locations').distinct()

    def perform_update(self, serializer):
        instance = serializer.save()
        self.handle_attachments(instance, self.request)

    def perform_destroy(self, instance):
        from Sales.models import SalesOrder
        linked = []
        if SalesOrder.objects.filter(retailer=instance, is_deleted=False).exists():
            linked.append('sales orders')
        if linked:
            raise DRFValidationError({'detail': f'Cannot delete retailer "{instance.name}" because it has associated {", ".join(linked)}.'})
        instance.name = _deleted_suffix_value(instance, "name")
        instance.code = _deleted_suffix_value(instance, "code")
        instance.gstin = None
        instance.is_deleted = True
        instance.save()


class RetailerLocationList(generics.ListCreateAPIView):
    serializer_class = RetailerLocationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        retailer_id = self.kwargs.get('retailer_id')
        return RetailerLocation.objects.filter(
            retailer_id=retailer_id
        ).select_related('state', 'city', 'area')

    def perform_create(self, serializer):
        retailer_id = self.kwargs.get('retailer_id')
        retailer = get_object_or_404(Retailer, id=retailer_id, is_deleted=False)
        serializer.save(retailer=retailer)


class RetailerLocationDetail(generics.RetrieveDestroyAPIView):
    serializer_class = RetailerLocationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        retailer_id = self.kwargs.get('retailer_id')
        return RetailerLocation.objects.filter(
            retailer_id=retailer_id
        ).select_related('state', 'city', 'area')


# ================================
# Price Book Views
# ================================

class PriceBookFilter(FilterSet):
    item_code = CharFilter(field_name='item__code', lookup_expr='icontains')
    item_name = CharFilter(field_name='item__name', lookup_expr='icontains')
    price_type = CharFilter(field_name='price_type')
    state_code = CharFilter(field_name='state__code', lookup_expr='icontains')
    city_code = CharFilter(field_name='city__code', lookup_expr='icontains')
    area_code = CharFilter(field_name='area__code', lookup_expr='icontains')
    superstockist_code = CharFilter(field_name='superstockist__code', lookup_expr='icontains')
    distributor_code = CharFilter(field_name='distributor__code', lookup_expr='icontains')
    retailer_code = CharFilter(field_name='retailer__code', lookup_expr='icontains')
    is_active = BooleanFilter(field_name='is_active')
    effective_from_start = DateFilter(field_name='effective_from', lookup_expr='gte')
    effective_from_end = DateFilter(field_name='effective_from', lookup_expr='lte')

    class Meta:
        model = PriceBook
        fields = [
            'item_code', 'item_name', 'price_type',
            'state_code', 'city_code', 'area_code',
            'superstockist_code', 'distributor_code', 'retailer_code',
            'is_active', 'effective_from_start', 'effective_from_end'
        ]


class PriceBookMini(generics.ListAPIView):
    serializer_class = PriceBookMiniSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        queryset = PriceBook.objects.filter(
            is_deleted=False,
            is_active=True
        ).select_related('item')
        return apply_company_location_filter(queryset, self.request.user, company_field='company')[:100]


class PriceBookList(generics.ListCreateAPIView):
    serializer_class = PriceBookSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = PriceBookFilter

    def get_queryset(self):
        queryset = PriceBook.objects.filter(
            is_deleted=False
        ).select_related(
            'item', 'document', 'state', 'city', 'area',
            'superstockist', 'distributor', 'retailer'
        ).order_by('-created_on')
        return apply_company_location_filter(queryset, self.request.user, company_field='company')


class PriceBookDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PriceBookSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = PriceBook.objects.select_related(
            'item', 'document', 'state', 'city', 'area',
            'superstockist', 'distributor', 'retailer'
        )
        # For DELETE, allow fetching even if already soft-deleted so we can return 204
        if getattr(self.request, 'method', '').upper() == 'DELETE':
            return apply_company_location_filter(qs, self.request.user, company_field='company')
        return apply_company_location_filter(qs.filter(is_deleted=False), self.request.user, company_field='company')

    def delete(self, request, *args, **kwargs):
        """Soft delete; if already deleted, return 204 instead of 404"""
        pk = kwargs.get('pk')
        instance = PriceBook.objects.filter(id=pk).first()

        # If not found at all, treat as idempotent success
        if not instance:
            return Response(status=status.HTTP_204_NO_CONTENT)

        if instance.is_deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)

        instance.is_deleted = True
        instance.save(update_fields=['is_deleted'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class PriceBookDocumentList(generics.ListAPIView):
    """List all price book documents"""
    serializer_class = PriceBookDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['location_type', 'document_date', 'cp_filter_state', 'cp_filter_city', 'cp_filter_area', 'status']
    search_fields = ['document_number', 'remarks', 'location_type', 'status', 'cp_filter_state__name', 'cp_filter_city__name', 'cp_filter_area__name']
    ordering_fields = ['document_number', 'document_date', 'created_on']
    ordering = ['-document_date', '-created_on']

    def get_queryset(self):
        from django.utils import timezone
        
        queryset = PriceBookDocument.objects.filter(is_deleted=False)
        
        # Auto-close documents where all entries have expired
        today = timezone.now().date()
        active_docs = queryset.filter(status='ACTIVE')
        
        for doc in active_docs:
            total_entries = doc.price_entries.filter(is_deleted=False).count()
            if total_entries > 0:
                expired_entries = doc.price_entries.filter(
                    is_deleted=False,
                    effective_to__isnull=False,
                    effective_to__lt=today
                ).count()
                
                if expired_entries == total_entries:
                    doc.status = 'CLOSED'
                    doc.save(update_fields=['status'])
        
        return queryset


class PriceBookDocumentDetail(generics.RetrieveAPIView):
    """Get a single price book document with all its price entries"""
    serializer_class = PriceBookDocumentDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PriceBookDocument.objects.filter(is_deleted=False)


class PriceBookDocumentDelete(APIView):
    """Delete price book document and all related entries"""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        """Soft delete document and cascade to all price entries, restore previously closed records"""
        from datetime import timedelta
        import logging
        logger = logging.getLogger(__name__)

        try:
            document = PriceBookDocument.objects.get(id=pk)
        except PriceBookDocument.DoesNotExist:
            return Response(status=status.HTTP_204_NO_CONTENT)

        if document.is_deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)

        logger.info(f"Deleting document {pk} with effective_from: {document.effective_from}")

        # Before deleting, restore previously closed records
        if document.effective_from:
            previous_day = document.effective_from - timedelta(days=1)
            logger.info(f"Looking for records with effective_to: {previous_day}")

            # Get all entries from this document
            entries_to_delete = PriceBook.objects.filter(document=document, is_deleted=False)
            logger.info(f"Found {entries_to_delete.count()} entries to process")

            for entry in entries_to_delete:
                # Build filter to find records that were closed by this entry
                restore_filters = {
                    'item_id': entry.item_id,
                    'effective_to': previous_day,
                    'is_deleted': False
                }

                # Determine location type and add appropriate filter
                location_type = None
                if entry.state_id and not entry.city_id:
                    location_type = 'STATE'
                    restore_filters['state_id'] = entry.state_id
                    restore_filters['city__isnull'] = True
                    restore_filters['area__isnull'] = True
                elif entry.city_id and not entry.area_id:
                    location_type = 'CITY'
                    restore_filters['city_id'] = entry.city_id
                    restore_filters['area__isnull'] = True
                elif entry.area_id:
                    location_type = 'AREA'
                    restore_filters['area_id'] = entry.area_id
                elif entry.superstockist_id:
                    location_type = 'SUPERSTOCKIST'
                    restore_filters['superstockist_id'] = entry.superstockist_id
                elif entry.distributor_id:
                    location_type = 'DISTRIBUTOR'
                    restore_filters['distributor_id'] = entry.distributor_id
                elif entry.retailer_id:
                    location_type = 'RETAILER'
                    restore_filters['retailer_id'] = entry.retailer_id
                else:
                    # BASE location
                    location_type = 'BASE'
                    restore_filters.update({
                        'state__isnull': True,
                        'city__isnull': True,
                        'area__isnull': True,
                        'superstockist__isnull': True,
                        'distributor__isnull': True,
                        'retailer__isnull': True
                    })

                logger.info(f"Entry {entry.id}: item={entry.item_id}, location_type={location_type}, filters={restore_filters}")

                # Find and restore records that were closed by this entry
                closed_records = PriceBook.objects.filter(**restore_filters).exclude(document=document)
                logger.info(f"Found {closed_records.count()} closed records to restore")

                if closed_records.exists():
                    # Clear effective_to to make them ongoing again
                    updated_count = closed_records.update(effective_to=None)
                    logger.info(f"Restored {updated_count} records to ongoing status")

                    # Also update their parent documents if all entries in that document should be ongoing
                    doc_ids = closed_records.values_list('document_id', flat=True).distinct()
                    for doc_id in doc_ids:
                        doc_entries = PriceBook.objects.filter(document_id=doc_id, is_deleted=False)
                        # If all entries have null effective_to, update document too
                        if not doc_entries.filter(effective_to__isnull=False).exists():
                            PriceBookDocument.objects.filter(id=doc_id).update(effective_to=None)
                            logger.info(f"Updated document {doc_id} effective_to to None")

        # Soft delete the document
        document.is_deleted = True
        document.save(update_fields=['is_deleted'])

        # Cascade soft delete to all related price entries
        deleted_count = PriceBook.objects.filter(document=document).update(is_deleted=True)
        logger.info(f"Soft deleted document {pk} and {deleted_count} entries")

        return Response(status=status.HTTP_204_NO_CONTENT)


class PriceBookDocumentUpdate(APIView):
    """
    Update price book document with its price entries

    PUT/PATCH /api/masters/price-book-documents/<id>/update/
    {
        "document_date": "2026-01-08",
        "effective_from": "2026-01-08",
        "effective_to": "2026-12-31",
        "remarks": "",
        "prices": [
            {
                "item_id": "uuid",
                "location_id": "uuid" or null,
                "selling_price": "120.00"
            }
        ]
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk):
        return self._update(request, pk)

    def patch(self, request, pk):
        return self._update(request, pk)

    def _update(self, request, pk):
        from .models import PriceBookDocument, PriceBook, Company

        try:
            document = PriceBookDocument.objects.get(id=pk, is_deleted=False)
        except PriceBookDocument.DoesNotExist:
            return Response(
                {'error': 'Document not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if effective_from is being changed
        old_effective_from = document.effective_from
        new_effective_from_str = request.data.get('effective_from')
        cp_filter_state = request.data.get('cp_filter_state')
        cp_filter_city = request.data.get('cp_filter_city')
        cp_filter_area = request.data.get('cp_filter_area')
        selected_categories = request.data.get('selected_categories')
        selected_brands = request.data.get('selected_brands')

        if new_effective_from_str:
            # Parse the date string
            if isinstance(new_effective_from_str, str):
                from datetime import datetime
                new_effective_from = datetime.strptime(new_effective_from_str, '%Y-%m-%d').date()
            else:
                new_effective_from = new_effective_from_str
        else:
            new_effective_from = document.effective_from

        effective_from_changed = old_effective_from != new_effective_from

        # Update document fields
        from datetime import datetime as _dt
        def _parse_date(val):
            if val is None:
                return None
            if isinstance(val, str):
                return _dt.strptime(val, '%Y-%m-%d').date()
            return val

        document.document_date = _parse_date(request.data.get('document_date')) or document.document_date
        document.effective_from = new_effective_from
        document.effective_to = _parse_date(request.data.get('effective_to')) if 'effective_to' in request.data else document.effective_to
        document.remarks = request.data.get('remarks', document.remarks)
        if selected_categories is not None:
            document.selected_categories = selected_categories
        if selected_brands is not None:
            document.selected_brands = selected_brands
        if document.location_type in ['SUPERSTOCKIST', 'DISTRIBUTOR', 'RETAILER']:
            document.cp_filter_state_id = cp_filter_state or None
            document.cp_filter_city_id = cp_filter_city or None
            document.cp_filter_area_id = cp_filter_area or None
        else:
            document.cp_filter_state = None
            document.cp_filter_city = None
            document.cp_filter_area = None
        document.save()
        if document.status == 'DRAFT':
            _set_draft_authorization(document)

        # Update all entries in this document to have the same effective dates as the document
        PriceBook.objects.filter(document=document, is_deleted=False).update(
            effective_from=document.effective_from,
            effective_to=document.effective_to
        )

        # If effective_from changed, auto-close previous ongoing prices for all entries in this document
        if effective_from_changed:
            previous_day = document.effective_from - timedelta(days=1)

            # Get all price entries in this document
            document_entries = PriceBook.objects.filter(document=document, is_deleted=False)

            auto_closed_total = 0

            for entry in document_entries:

                # Build filter for ongoing prices with same item and location
                close_filters = {
                    'item_id': entry.item_id,
                    'effective_to__isnull': True,
                    'is_deleted': False
                }

                close_filters_qs = PriceBook.objects.filter(**close_filters).exclude(id=entry.id)

                # Add location filter based on document's location type
                if document.location_type == 'STATE' and entry.state_id:
                    close_filters_qs = close_filters_qs.filter(state_id=entry.state_id)
                elif document.location_type == 'CITY' and entry.city_id:
                    close_filters_qs = close_filters_qs.filter(city_id=entry.city_id)
                elif document.location_type == 'AREA' and entry.area_id:
                    close_filters_qs = close_filters_qs.filter(area_id=entry.area_id)
                elif document.location_type == 'SUPERSTOCKIST' and entry.superstockist_id:
                    close_filters_qs = close_filters_qs.filter(superstockist_id=entry.superstockist_id)
                elif document.location_type == 'DISTRIBUTOR' and entry.distributor_id:
                    close_filters_qs = close_filters_qs.filter(distributor_id=entry.distributor_id)
                elif document.location_type == 'RETAILER' and entry.retailer_id:
                    close_filters_qs = close_filters_qs.filter(retailer_id=entry.retailer_id)
                elif document.location_type == 'BASE':
                    # For BASE prices, close other BASE prices
                    close_filters_qs = close_filters_qs.filter(
                        state__isnull=True,
                        city__isnull=True,
                        area__isnull=True,
                        superstockist__isnull=True,
                        distributor__isnull=True,
                        retailer__isnull=True
                    )

                # Auto-close only if their document's effective_from is before this document's effective_from
                # We need to check the document dates, not the entry dates (in case they're out of sync)
                try:
                    closed_documents = set()  # Track which documents have affected entries
                    for other_price in close_filters_qs:
                        if other_price.document and other_price.document.effective_from <= document.effective_from and other_price.document_id != document.id:
                            other_price.effective_to = previous_day
                            other_price.save()
                            auto_closed_total += 1
                            closed_documents.add(other_price.document.id)

                    if closed_documents:
                        # Check each document - only update document effective_to if ALL its entries are now closed
                        for doc_id in closed_documents:
                            affected_doc = PriceBookDocument.objects.filter(id=doc_id).first()
                            if affected_doc:
                                # Count ongoing entries in this document
                                ongoing_count = PriceBook.objects.filter(
                                    document_id=doc_id,
                                    is_deleted=False,
                                    effective_to__isnull=True
                                ).count()

                                if ongoing_count == 0:
                                    # All entries closed - update document effective_to
                                    affected_doc.effective_to = previous_day
                                    affected_doc.save()
                                else:
                                    pass
                except Exception as e:
                    import traceback
                    traceback.print_exc()

        # Initialize counters
        updated_count = 0
        created_count = 0

        # Handle price updates if provided
        prices_data = request.data.get('prices', [])
        bulk_adjustment = request.data.get('bulk_adjustment', None)

        # Apply bulk adjustment to prices if provided
        if bulk_adjustment and prices_data:
            from decimal import Decimal, ROUND_HALF_UP
            adj_type = bulk_adjustment.get('adjustment_type')
            upd_type = bulk_adjustment.get('update_type')
            adj_value = Decimal(str(bulk_adjustment.get('adjustment_value', 0)))

            if adj_value and adj_type and upd_type:
                skipped_items = []
                for price_entry in prices_data:
                    current_price = Decimal(str(price_entry.get('selling_price', 0)))
                    item_id = price_entry.get('item_id', 'unknown')

                    if current_price == 0:
                        if adj_type == 'percentage':
                            skipped_items.append({'item_id': item_id, 'reason': 'Cannot apply percentage adjustment on zero selling price'})
                            continue
                        if upd_type == 'decrease_by':
                            skipped_items.append({'item_id': item_id, 'reason': 'Cannot decrease zero selling price'})
                            continue
                        price_entry['selling_price'] = str(adj_value)
                        continue

                    if adj_type == 'percentage':
                        delta = (current_price * adj_value / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    else:
                        delta = adj_value

                    new_price = (current_price + delta) if upd_type == 'increase_by' else (current_price - delta)

                    if new_price < 0:
                        skipped_items.append({'item_id': item_id, 'reason': f'Adjustment would result in negative price ({new_price}). Current price: {current_price}'})
                        continue

                    price_entry['selling_price'] = str(new_price)

                if skipped_items:
                    return Response({
                        'error': 'Bulk adjustment could not be applied',
                        'skipped_items': skipped_items
                    }, status=status.HTTP_400_BAD_REQUEST)

        if prices_data:
            # Get company
            company = Company.objects.filter(is_deleted=False).first()
            if not company:
                return Response(
                    {'error': 'No active company found'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Map location_type to field names
            location_field_map = {
                'STATE': 'state_id',
                'CITY': 'city_id',
                'AREA': 'area_id',
                'SUPERSTOCKIST': 'superstockist_id',
                'DISTRIBUTOR': 'distributor_id',
                'RETAILER': 'retailer_id',
            }

            # Determine price_type from location_type
            if document.location_type in ['STATE', 'CITY', 'AREA']:
                price_type = 'GEOGRAPHIC'
            elif document.location_type in ['SUPERSTOCKIST', 'DISTRIBUTOR', 'RETAILER']:
                price_type = 'CHANNEL_PARTNER'
            else:
                price_type = 'BASE'

            for price_data in prices_data:
                item_id = price_data.get('item_id')
                location_id = price_data.get('location_id')
                selling_price = price_data.get('selling_price', '0')

                if not item_id:
                    continue

                # Build filter for existing price
                filters = {
                    'item_id': item_id,
                    'document': document,
                    'is_deleted': False
                }

                # Add location filter
                if document.location_type != 'BASE' and location_id:
                    location_field = location_field_map.get(document.location_type)
                    if location_field:
                        filters[location_field] = location_id

                # Prepare defaults with parent location IDs for hierarchy validation
                defaults = {
                    'company': company,
                    'price_type': price_type,
                    'selling_price': selling_price,
                    'base_price': '0',
                    'mrp': '0',
                    'effective_from': document.effective_from,
                    'effective_to': document.effective_to,
                    'is_active': True,
                }

                # Add location fields with parent IDs for GEOGRAPHIC types
                if document.location_type != 'BASE' and location_id:
                    location_field = location_field_map.get(document.location_type)
                    if location_field:
                        defaults[location_field] = location_id

                        # Set parent location IDs to satisfy model validation
                        if document.location_type == 'CITY':
                            from .models import City
                            city = City.objects.filter(id=location_id).select_related('state').first()
                            if city and city.state:
                                defaults['state'] = city.state
                        elif document.location_type == 'AREA':
                            from .models import Area
                            area = Area.objects.filter(id=location_id).select_related('city__state').first()
                            if area:
                                if area.city:
                                    defaults['city'] = area.city
                                    if area.city.state:
                                        defaults['state'] = area.city.state

                # Update or create price entry
                price_entry, created = PriceBook.objects.update_or_create(
                    **filters,
                    defaults=defaults
                )

                # If newly created, auto-close previous ongoing prices
                if created:
                    previous_day = document.effective_from - timedelta(days=1)

                    close_filters = {
                        'item_id': item_id,
                        'effective_to__isnull': True,
                        'is_deleted': False
                    }

                    # Exclude the current entry we just created
                    close_filters_qs = PriceBook.objects.filter(**close_filters).exclude(id=price_entry.id)

                    # Add location filter to match the same granularity
                    if document.location_type != 'BASE' and location_id:
                        location_field = location_field_map.get(document.location_type)
                        if location_field:
                            close_filters_qs = close_filters_qs.filter(**{location_field: location_id})
                    elif document.location_type == 'BASE':
                        # For BASE prices, close other BASE prices (no location fields)
                        close_filters_qs = close_filters_qs.filter(
                            state__isnull=True,
                            city__isnull=True,
                            area__isnull=True,
                            superstockist__isnull=True,
                            distributor__isnull=True,
                            retailer__isnull=True
                        )

                    # Auto-close only if the new effective_from is after their effective_from
                    closed_documents = set()
                    for other_price in close_filters_qs.filter(effective_from__lt=document.effective_from):
                        other_price.effective_to = previous_day
                        other_price.save()
                        if other_price.document:
                            closed_documents.add(other_price.document.id)

                    auto_closed = len(closed_documents)

                    if closed_documents:
                        # Check each document - only update document effective_to if ALL its entries are now closed
                        for doc_id in closed_documents:
                            affected_doc = PriceBookDocument.objects.filter(id=doc_id).first()
                            if affected_doc:
                                # Count ongoing entries in this document
                                ongoing_count = PriceBook.objects.filter(
                                    document_id=doc_id,
                                    is_deleted=False,
                                    effective_to__isnull=True
                                ).count()

                                if ongoing_count == 0:
                                    # All entries closed - update document effective_to
                                    affected_doc.effective_to = previous_day
                                    affected_doc.save()
                                else:
                                    pass

                    if auto_closed > 0:
                        pass

                    created_count += 1
                else:
                    updated_count += 1

            # Update total entries count
            document.total_entries = PriceBook.objects.filter(
                document=document,
                is_deleted=False
            ).count()
            document.save()
            if document.status == 'DRAFT':
                _set_draft_authorization(document)

        # Return updated document
        serializer = PriceBookDocumentDetailSerializer(document)
        return Response({
            'success': True,
            'message': (
                'Document updated successfully. '
                f'{updated_count} entries updated, {created_count} entries created.'
            ),
            'document': serializer.data,
            'updated_count': updated_count,
            'created_count': created_count
        }, status=status.HTTP_200_OK)


class GeneratePriceBookDocumentNumber(APIView):
    """
    Generate next price book document number
    GET /api/masters/price-books/generate-document-number/

    Returns:
    {
        "document_number": "PB-25-26-1",
        "financial_year": "25-26"
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from .models import PriceBookDocument
        document_number = PriceBookDocument.generate_document_number()

        # Extract FY from document number
        import re
        match = re.search(r'PB-(\d{2}-\d{2})-', document_number)
        fy = match.group(1) if match else ''

        return Response({
            'document_number': document_number,
            'financial_year': fy
        }, status=status.HTTP_200_OK)


class PriceBookBulkCreate(APIView):
    """
    Bulk create/update price book entries with document header

    POST /api/masters/price-books/bulk-create/
    {
        "document_number": "PB-25-26-1",
        "document_date": "2026-01-07",
        "location_type": "STATE",
        "effective_from": "2026-01-01",
        "effective_to": "2026-12-31",
        "remarks": "",
        "prices": [
            {
                "item_id": 1,
                "location_id": 10,
                "base_price": "100.00",
                "selling_price": "120.00",
                "mrp": "150.00",
                "is_active": true
            },
            ...
        ]
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from .models import PriceBookDocument, PriceBook

        # Extract document and prices data
        document_number = request.data.get('document_number')
        document_date = request.data.get('document_date')
        location_type = request.data.get('location_type')
        effective_from = request.data.get('effective_from')
        effective_to = request.data.get('effective_to')
        remarks = request.data.get('remarks', '')
        cp_filter_state = request.data.get('cp_filter_state')
        cp_filter_city = request.data.get('cp_filter_city')
        cp_filter_area = request.data.get('cp_filter_area')
        prices_data = request.data.get('prices', [])
        save_as_draft = request.data.get('save_as_draft', False)  # New parameter
        selected_categories = request.data.get('selected_categories', [])
        selected_brands = request.data.get('selected_brands', [])
        bulk_adjustment = request.data.get('bulk_adjustment', None)

        # Apply bulk adjustment to prices if provided
        if bulk_adjustment and prices_data:
            from decimal import Decimal, ROUND_HALF_UP
            adj_type = bulk_adjustment.get('adjustment_type')  # 'percentage' or 'amount'
            upd_type = bulk_adjustment.get('update_type')      # 'increase_by' or 'decrease_by'
            adj_value = Decimal(str(bulk_adjustment.get('adjustment_value', 0)))

            if adj_value and adj_type and upd_type:
                skipped_items = []
                for price_entry in prices_data:
                    current_price = Decimal(str(price_entry.get('selling_price', 0)))
                    item_id = price_entry.get('item_id', 'unknown')

                    if current_price == 0:
                        if adj_type == 'percentage':
                            skipped_items.append({
                                'item_id': item_id,
                                'reason': 'Cannot apply percentage adjustment on zero selling price'
                            })
                            continue
                        if upd_type == 'decrease_by':
                            skipped_items.append({
                                'item_id': item_id,
                                'reason': 'Cannot decrease zero selling price'
                            })
                            continue
                        # amount + increase_by on zero price: set price = adjustment value
                        price_entry['selling_price'] = str(adj_value)
                        continue

                    if adj_type == 'percentage':
                        delta = (current_price * adj_value / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    else:
                        delta = adj_value

                    if upd_type == 'increase_by':
                        new_price = current_price + delta
                    else:
                        new_price = current_price - delta

                    if new_price < 0:
                        skipped_items.append({
                            'item_id': item_id,
                            'reason': f'Adjustment would result in negative price ({new_price}). Current price: {current_price}'
                        })
                        continue

                    price_entry['selling_price'] = str(new_price)

                if skipped_items:
                    return Response({
                        'error': 'Bulk adjustment could not be applied',
                        'skipped_items': skipped_items
                    }, status=status.HTTP_400_BAD_REQUEST)

        # Normalize dates to date objects so arithmetic works
        from datetime import datetime
        if isinstance(document_date, str):
            document_date = datetime.strptime(document_date, '%Y-%m-%d').date()
        if isinstance(effective_from, str):
            effective_from = datetime.strptime(effective_from, '%Y-%m-%d').date()
        if isinstance(effective_to, str):
            effective_to = datetime.strptime(effective_to, '%Y-%m-%d').date()

        # Validation
        if not document_number:
            return Response(
                {'error': 'document_number is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not document_date:
            return Response(
                {'error': 'document_date is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not location_type:
            return Response(
                {'error': 'location_type is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not effective_from:
            return Response(
                {'error': 'effective_from is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not prices_data or not isinstance(prices_data, list):
            return Response(
                {'error': 'prices array is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Channel partner filters apply only when location type is a channel partner
        if location_type not in ['SUPERSTOCKIST', 'DISTRIBUTOR', 'RETAILER']:
            cp_filter_state = None
            cp_filter_city = None
            cp_filter_area = None

        try:
            # Determine document status
            doc_status = PriceBookDocument.Status.DRAFT if save_as_draft else PriceBookDocument.Status.ACTIVE

            # Check for existing draft if creating new draft
            if save_as_draft:
                existing_draft = PriceBookDocument.objects.filter(
                    location_type=location_type,
                    status=PriceBookDocument.Status.DRAFT,
                    is_deleted=False
                ).first()

                if existing_draft and existing_draft.document_number != document_number:
                    return Response({
                        'error': (
                            f'A draft already exists for {location_type}. '
                            f'Document: {existing_draft.document_number}'
                        ),
                        'existing_draft': {
                            'id': existing_draft.id,
                            'document_number': existing_draft.document_number,
                            'document_date': existing_draft.document_date
                        }
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Create or get document
            document, created = PriceBookDocument.objects.get_or_create(
                document_number=document_number,
                defaults={
                    'document_date': document_date,
                    'location_type': location_type,
                    'status': doc_status,
                    'cp_filter_state_id': cp_filter_state or None,
                    'cp_filter_city_id': cp_filter_city or None,
                    'cp_filter_area_id': cp_filter_area or None,
                    'effective_from': effective_from,
                    'effective_to': effective_to,
                    'remarks': remarks,
                    'selected_categories': selected_categories,
                    'selected_brands': selected_brands,
                    'total_entries': 0
                }
            )

            if not created:
                # Update existing document
                document.document_date = document_date
                document.location_type = location_type
                document.status = doc_status
                document.cp_filter_state_id = cp_filter_state or None
                document.cp_filter_city_id = cp_filter_city or None
                document.cp_filter_area_id = cp_filter_area or None
                document.effective_from = effective_from
                document.effective_to = effective_to
                document.remarks = remarks
                document.selected_categories = selected_categories
                document.selected_brands = selected_brands
                document.save()
            if document.status == PriceBookDocument.Status.DRAFT:
                _set_draft_authorization(document)

            created_count = 0
            updated_count = 0
            errors = []

            # Get company for price book entries
            from .models import Company
            company = Company.objects.filter(is_deleted=False).first()
            if not company:
                return Response(
                    {'error': 'No active company found'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Map location_type to field names
            location_field_map = {
                'STATE': 'state_id',
                'CITY': 'city_id',
                'AREA': 'area_id',
                'SUPERSTOCKIST': 'superstockist_id',
                'DISTRIBUTOR': 'distributor_id',
                'RETAILER': 'retailer_id',
            }

            # Determine price_type from location_type
            if location_type in ['STATE', 'CITY', 'AREA']:
                price_type = 'GEOGRAPHIC'
            elif location_type in ['SUPERSTOCKIST', 'DISTRIBUTOR', 'RETAILER']:
                price_type = 'CHANNEL_PARTNER'
            else:
                price_type = 'BASE'

            for idx, price_data in enumerate(prices_data):
                try:
                    item_id = price_data.get('item_id')
                    location_id = price_data.get('location_id')

                    if not item_id:
                        errors.append({
                            'index': idx,
                            'error': 'item_id is required'
                        })
                        continue

                    # Build filter for existing price
                    filters = {
                        'item_id': item_id,
                        'document': document,
                        'is_deleted': False
                    }

                    # Add location filter
                    if location_type != 'BASE' and location_id:
                        location_field = location_field_map.get(location_type)
                        if location_field:
                            filters[location_field] = location_id

                    existing_price = PriceBook.objects.filter(**filters).first()

                    # Build price data
                    price_book_data = {
                        'item_id': item_id,
                        'company_id': company.id,
                        'price_type': price_type,
                        'base_price': price_data.get('base_price'),
                        'selling_price': price_data.get('selling_price'),
                        'mrp': price_data.get('mrp'),
                        'effective_from': effective_from,
                        'effective_to': effective_to,
                        'is_active': price_data.get('is_active', True),
                        'document_id': document.id
                    }

                    # Generate unique code if creating new entry
                    if not existing_price:
                        # Generate code: PB-{ITEM_CODE}-{DOC_INCREMENT}-{ENTRY_NUMBER}
                        from .models import Item
                        try:
                            item = Item.objects.get(id=item_id)
                            doc_increment = document_number.split('-')[-1]
                            entry_number = idx + 1
                            price_book_data['code'] = f"PB-{item.code}-{doc_increment}-{entry_number}"
                        except Item.DoesNotExist:
                            # Fallback to index-based code
                            price_book_data['code'] = f"PB-UNKNOWN-{idx + 1}"

                    # Add location field with parent locations for hierarchy validation
                    if location_type != 'BASE' and location_id:
                        location_field = location_field_map.get(location_type)
                        if location_field:
                            price_book_data[location_field] = location_id

                            # For GEOGRAPHIC types, also set parent location IDs to satisfy model validation
                            if location_type == 'CITY':
                                from .models import City
                                city = City.objects.filter(id=location_id).select_related('state').first()
                                if city and city.state:
                                    price_book_data['state_id'] = city.state_id
                            elif location_type == 'AREA':
                                from .models import Area
                                area = Area.objects.filter(id=location_id).select_related('city__state').first()
                                if area:
                                    if area.city:
                                        price_book_data['city_id'] = area.city_id
                                        if area.city.state:
                                            price_book_data['state_id'] = area.city.state_id

                    if existing_price:
                        # Update existing
                        serializer = PriceBookSerializer(existing_price, data=price_book_data, partial=True)
                        if serializer.is_valid():
                            serializer.save()
                            updated_count += 1
                        else:
                            errors.append({
                                'index': idx,
                                'item_id': item_id,
                                'errors': serializer.errors
                            })
                    else:
                        # Auto-close previous ongoing price books ONLY if this is an ACTIVE document (not draft)
                        if document.status == PriceBookDocument.Status.ACTIVE:
                            # Find all ongoing prices (effective_to = null) with same item and location
                            previous_day = effective_from - timedelta(days=1)

                            close_filters = {
                                'item_id': item_id,
                                'effective_to__isnull': True,
                                'is_deleted': False
                            }

                            # Add location filter to match the same granularity
                            if location_type != 'BASE' and location_id:
                                location_field = location_field_map.get(location_type)
                                if location_field:
                                    close_filters[location_field] = location_id
                            elif location_type == 'BASE':
                                # For BASE prices, close other BASE prices (no location fields)
                                close_filters['state__isnull'] = True
                                close_filters['city__isnull'] = True
                                close_filters['area__isnull'] = True
                                close_filters['superstockist__isnull'] = True
                                close_filters['distributor__isnull'] = True
                                close_filters['retailer__isnull'] = True

                            # Auto-close only if their document's effective_from is before this
                            # document's effective_from
                            ongoing_prices = PriceBook.objects.filter(**close_filters)
                            auto_closed_count = 0
                            closed_documents = set()

                            try:
                                for other_price in ongoing_prices:
                                    if other_price.document and other_price.document.effective_from <= effective_from and other_price.document_id != document.id:
                                        other_price.effective_to = previous_day
                                        other_price.save()
                                        auto_closed_count += 1
                                        closed_documents.add(other_price.document.id)

                                if closed_documents:
                                    # Check each document - only update document effective_to if ALL its
                                    # entries are now closed
                                    for doc_id in closed_documents:
                                        affected_doc = PriceBookDocument.objects.filter(id=doc_id).first()
                                        if affected_doc:
                                            # Count ongoing entries in this document
                                            ongoing_count = PriceBook.objects.filter(
                                                document_id=doc_id,
                                                is_deleted=False,
                                                effective_to__isnull=True
                                            ).count()

                                            if ongoing_count == 0:
                                                # All entries closed - update document effective_to
                                                affected_doc.effective_to = previous_day
                                                affected_doc.save()
                                            else:
                                                pass

                                if auto_closed_count > 0:
                                    pass

                            except Exception as e:
                                import traceback
                                traceback.print_exc()

                        # Create new
                        serializer = PriceBookSerializer(data=price_book_data)
                        if serializer.is_valid():
                            serializer.save()
                            created_count += 1
                        else:
                            errors.append({
                                'index': idx,
                                'item_id': item_id,
                                'errors': serializer.errors
                            })

                except Exception as e:
                    errors.append({
                        'index': idx,
                        'item_id': price_data.get('item_id'),
                        'error': str(e)
                    })

            # Update document total_entries
            document.total_entries = created_count + updated_count
            document.save()

            response_data = {
                'success': len(errors) == 0,
                'document_number': document_number,
                'created': created_count,
                'updated': updated_count,
                'total': created_count + updated_count,
                'message': f'{created_count + updated_count} price book entries saved successfully'
            }

            if errors:
                response_data['errors'] = errors
                response_data['message'] = (
                    f'Processed {created_count + updated_count} entries with '
                    f'{len(errors)} errors'
                )

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            import logging
            import traceback
            logging.exception('Finalize failed', exc_info=True)
            traceback_str = traceback.format_exc()
            return Response(
                {'error': str(e), 'trace': traceback_str},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PriceBookDocumentFinalize(APIView):
    """
    Finalize a draft price book document

    POST /api/masters/price-book-documents/{document_id}/finalize/

    Changes status from DRAFT to ACTIVE and triggers auto-close logic
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, document_id):
        try:
            from datetime import datetime
            from django.db import transaction

            document_id = str(document_id)

            # Get the document
            try:
                document = PriceBookDocument.objects.get(id=document_id, is_deleted=False)
            except PriceBookDocument.DoesNotExist:
                return Response(
                    {'error': f'Price book document not found for id {document_id}'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check if already finalized
            if document.status != 'DRAFT':
                return Response(
                    {'error': f'Document is already {document.status}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate that document has entries
            if not document.price_entries.filter(is_deleted=False).exists():
                return Response(
                    {'error': 'Cannot finalize document with no entries'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not document.effective_from:
                return Response(
                    {'error': 'Document effective_from is missing'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            with transaction.atomic():
                # Update status to ACTIVE
                document.status = 'ACTIVE'
                document.save()

                # Now trigger auto-close logic
                # Get all entries from this document
                entries = list(document.price_entries.filter(is_deleted=False))

                # Parse effective_from
                effective_from = document.effective_from
                if isinstance(effective_from, str):
                    effective_from = datetime.strptime(effective_from, '%Y-%m-%d').date()

                # Map document location_type to the relevant field on PriceBook
                location_field_map = {
                    'STATE': 'state_id',
                    'CITY': 'city_id',
                    'AREA': 'area_id',
                    'SUPERSTOCKIST': 'superstockist_id',
                    'DISTRIBUTOR': 'distributor_id',
                    'RETAILER': 'retailer_id',
                }

                field_name_for_type = location_field_map.get(document.location_type)

                for entry in entries:
                    item_id = str(entry.item_id)
                    location_type = document.location_type

                    # Determine location filter
                    if location_type == 'BASE':
                        location_filter = {
                            'state__isnull': True,
                            'city__isnull': True,
                            'area__isnull': True,
                            'superstockist__isnull': True,
                            'distributor__isnull': True,
                            'retailer__isnull': True,
                        }
                        location_label = 'BASE'
                    else:
                        if not field_name_for_type:
                            return Response(
                                {'error': f'Unsupported location_type {location_type}'},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                        attr_name = field_name_for_type.replace('_id', '')
                        location_value = getattr(entry, attr_name, None)
                        if not location_value:
                            # Skip if location missing
                            continue
                        location_id_value = str(location_value.id if hasattr(location_value, 'id') else location_value)
                        location_filter = {field_name_for_type: location_id_value}
                        location_label = f"{attr_name}={location_id_value}"

                    # Debug log for each entry being processed
                    import logging
                    logging.info('Finalize closing superseded', extra={
                        'item_id': item_id,
                        'location_type': location_type,
                        'location_filter': location_filter,
                        'location_label': location_label,
                        'document_id': str(document.id),
                    })

                    superseded_entries = PriceBook.objects.filter(
                        item_id=item_id,
                        is_deleted=False,
                        effective_to__isnull=True,
                        **location_filter
                    ).exclude(
                        document=document
                    ).exclude(
                        document__status='DRAFT'
                    )

                    # Close these entries
                    for old_entry in superseded_entries:
                        old_entry.effective_to = effective_from
                        old_entry.save()

                    # Mark affected documents as CLOSED if no open entries remain
                    affected_docs = set(old_entry.document for old_entry in superseded_entries if old_entry.document)
                    for doc in affected_docs:
                        ongoing_entries = PriceBook.objects.filter(
                            document=doc,
                            is_deleted=False,
                            effective_to__isnull=True
                        ).count()

                        if ongoing_entries == 0 and doc.status == 'ACTIVE':
                            doc.status = 'CLOSED'
                            doc.save()

                # Note: PriceBookHistory tracks individual price books, not documents.
                # For finalize, we skip history to avoid schema mismatch; add a document-level
                # history model if needed in the future.

            return Response({
                'success': True,
                'message': f'Document {document.document_number} finalized successfully',
                'document_number': document.document_number,
                'status': document.status
            }, status=status.HTTP_200_OK)

        except Exception as e:
            import logging
            import traceback
            logging.exception('Finalize failed', exc_info=True)
            traceback_str = traceback.format_exc()
            return Response(
                {'error': str(e), 'trace': traceback_str},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PriceBookDocumentDuplicateAsDraft(APIView):
    """
    Duplicate an existing price book document as a draft

    POST /api/masters/price-book-documents/{document_id}/duplicate-as-draft/

    Creates a new document with DRAFT status copying all entries
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, document_id):
        try:
            from django.db import transaction

            # Get the source document
            try:
                source_doc = PriceBookDocument.objects.get(id=document_id, is_deleted=False)
            except PriceBookDocument.DoesNotExist:
                return Response(
                    {'error': 'Source document not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get all entries from source document
            source_entries = list(source_doc.price_entries.filter(is_deleted=False))

            if not source_entries:
                return Response(
                    {'error': 'Source document has no entries to duplicate'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            with transaction.atomic():
                # Generate new document number using the same method as the model
                new_number = PriceBookDocument.generate_document_number()

                # Create new document
                new_doc = PriceBookDocument.objects.create(
                    document_number=new_number,
                    document_date=timezone.now().date(),
                    location_type=source_doc.location_type,
                    cp_filter_state=source_doc.cp_filter_state,
                    cp_filter_city=source_doc.cp_filter_city,
                    cp_filter_area=source_doc.cp_filter_area,
                    effective_from=source_doc.effective_from,
                    status='DRAFT',
                    total_entries=0
                )

                # Copy all entries
                created_count = 0
                for source_entry in source_entries:
                    PriceBook.objects.create(
                        document=new_doc,
                        company=source_entry.company,
                        item=source_entry.item,
                        price_type=source_entry.price_type,
                        state=source_entry.state,
                        city=source_entry.city,
                        area=source_entry.area,
                        superstockist=source_entry.superstockist,
                        distributor=source_entry.distributor,
                        retailer=source_entry.retailer,
                        base_price=source_entry.base_price,
                        selling_price=source_entry.selling_price,
                        mrp=source_entry.mrp,
                        discount_percentage=source_entry.discount_percentage,
                        effective_from=source_entry.effective_from,
                        effective_to=None,
                        is_active=True
                    )
                    created_count += 1

                # Update document total_entries
                new_doc.total_entries = created_count
                new_doc.save()

            return Response({
                'success': True,
                'message': f'Document duplicated successfully as {new_doc.document_number}',
                'document_number': new_doc.document_number,
                'document_id': str(new_doc.id),
                'entries_copied': created_count
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PriceBookLoadGridWithParents(APIView):
    """
    Optimized endpoint to load price grid with parent prices in a single query

    POST /api/masters/price-books/load-grid-with-parents/
    {
        "location_type": "CITY",
        "item_ids": [1, 2, 3],
        "location_ids": [10, 11, 12],
        "effective_from": "2026-01-11",
        "channel_config": {
            "enable_superstockist": true,
            "enable_distributor": true,
            "enable_retailer": true
        }
    }

    Response: {
        "current_prices": {
            "1-10": "150.00",
            "1-11": "155.00",
            ...
        },
        "parent_prices": {
            "1-10": {
                "price": "140.00",
                "level": "STATE",
                "location_id": 5,
                "location_name": "Karnataka"
            },
            ...
        }
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from datetime import datetime
        from django.db.models import Q

        # Extract request data
        location_type = request.data.get('location_type')
        item_ids = request.data.get('item_ids', [])
        location_ids = request.data.get('location_ids', [])
        effective_from = request.data.get('effective_from')
        channel_config = request.data.get('channel_config', {})

        # Normalize IDs: items and locations may be UUID strings, keep as strings
        def to_str_list(values):
            safe_list = []
            for v in values:
                if v is None:
                    continue
                safe_list.append(str(v))
            return safe_list

        item_ids = to_str_list(item_ids)  # keep UUIDs intact
        location_ids = to_str_list(location_ids)

        # Validation
        if not location_type:
            return Response({'error': 'location_type is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not item_ids:
            return Response({'current_prices': {}, 'parent_prices': {}}, status=status.HTTP_200_OK)
        if not effective_from:
            return Response({'error': 'effective_from is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Parse date
        if isinstance(effective_from, str):
            effective_from = datetime.strptime(effective_from, '%Y-%m-%d').date()

        # Helper to pick the best price entry: prefer open-ended (effective_to is null); otherwise latest effective_from; then latest created_on
        def choose_best(existing, candidate):
            if existing is None:
                return candidate
            if existing.effective_to and candidate.effective_to is None:
                return candidate
            if existing.effective_to is None and candidate.effective_to:
                return existing
            if candidate.effective_from and existing.effective_from:
                if candidate.effective_from > existing.effective_from:
                    return candidate
                if candidate.effective_from < existing.effective_from:
                    return existing
                # Same effective_from: prefer the most recently created record
                if hasattr(candidate, 'created_on') and hasattr(existing, 'created_on'):
                    if candidate.created_on and existing.created_on:
                        return candidate if candidate.created_on > existing.created_on else existing
                return candidate
            return existing

        # Base queryset for active prices
        # Exclude prices from DRAFT documents
        def get_price_queryset(item_ids, effective_from):
            return PriceBook.objects.filter(
                item_id__in=item_ids,
                is_deleted=False,
                is_active=True,
                effective_from__lte=effective_from
            ).filter(
                Q(effective_to__isnull=True) | Q(effective_to__gte=effective_from)
            ).exclude(
                document__status='DRAFT'
            ).select_related('item', 'state', 'city', 'area', 'superstockist', 'distributor', 'retailer')

        current_prices = {}
        parent_prices = {}

        # Fetch current location type prices
        if location_type == 'BASE':
            # BASE prices - no location, no parent
            prices = get_price_queryset(item_ids, effective_from).filter(
                price_type='BASE',
                state__isnull=True,
                city__isnull=True,
                area__isnull=True
            )
            base_current_map = {}
            for price in prices:
                key = f"{price.item_id}-"
                base_current_map[key] = choose_best(base_current_map.get(key), price)
            for key, val in base_current_map.items():
                current_prices[key] = str(val.selling_price)

        elif location_type == 'STATE':
            # STATE prices - parent is BASE
            if not location_ids:
                return Response({'current_prices': {}, 'parent_prices': {}})

            # Fetch current STATE prices
            state_prices = get_price_queryset(item_ids, effective_from).filter(
                price_type='GEOGRAPHIC',
                state_id__in=location_ids,
                city__isnull=True,
                area__isnull=True
            )
            state_current_map = {}
            for price in state_prices:
                key = f"{price.item_id}-{price.state_id}"
                state_current_map[key] = choose_best(state_current_map.get(key), price)
            for key, val in state_current_map.items():
                current_prices[key] = str(val.selling_price)

            # Fetch parent BASE prices
            base_prices = get_price_queryset(item_ids, effective_from).filter(
                price_type='BASE'
            )
            base_price_map = {str(bp.item_id): bp for bp in base_prices}
            for item_id in item_ids:
                base_price = base_price_map.get(str(item_id))
                if base_price:
                    for location_id in location_ids:
                        key = f"{item_id}-{location_id}"
                        parent_prices[key] = {
                            'price': str(base_price.selling_price),
                            'level': 'BASE',
                            'location_id': None,
                            'location_name': 'Base Price'
                        }

        elif location_type == 'CITY':
            # CITY prices - parent is STATE
            if not location_ids:
                return Response({'current_prices': {}, 'parent_prices': {}})

            # Fetch cities with their states in one query
            from .models import City
            cities = City.objects.filter(
                id__in=location_ids).select_related('state').values(
                'id', 'state_id', 'state__name')
            city_state_map = {str(c['id']): {'state_id': str(c['state_id']),
                                             'state_name': c['state__name']} for c in cities}
            try:
                pass
            except Exception:
                pass

            # Fetch current CITY prices
            city_prices = get_price_queryset(item_ids, effective_from).filter(
                price_type='GEOGRAPHIC',
                city_id__in=location_ids,
                area__isnull=True
            )
            city_current_map = {}
            for price in city_prices:
                key = f"{price.item_id}-{price.city_id}"
                city_current_map[key] = choose_best(city_current_map.get(key), price)
            for key, val in city_current_map.items():
                current_prices[key] = str(val.selling_price)

            # Fetch parent STATE prices
            state_ids = list(set([c['state_id'] for c in city_state_map.values()]))
            state_prices = get_price_queryset(item_ids, effective_from).filter(
                price_type='GEOGRAPHIC',
                state_id__in=state_ids,
                city__isnull=True
            )

            # Map state prices by item and state (ensure string keys)
            state_price_map = {}
            for price in state_prices:
                state_price_map[f"{str(price.item_id)}-{str(price.state_id)}"] = price
            try:
                pass
            except Exception:
                pass

            # Fetch BASE prices as fallback
            base_prices_qs = get_price_queryset(item_ids, effective_from).filter(price_type='BASE')
            base_price_map = {str(bp.item_id): bp for bp in base_prices_qs}

            # Fetch any available state prices as additional fallback (for items with no specific state price)
            any_state_prices = get_price_queryset(item_ids, effective_from).filter(
                price_type='GEOGRAPHIC',
                city__isnull=True,
                area__isnull=True
            ).select_related('state').order_by('item_id', '-effective_from')
            # Group by item to get one fallback price per item
            any_state_price_map = {}
            for price in any_state_prices:
                item_key = str(price.item_id)
                if item_key not in any_state_price_map:
                    any_state_price_map[item_key] = price

            # Match parent prices to city locations
            for item_id in item_ids:
                for city_id in location_ids:
                    key = f"{item_id}-{city_id}"
                    city_info = city_state_map.get(city_id)
                    if city_info:
                        state_key = f"{item_id}-{city_info['state_id']}"
                        state_price = state_price_map.get(state_key)

                        if state_price:
                            # Specific state price exists - use it
                            parent_prices[key] = {
                                'price': str(state_price.selling_price),
                                'level': 'STATE',
                                'location_id': city_info['state_id'],
                                'location_name': city_info['state_name']
                            }
                        elif str(item_id) in base_price_map:
                            # BASE price exists - use it
                            parent_prices[key] = {
                                'price': str(base_price_map[str(item_id)].selling_price),
                                'level': 'BASE',
                                'location_id': None,
                                'location_name': 'Base Price'
                            }
                        elif str(item_id) in any_state_price_map:
                            # Fallback to any available state price as reference
                            fallback_price = any_state_price_map[str(item_id)]
                            parent_prices[key] = {
                                'price': str(fallback_price.selling_price),
                                'level': 'STATE',
                                'location_id': str(fallback_price.state_id) if fallback_price.state else None,
                                'location_name': f"{fallback_price.state.name if fallback_price.state else 'Other State'} (Reference)"
                            }
            try:
                pass
                for item_id in item_ids:
                    for city_id in location_ids:
                        key = f"{item_id}-{city_id}"
                        if key not in parent_prices:
                            missing.append(key)
                            if len(missing) >= 20:
                                break
                    if len(missing) >= 20:
                        break
                if missing:
                    pass
            except Exception:
                pass

        elif location_type == 'AREA':
            # AREA prices - parent is CITY
            if not location_ids:
                return Response({'current_prices': {}, 'parent_prices': {}})

            # Fetch areas with their cities and states
            from .models import Area
            areas = Area.objects.filter(id__in=location_ids).select_related('city', 'city__state').values(
                'id', 'city_id', 'city__name', 'city__state_id', 'city__state__name'
            )
            area_city_map = {
                str(a['id']): {
                    'city_id': str(a['city_id']),
                    'city_name': a['city__name'],
                    'state_id': str(a['city__state_id']),
                    'state_name': a['city__state__name']
                } for a in areas
            }

            # Fetch current AREA prices
            area_prices = get_price_queryset(item_ids, effective_from).filter(
                price_type='GEOGRAPHIC',
                area_id__in=location_ids
            )
            area_current_map = {}
            for price in area_prices:
                key = f"{price.item_id}-{price.area_id}"
                area_current_map[key] = choose_best(area_current_map.get(key), price)
            for key, val in area_current_map.items():
                current_prices[key] = str(val.selling_price)

            # Fetch parent CITY prices
            city_ids = list(set([a['city_id'] for a in area_city_map.values()]))
            city_prices = get_price_queryset(item_ids, effective_from).filter(
                price_type='GEOGRAPHIC',
                city_id__in=city_ids,
                area__isnull=True
            )
            city_price_map = {f"{str(price.item_id)}-{str(price.city_id)}": price for price in city_prices}

            # Fetch STATE and BASE prices as fallback
            state_ids = list(set([a['state_id'] for a in area_city_map.values()]))
            state_prices = get_price_queryset(item_ids, effective_from).filter(
                price_type='GEOGRAPHIC',
                state_id__in=state_ids,
                city__isnull=True
            )
            state_price_map = {f"{str(price.item_id)}-{str(price.state_id)}": price for price in state_prices}

            base_prices_qs = get_price_queryset(item_ids, effective_from).filter(price_type='BASE')
            base_price_map = {str(bp.item_id): bp for bp in base_prices_qs}

            # Match parent prices
            for item_id in item_ids:
                for area_id in location_ids:
                    key = f"{item_id}-{area_id}"
                    area_info = area_city_map.get(area_id)
                    if area_info:
                        # Try CITY first
                        city_key = f"{item_id}-{area_info['city_id']}"
                        city_price = city_price_map.get(city_key)

                        if city_price:
                            parent_prices[key] = {
                                'price': str(city_price.selling_price),
                                'level': 'CITY',
                                'location_id': area_info['city_id'],
                                'location_name': area_info['city_name']
                            }
                        else:
                            # Fallback to STATE
                            state_key = f"{item_id}-{area_info['state_id']}"
                            state_price = state_price_map.get(state_key)

                            if state_price:
                                parent_prices[key] = {
                                    'price': str(state_price.selling_price),
                                    'level': 'STATE',
                                    'location_id': area_info['state_id'],
                                    'location_name': area_info['state_name']
                                }
                            elif item_id in base_price_map:
                                parent_prices[key] = {
                                    'price': str(base_price_map[item_id].selling_price),
                                    'level': 'BASE',
                                    'location_id': None,
                                    'location_name': 'Base Price'
                                }

        elif location_type == 'SUPERSTOCKIST':
            # SUPERSTOCKIST prices - parent is AREA
            if not location_ids:
                return Response({'current_prices': {}, 'parent_prices': {}})

            # Fetch superstockists with their locations
            from .models import Superstockist
            superstockists = Superstockist.objects.filter(id__in=location_ids).select_related(
                'state', 'city', 'area'
            ).values('id', 'state_id', 'state__name', 'city_id', 'city__name', 'area_id', 'area__name')
            ss_location_map = {
                str(ss['id']): {
                    'area_id': str(ss['area_id']) if ss['area_id'] else None,
                    'area_name': ss['area__name'],
                    'city_id': str(ss['city_id']) if ss['city_id'] else None,
                    'city_name': ss['city__name'],
                    'state_id': str(ss['state_id']) if ss['state_id'] else None,
                    'state_name': ss['state__name']
                } for ss in superstockists
            }

            # Fetch current SUPERSTOCKIST prices
            ss_prices = get_price_queryset(item_ids, effective_from).filter(
                price_type='CHANNEL_PARTNER',
                superstockist_id__in=location_ids
            )
            ss_current_map = {}
            for price in ss_prices:
                key = f"{price.item_id}-{price.superstockist_id}"
                ss_current_map[key] = choose_best(ss_current_map.get(key), price)
            for key, val in ss_current_map.items():
                current_prices[key] = str(val.selling_price)

            # Fetch parent prices (AREA, CITY, STATE, BASE)
            area_ids = [ss['area_id'] for ss in ss_location_map.values() if ss['area_id']]
            city_ids = [ss['city_id'] for ss in ss_location_map.values() if ss['city_id']]
            state_ids = [ss['state_id'] for ss in ss_location_map.values() if ss['state_id']]

            area_prices = get_price_queryset(item_ids, effective_from).filter(
                price_type='GEOGRAPHIC', area_id__in=area_ids
            ) if area_ids else []
            area_price_map = {f"{str(price.item_id)}-{str(price.area_id)}": price for price in area_prices}

            city_prices = get_price_queryset(item_ids, effective_from).filter(
                price_type='GEOGRAPHIC', city_id__in=city_ids, area__isnull=True
            ) if city_ids else []
            city_price_map = {f"{str(price.item_id)}-{str(price.city_id)}": price for price in city_prices}

            state_prices = get_price_queryset(item_ids, effective_from).filter(
                price_type='GEOGRAPHIC', state_id__in=state_ids, city__isnull=True
            ) if state_ids else []
            state_price_map = {f"{str(price.item_id)}-{str(price.state_id)}": price for price in state_prices}

            base_prices_qs = get_price_queryset(item_ids, effective_from).filter(price_type='BASE')
            base_price_map = {str(bp.item_id): bp for bp in base_prices_qs}

            # Match parent prices with fallback
            for item_id in item_ids:
                for ss_id in location_ids:
                    key = f"{item_id}-{ss_id}"
                    ss_info = ss_location_map.get(ss_id)
                    if ss_info:
                        # Try AREA → CITY → STATE → BASE
                        if ss_info['area_id']:
                            area_key = f"{item_id}-{ss_info['area_id']}"
                            if area_key in area_price_map:
                                parent_prices[key] = {
                                    'price': str(area_price_map[area_key].selling_price),
                                    'level': 'AREA',
                                    'location_id': ss_info['area_id'],
                                    'location_name': ss_info['area_name']
                                }
                                continue

                        if ss_info['city_id']:
                            city_key = f"{item_id}-{ss_info['city_id']}"
                            if city_key in city_price_map:
                                parent_prices[key] = {
                                    'price': str(city_price_map[city_key].selling_price),
                                    'level': 'CITY',
                                    'location_id': ss_info['city_id'],
                                    'location_name': ss_info['city_name']
                                }
                                continue

                        if ss_info['state_id']:
                            state_key = f"{item_id}-{ss_info['state_id']}"
                            if state_key in state_price_map:
                                parent_prices[key] = {
                                    'price': str(state_price_map[state_key].selling_price),
                                    'level': 'STATE',
                                    'location_id': ss_info['state_id'],
                                    'location_name': ss_info['state_name']
                                }
                                continue

                        if item_id in base_price_map:
                            parent_prices[key] = {
                                'price': str(base_price_map[item_id].selling_price),
                                'level': 'BASE',
                                'location_id': None,
                                'location_name': 'Base Price'
                            }

        elif location_type == 'DISTRIBUTOR':
            # DISTRIBUTOR prices - parent is SUPERSTOCKIST (if enabled and linked) or AREA
            if not location_ids:
                return Response({'current_prices': {}, 'parent_prices': {}})

            from .models import Distributor
            distributors = Distributor.objects.filter(id__in=location_ids).select_related(
                'superstockist', 'state', 'city', 'area'
            ).values(
                'id', 'superstockist_id', 'state_id', 'state__name',
                'city_id', 'city__name', 'area_id', 'area__name'
            )
            dist_info_map = {
                str(d['id']): {
                    'superstockist_id': str(d['superstockist_id']) if d['superstockist_id'] else None,
                    'area_id': str(d['area_id']) if d['area_id'] else None,
                    'area_name': d['area__name'],
                    'city_id': str(d['city_id']) if d['city_id'] else None,
                    'city_name': d['city__name'],
                    'state_id': str(d['state_id']) if d['state_id'] else None,
                    'state_name': d['state__name']
                } for d in distributors
            }

            # Fetch current DISTRIBUTOR prices
            dist_prices = get_price_queryset(item_ids, effective_from).filter(
                price_type='CHANNEL_PARTNER',
                distributor_id__in=location_ids
            )
            dist_current_map = {}
            for price in dist_prices:
                key = f"{price.item_id}-{price.distributor_id}"
                dist_current_map[key] = choose_best(dist_current_map.get(key), price)
            for key, val in dist_current_map.items():
                current_prices[key] = str(val.selling_price)

            # Fetch parent prices
            enable_superstockist = channel_config.get('enable_superstockist', False)

            ss_ids = [d['superstockist_id'] for d in dist_info_map.values() if d['superstockist_id']]
            ss_prices = get_price_queryset(item_ids, effective_from).filter(
                price_type='CHANNEL_PARTNER', superstockist_id__in=ss_ids
            ) if ss_ids and enable_superstockist else []
            ss_price_map = {f"{str(price.item_id)}-{str(price.superstockist_id)}": price for price in ss_prices}

            # Geographic fallbacks
            area_ids = [d['area_id'] for d in dist_info_map.values() if d['area_id']]
            city_ids = [d['city_id'] for d in dist_info_map.values() if d['city_id']]
            state_ids = [d['state_id'] for d in dist_info_map.values() if d['state_id']]

            area_prices = get_price_queryset(item_ids, effective_from).filter(
                price_type='GEOGRAPHIC', area_id__in=area_ids
            ) if area_ids else []
            area_price_map = {f"{str(price.item_id)}-{str(price.area_id)}": price for price in area_prices}

            city_prices = get_price_queryset(item_ids, effective_from).filter(
                price_type='GEOGRAPHIC', city_id__in=city_ids, area__isnull=True
            ) if city_ids else []
            city_price_map = {f"{str(price.item_id)}-{str(price.city_id)}": price for price in city_prices}

            state_prices = get_price_queryset(item_ids, effective_from).filter(
                price_type='GEOGRAPHIC', state_id__in=state_ids, city__isnull=True
            ) if state_ids else []
            state_price_map = {f"{str(price.item_id)}-{str(price.state_id)}": price for price in state_prices}

            base_prices_qs = get_price_queryset(item_ids, effective_from).filter(price_type='BASE')
            base_price_map = {str(bp.item_id): bp for bp in base_prices_qs}

            # Match parent prices
            for item_id in item_ids:
                for dist_id in location_ids:
                    key = f"{item_id}-{dist_id}"
                    dist_info = dist_info_map.get(dist_id)
                    if dist_info:
                        # Try SUPERSTOCKIST → AREA → CITY → STATE → BASE
                        if enable_superstockist and dist_info['superstockist_id']:
                            ss_key = f"{item_id}-{dist_info['superstockist_id']}"
                            if ss_key in ss_price_map:
                                parent_prices[key] = {
                                    'price': str(ss_price_map[ss_key].selling_price),
                                    'level': 'SUPERSTOCKIST',
                                    'location_id': dist_info['superstockist_id'],
                                    'location_name': 'Superstockist'
                                }
                                continue

                        if dist_info['area_id']:
                            area_key = f"{item_id}-{dist_info['area_id']}"
                            if area_key in area_price_map:
                                parent_prices[key] = {
                                    'price': str(area_price_map[area_key].selling_price),
                                    'level': 'AREA',
                                    'location_id': dist_info['area_id'],
                                    'location_name': dist_info['area_name']
                                }
                                continue

                        if dist_info['city_id']:
                            city_key = f"{item_id}-{dist_info['city_id']}"
                            if city_key in city_price_map:
                                parent_prices[key] = {
                                    'price': str(city_price_map[city_key].selling_price),
                                    'level': 'CITY',
                                    'location_id': dist_info['city_id'],
                                    'location_name': dist_info['city_name']
                                }
                                continue

                        if dist_info['state_id']:
                            state_key = f"{item_id}-{dist_info['state_id']}"
                            if state_key in state_price_map:
                                parent_prices[key] = {
                                    'price': str(state_price_map[state_key].selling_price),
                                    'level': 'STATE',
                                    'location_id': dist_info['state_id'],
                                    'location_name': dist_info['state_name']
                                }
                                continue

                        if item_id in base_price_map:
                            parent_prices[key] = {
                                'price': str(base_price_map[item_id].selling_price),
                                'level': 'BASE',
                                'location_id': None,
                                'location_name': 'Base Price'
                            }

        elif location_type == 'RETAILER':
            # RETAILER prices - parent is DISTRIBUTOR (if enabled and linked) or SUPERSTOCKIST or AREA
            if not location_ids:
                return Response({'current_prices': {}, 'parent_prices': {}})

            from .models import Retailer
            retailers = Retailer.objects.filter(id__in=location_ids).select_related(
                'distributor', 'distributor__superstockist', 'state', 'city', 'area'
            ).values(
                'id', 'distributor_id', 'distributor__superstockist_id',
                'state_id', 'state__name', 'city_id', 'city__name', 'area_id', 'area__name'
            )
            retailer_info_map = {
                str(r['id']): {
                    'distributor_id': str(r['distributor_id']) if r['distributor_id'] else None,
                    'superstockist_id': (
                        str(r['distributor__superstockist_id'])
                        if r['distributor__superstockist_id'] else None
                    ),
                    'area_id': str(r['area_id']) if r['area_id'] else None,
                    'area_name': r['area__name'],
                    'city_id': str(r['city_id']) if r['city_id'] else None,
                    'city_name': r['city__name'],
                    'state_id': str(r['state_id']) if r['state_id'] else None,
                    'state_name': r['state__name']
                } for r in retailers
            }

            # Fetch current RETAILER prices
            retailer_prices = get_price_queryset(item_ids, effective_from).filter(
                price_type='CHANNEL_PARTNER',
                retailer_id__in=location_ids
            )
            retailer_current_map = {}
            for price in retailer_prices:
                key = f"{price.item_id}-{price.retailer_id}"
                retailer_current_map[key] = choose_best(retailer_current_map.get(key), price)
            for key, val in retailer_current_map.items():
                current_prices[key] = str(val.selling_price)

            # Fetch parent prices
            enable_distributor = channel_config.get('enable_distributor', False)
            enable_superstockist = channel_config.get('enable_superstockist', False)

            dist_ids = [r['distributor_id'] for r in retailer_info_map.values() if r['distributor_id']]
            dist_prices = get_price_queryset(item_ids, effective_from).filter(
                price_type='CHANNEL_PARTNER', distributor_id__in=dist_ids
            ) if dist_ids and enable_distributor else []
            dist_price_map = {f"{str(price.item_id)}-{str(price.distributor_id)}": price for price in dist_prices}

            ss_ids = [r['superstockist_id'] for r in retailer_info_map.values() if r['superstockist_id']]
            ss_prices = get_price_queryset(item_ids, effective_from).filter(
                price_type='CHANNEL_PARTNER', superstockist_id__in=ss_ids
            ) if ss_ids and enable_superstockist else []
            ss_price_map = {f"{str(price.item_id)}-{str(price.superstockist_id)}": price for price in ss_prices}

            # Geographic fallbacks
            area_ids = [r['area_id'] for r in retailer_info_map.values() if r['area_id']]
            city_ids = [r['city_id'] for r in retailer_info_map.values() if r['city_id']]
            state_ids = [r['state_id'] for r in retailer_info_map.values() if r['state_id']]

            area_prices = get_price_queryset(item_ids, effective_from).filter(
                price_type='GEOGRAPHIC', area_id__in=area_ids
            ) if area_ids else []
            area_price_map = {f"{str(price.item_id)}-{str(price.area_id)}": price for price in area_prices}

            city_prices = get_price_queryset(item_ids, effective_from).filter(
                price_type='GEOGRAPHIC', city_id__in=city_ids, area__isnull=True
            ) if city_ids else []
            city_price_map = {f"{str(price.item_id)}-{str(price.city_id)}": price for price in city_prices}

            state_prices = get_price_queryset(item_ids, effective_from).filter(
                price_type='GEOGRAPHIC', state_id__in=state_ids, city__isnull=True
            ) if state_ids else []
            state_price_map = {f"{str(price.item_id)}-{str(price.state_id)}": price for price in state_prices}

            base_prices_qs = get_price_queryset(item_ids, effective_from).filter(price_type='BASE')
            base_price_map = {str(bp.item_id): bp for bp in base_prices_qs}

            # Match parent prices
            for item_id in item_ids:
                for retailer_id in location_ids:
                    key = f"{item_id}-{retailer_id}"
                    retailer_info = retailer_info_map.get(retailer_id)
                    if retailer_info:
                        # Try DISTRIBUTOR → SUPERSTOCKIST → AREA → CITY → STATE → BASE
                        if enable_distributor and retailer_info['distributor_id']:
                            dist_key = f"{item_id}-{retailer_info['distributor_id']}"
                            if dist_key in dist_price_map:
                                parent_prices[key] = {
                                    'price': str(dist_price_map[dist_key].selling_price),
                                    'level': 'DISTRIBUTOR',
                                    'location_id': retailer_info['distributor_id'],
                                    'location_name': 'Distributor'
                                }
                                continue

                        if enable_superstockist and retailer_info['superstockist_id']:
                            ss_key = f"{item_id}-{retailer_info['superstockist_id']}"
                            if ss_key in ss_price_map:
                                parent_prices[key] = {
                                    'price': str(ss_price_map[ss_key].selling_price),
                                    'level': 'SUPERSTOCKIST',
                                    'location_id': retailer_info['superstockist_id'],
                                    'location_name': 'Superstockist'
                                }
                                continue

                        if retailer_info['area_id']:
                            area_key = f"{item_id}-{retailer_info['area_id']}"
                            if area_key in area_price_map:
                                parent_prices[key] = {
                                    'price': str(area_price_map[area_key].selling_price),
                                    'level': 'AREA',
                                    'location_id': retailer_info['area_id'],
                                    'location_name': retailer_info['area_name']
                                }
                                continue

                        if retailer_info['city_id']:
                            city_key = f"{item_id}-{retailer_info['city_id']}"
                            if city_key in city_price_map:
                                parent_prices[key] = {
                                    'price': str(city_price_map[city_key].selling_price),
                                    'level': 'CITY',
                                    'location_id': retailer_info['city_id'],
                                    'location_name': retailer_info['city_name']
                                }
                                continue

                        if retailer_info['state_id']:
                            state_key = f"{item_id}-{retailer_info['state_id']}"
                            if state_key in state_price_map:
                                parent_prices[key] = {
                                    'price': str(state_price_map[state_key].selling_price),
                                    'level': 'STATE',
                                    'location_id': retailer_info['state_id'],
                                    'location_name': retailer_info['state_name']
                                }
                                continue

                        if item_id in base_price_map:
                            parent_prices[key] = {
                                'price': str(base_price_map[item_id].selling_price),
                                'level': 'BASE',
                                'location_id': None,
                                'location_name': 'Base Price'
                            }

        return Response({
            'current_prices': current_prices,
            'parent_prices': parent_prices
        })


class PriceBookHistoryFilter(FilterSet):
    item_code = CharFilter(field_name='price_book__item__code', lookup_expr='icontains')
    action = CharFilter(field_name='action')
    created_on_start = DateTimeFilter(field_name='created_on', lookup_expr='gte')
    created_on_end = DateTimeFilter(field_name='created_on', lookup_expr='lte')

    class Meta:
        model = PriceBookHistory
        fields = ['item_code', 'action', 'created_on_start', 'created_on_end']


class PriceBookHistoryList(generics.ListAPIView):
    serializer_class = PriceBookHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = PriceBookHistoryFilter

    def get_queryset(self):
        price_book_id = self.request.query_params.get('price_book_id')
        queryset = PriceBookHistory.objects.select_related('price_book__item')

        if price_book_id:
            queryset = queryset.filter(price_book_id=price_book_id)

        return queryset.order_by('-created_on')


class GetItemPrice(APIView):
    """
    Price Resolution Endpoint
    Resolves the best applicable price for an item based on:
    - Geographic scope (area > city > state)
    - Channel partner scope (retailer > distributor > superstockist)
    - Base price (fallback)

    Query Parameters:
    - item_id (required): Item ID
    - state_id (optional): State ID
    - city_id (optional): City ID
    - area_id (optional): Area ID
    - retailer_id (optional): Retailer ID
    - distributor_id (optional): Distributor ID
    - superstockist_id (optional): Superstockist ID
    - date (optional): Date for price (YYYY-MM-DD, default: today)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from datetime import date

        # Required parameters
        item_id = request.query_params.get('item_id')
        if not item_id:
            return Response(
                {'error': 'item_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Optional parameters
        state_id = request.query_params.get('state_id')
        city_id = request.query_params.get('city_id')
        area_id = request.query_params.get('area_id')
        retailer_id = request.query_params.get('retailer_id')
        distributor_id = request.query_params.get('distributor_id')
        superstockist_id = request.query_params.get('superstockist_id')
        price_date = request.query_params.get('date')

        # Parse date
        if price_date:
            try:
                price_date = datetime.strptime(price_date, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            price_date = date.today()

        # Base queryset - active prices for this item
        # Exclude prices from DRAFT documents
        base_qs = PriceBook.objects.filter(
            item_id=item_id,
            is_deleted=False,
            is_active=True,
            effective_from__lte=price_date
        ).filter(
            Q(effective_to__isnull=True) | Q(effective_to__gte=price_date)
        ).exclude(
            document__status='DRAFT'
        ).select_related('item')

        # Priority 1: Retailer-specific price
        if retailer_id:
            price = base_qs.filter(
                price_type='CHANNEL_PARTNER',
                retailer_id=retailer_id,
                distributor__isnull=True,
                superstockist__isnull=True
            ).first()
            if price:
                return Response({
                    'price': PriceBookSerializer(price).data,
                    'match_level': 'RETAILER',
                    'message': 'Retailer-specific price found'
                })

        # Priority 2: Distributor-specific price
        if distributor_id:
            price = base_qs.filter(
                price_type='CHANNEL_PARTNER',
                distributor_id=distributor_id,
                retailer__isnull=True,
                superstockist__isnull=True
            ).first()
            if price:
                return Response({
                    'price': PriceBookSerializer(price).data,
                    'match_level': 'DISTRIBUTOR',
                    'message': 'Distributor-specific price found'
                })

        # Priority 3: Superstockist-specific price
        if superstockist_id:
            price = base_qs.filter(
                price_type='CHANNEL_PARTNER',
                superstockist_id=superstockist_id,
                retailer__isnull=True,
                distributor__isnull=True
            ).first()
            if price:
                return Response({
                    'price': PriceBookSerializer(price).data,
                    'match_level': 'SUPERSTOCKIST',
                    'message': 'Superstockist-specific price found'
                })

        # Priority 4: Area-specific price
        if area_id:
            price = base_qs.filter(
                price_type='GEOGRAPHIC',
                area_id=area_id,
                city__isnull=True,
                state__isnull=True
            ).first()
            if price:
                return Response({
                    'price': PriceBookSerializer(price).data,
                    'match_level': 'AREA',
                    'message': 'Area-specific price found'
                })

        # Priority 5: City-specific price
        if city_id:
            price = base_qs.filter(
                price_type='GEOGRAPHIC',
                city_id=city_id,
                area__isnull=True,
                state__isnull=True
            ).first()
            if price:
                return Response({
                    'price': PriceBookSerializer(price).data,
                    'match_level': 'CITY',
                    'message': 'City-specific price found'
                })

        # Priority 6: State-specific price
        if state_id:
            price = base_qs.filter(
                price_type='GEOGRAPHIC',
                state_id=state_id,
                city__isnull=True,
                area__isnull=True
            ).first()
            if price:
                return Response({
                    'price': PriceBookSerializer(price).data,
                    'match_level': 'STATE',
                    'message': 'State-specific price found'
                })

        # Priority 7: Base price (fallback)
        price = base_qs.filter(
            price_type='BASE',
            state__isnull=True,
            city__isnull=True,
            area__isnull=True,
            retailer__isnull=True,
            distributor__isnull=True,
            superstockist__isnull=True
        ).first()

        if price:
            return Response({
                'price': PriceBookSerializer(price).data,
                'match_level': 'BASE',
                'message': 'Base price found'
            })

        # No price found
        return Response(
            {
                'error': 'No applicable price found for this item',
                'item_id': item_id,
                'date': str(price_date)
            },
            status=status.HTTP_404_NOT_FOUND
        )


# ============================================================================
# SALES ORDER VIEWS
# ============================================================================

# ============================================================================
# SALES ORDER VIEWS MOVED TO Sales APP
# ============================================================================
# The Sales Order views, filters, and price cascade functionality have been
# moved to the Sales app. If you need to reference them, import from:
# from Sales.views import SalesOrderList, SalesOrderDetail, etc.
# ============================================================================


# Attachment Views


class SchemeFilter(FilterSet):
    """Filter for Scheme model"""
    name = CharFilter(field_name='name', lookup_expr='icontains')
    code = CharFilter(field_name='code', lookup_expr='icontains')
    scheme_type = CharFilter(field_name='scheme_type')
    status = CharFilter(field_name='status')
    company = CharFilter(field_name='company__id')

    class Meta:
        model = Scheme
        fields = ['name', 'code', 'scheme_type', 'status', 'company']


class SchemeMiniList(generics.ListAPIView):
    """Mini serializer for dropdowns"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SchemeMiniSerializer
    pagination_class = None
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    model = Scheme
    search_fields = ['code', 'name']
    ordering_fields = ['code', 'created_on']

    def get_queryset(self):
        _auto_expire_schemes()
        queryset = Scheme.objects.filter(is_deleted=False, status='ACTIVE').order_by('name')
        return apply_company_location_filter(queryset, self.request.user, company_field='company')


class SchemeListCreateView(generics.ListCreateAPIView):
    """
    List all schemes with filtering and pagination.
    Create a new scheme.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SchemeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = SchemeFilter
    search_fields = ['code', 'name', 'description', 'scheme_type', 'status', 'company__name']
    ordering_fields = ['code', 'created_on', 'scheme_type', 'status']

    model = Scheme
    queryset = Scheme.objects.filter(is_deleted=False).order_by('-created_on')

    def get_queryset(self):
        """Filter by company based on user access"""
        _auto_expire_schemes()
        queryset = super().get_queryset()
        queryset = apply_company_location_filter(queryset, self.request.user, company_field='company')
        company_id = self.request.query_params.get('company_id')
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        return queryset

    def perform_create(self, serializer):
        """Save scheme with creator info"""
        instance = serializer.save()
        if instance.status == 'DRAFT':
            _set_draft_authorization(instance)


class SchemeChoicesView(APIView):
    """Provide scheme choice lists for frontend dropdowns."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        scheme_type = request.query_params.get('scheme_type')
        scheme_types = [
            {"id": value, "name": label}
            for value, label in Scheme.SchemeType.choices
        ]
        condition_choices = list(SchemeCondition.ConditionType.choices)
        benefit_choices = list(SchemeBenefit.BenefitType.choices)

        if scheme_type:
            constraints = get_scheme_type_constraints(scheme_type)
            if not constraints:
                raise DRFValidationError({"scheme_type": "Invalid scheme_type"})
            allowed_condition_types = set(constraints.get('condition_types', []))
            allowed_benefit_types = set(constraints.get('benefit_types', []))
            condition_choices = [c for c in condition_choices if c[0] in allowed_condition_types]
            benefit_choices = [b for b in benefit_choices if b[0] in allowed_benefit_types]

        condition_types = [{"id": value, "name": label} for value, label in condition_choices]
        benefit_types = [{"id": value, "name": label} for value, label in benefit_choices]

        return Response({
            "scheme_types": scheme_types,
            "condition_types": condition_types,
            "benefit_types": benefit_types,
        })


class SchemeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a scheme.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SchemeSerializer
    model = Scheme

    def get_queryset(self):
        queryset = Scheme.objects.filter(is_deleted=False)
        return apply_company_location_filter(queryset, self.request.user, company_field='company')

    def perform_update(self, serializer):
        """Update scheme"""
        instance = serializer.save()
        if instance.status == 'DRAFT':
            _set_draft_authorization(instance)

    def perform_destroy(self, instance):
        """Soft delete the scheme"""
        instance.is_deleted = True
        instance.code = f"{instance.code}_DEL_{uuid.uuid4().hex[:8]}"
        instance.save()


class SchemeActivateView(generics.GenericAPIView):
    """Activate a scheme"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SchemeSerializer

    def get_queryset(self):
        queryset = Scheme.objects.filter(is_deleted=False)
        return apply_company_location_filter(queryset, self.request.user, company_field='company')

    def post(self, request, *args, **kwargs):
        """Activate the scheme"""
        instance = self.get_object()
        if instance.status == 'DRAFT':
            instance.status = 'ACTIVE'
            instance.save()
            # Create history record
            SchemeHistory.objects.create(
                scheme=instance,
                action='ACTIVATED',
                changed_by_type=self.request.user.groups.first().name if self.request.user.groups.exists() else 'USER',
                changed_by_identifier=str(self.request.user.id),
                changes={'status': {'from': 'DRAFT', 'to': 'ACTIVE'}}
            )
            serializer = self.get_serializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(
            {'detail': 'Scheme must be in DRAFT status to activate'},
            status=status.HTTP_400_BAD_REQUEST
        )


class SchemeDeactivateView(generics.GenericAPIView):
    """Deactivate a scheme"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SchemeSerializer

    def get_queryset(self):
        queryset = Scheme.objects.filter(is_deleted=False)
        return apply_company_location_filter(queryset, self.request.user, company_field='company')

    def post(self, request, *args, **kwargs):
        """Deactivate the scheme"""
        instance = self.get_object()
        if instance.status == 'ACTIVE':
            instance.status = 'INACTIVE'
            instance.save()
            # Create history record
            SchemeHistory.objects.create(
                scheme=instance,
                action='DEACTIVATED',
                changed_by_type=self.request.user.groups.first().name if self.request.user.groups.exists() else 'USER',
                changed_by_identifier=str(self.request.user.id),
                changes={'status': {'from': 'ACTIVE', 'to': 'INACTIVE'}}
            )
            serializer = self.get_serializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(
            {'detail': 'Scheme must be in ACTIVE status to deactivate'},
            status=status.HTTP_400_BAD_REQUEST
        )


class SchemeHistoryView(generics.ListAPIView):
    """Get history of changes for a scheme"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SchemeHistorySerializer
    pagination_class = None
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['changed_at', 'action']
    ordering = ['-changed_at']

    def get_queryset(self):
        """Get history for specific scheme"""
        scheme_id = self.kwargs.get('scheme_id')
        return SchemeHistory.objects.filter(
            scheme_id=scheme_id,
            scheme__is_deleted=False
        ).order_by('-changed_at')


class SuperstockistAttachmentList(AttachmentListView):

    model = Superstockist


class SuperstockistAttachmentUpload(AttachmentUploadView):
    model = Superstockist


class SuperstockistAttachmentDelete(AttachmentDeleteView):
    model = Superstockist


class DistributorAttachmentList(AttachmentListView):
    model = Distributor


class DistributorAttachmentUpload(AttachmentUploadView):
    model = Distributor


class DistributorAttachmentDelete(AttachmentDeleteView):
    model = Distributor


class RetailerAttachmentList(AttachmentListView):
    model = Retailer


class RetailerAttachmentUpload(AttachmentUploadView):
    model = Retailer


class RetailerAttachmentDelete(AttachmentDeleteView):
    model = Retailer


# Superstockist Contacts
class SuperstockistContactList(generics.ListCreateAPIView):
    serializer_class = SuperstockistContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        superstockist_id = self.kwargs.get('superstockist_id')
        return SuperstockistContact.objects.filter(
            superstockist_id=superstockist_id, is_deleted=False).order_by(
            '-is_primary', 'contact_person')

    def perform_create(self, serializer):
        superstockist_id = self.kwargs.get('superstockist_id')
        superstockist = get_object_or_404(Superstockist, id=superstockist_id, is_deleted=False)
        serializer.save(superstockist=superstockist)


class SuperstockistContactDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SuperstockistContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        superstockist_id = self.kwargs.get('superstockist_id')
        return SuperstockistContact.objects.filter(superstockist_id=superstockist_id, is_deleted=False)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()


# Distributor Contacts
class DistributorContactList(generics.ListCreateAPIView):
    serializer_class = DistributorContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        distributor_id = self.kwargs.get('distributor_id')
        return DistributorContact.objects.filter(
            distributor_id=distributor_id, is_deleted=False).order_by(
            '-is_primary', 'contact_person')

    def perform_create(self, serializer):
        distributor_id = self.kwargs.get('distributor_id')
        distributor = get_object_or_404(Distributor, id=distributor_id, is_deleted=False)
        serializer.save(distributor=distributor)


class DistributorContactDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DistributorContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        distributor_id = self.kwargs.get('distributor_id')
        return DistributorContact.objects.filter(distributor_id=distributor_id, is_deleted=False)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()


# Retailer Contacts
class RetailerContactList(generics.ListCreateAPIView):
    serializer_class = RetailerContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        retailer_id = self.kwargs.get('retailer_id')
        return RetailerContact.objects.filter(
            retailer_id=retailer_id, is_deleted=False).order_by(
            '-is_primary', 'contact_person')

    def perform_create(self, serializer):
        retailer_id = self.kwargs.get('retailer_id')
        retailer = get_object_or_404(Retailer, id=retailer_id, is_deleted=False)
        serializer.save(retailer=retailer)


class RetailerContactDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RetailerContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        retailer_id = self.kwargs.get('retailer_id')
        return RetailerContact.objects.filter(retailer_id=retailer_id, is_deleted=False)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()



# ============================================================================
# GENERIC CHANNEL PARTNER VIEWS
# ============================================================================

class ChannelPartnerMiniList(APIView):
    """
    Generic mini list endpoint for all channel partner types.
    Returns combined list of superstockists, distributors, and retailers.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from django.db.models import Value, CharField
        
        # Get filtered querysets for each type
        superstockists = Superstockist.filtered_objects.get_qs(
            user=request.user, is_active=True
        ).annotate(partner_type=Value('SUPERSTOCKIST', output_field=CharField()))
        
        distributors = Distributor.filtered_objects.get_qs(
            user=request.user, is_active=True
        ).annotate(partner_type=Value('DISTRIBUTOR', output_field=CharField()))
        
        retailers = Retailer.filtered_objects.get_qs(
            user=request.user, is_active=True
        ).annotate(partner_type=Value('RETAILER', output_field=CharField()))
        
        # Apply company/location filters
        superstockists = apply_channel_partner_company_location_filter(
            superstockists, request.user, 'company', 'state', 'city', 'locations'
        )
        distributors = apply_channel_partner_company_location_filter(
            distributors, request.user, 'company', 'state', 'city', 'locations'
        )
        retailers = apply_channel_partner_company_location_filter(
            retailers, request.user, 'company', 'state', 'city', 'locations'
        )
        
        # Combine results
        results = []
        
        for s in superstockists.values('id', 'code', 'name', 'partner_type'):
            results.append(s)
        
        for d in distributors.values('id', 'code', 'name', 'partner_type'):
            results.append(d)
        
        for r in retailers.values('id', 'code', 'name', 'partner_type'):
            results.append(r)
        
        # Sort by name
        results.sort(key=lambda x: x['name'])
        
        return Response(results)


class ChannelPartnerDetail(APIView):
    """
    Generic detail endpoint for channel partners.
    Automatically determines the type and returns the appropriate record.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        # Try each type in order
        try:
            obj = Superstockist.filtered_objects.get_qs(user=request.user).get(id=pk)
            serializer = SuperstockistSerializer(obj)
            data = serializer.data
            data['partner_type'] = 'SUPERSTOCKIST'
            return Response(data)
        except Superstockist.DoesNotExist:
            pass
        
        try:
            obj = Distributor.filtered_objects.get_qs(user=request.user).get(id=pk)
            serializer = DistributorSerializer(obj)
            data = serializer.data
            data['partner_type'] = 'DISTRIBUTOR'
            return Response(data)
        except Distributor.DoesNotExist:
            pass
        
        try:
            obj = Retailer.filtered_objects.get_qs(user=request.user).get(id=pk)
            serializer = RetailerSerializer(obj)
            data = serializer.data
            data['partner_type'] = 'RETAILER'
            return Response(data)
        except Retailer.DoesNotExist:
            pass
        
        return Response(
            {'detail': 'Channel partner not found'},
            status=status.HTTP_404_NOT_FOUND
        )


# ============================================================================
# PROJECT MASTER VIEWSETS — SRS Module 6
# ============================================================================

class ProjectList(generics.ListCreateAPIView):
    """List + Create Project."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProjectSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'project_type', 'approval_type', 'is_active', 'location']
    search_fields = ['name', 'code', 'developer_name', 'rera_number']
    ordering_fields = ['name', 'created_on', 'status']
    ordering = ['name']

    def get_queryset(self):
        # Soft-delete aware: hide tombstoned rows from list views
        return Project.objects.filter(is_deleted=False).select_related('location').all()


class ProjectDetail(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve / Update / Soft-delete Project."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProjectSerializer
    lookup_field = 'pk'

    def get_queryset(self):
        return Project.objects.select_related('location').all()

    def perform_destroy(self, instance):
        # Soft delete: flip is_deleted, don't drop the row
        instance.delete()


class ProjectMini(generics.ListAPIView):
    """Minimal list for dropdowns. Excludes soft-deleted + inactive."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProjectMiniSerializer

    def get_queryset(self):
        return Project.objects.filter(is_deleted=False, is_active=True).order_by('name')


class ProjectChoices(APIView):
    """Return choice enums for Project form."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({
            'project_statuses': [{'value': k, 'label': v} for k, v in Project.PROJECT_STATUS_CHOICES],
            'project_types': [{'value': k, 'label': v} for k, v in Project.PROJECT_TYPE_CHOICES],
            'approval_types': [{'value': k, 'label': v} for k, v in Project.APPROVAL_TYPE_CHOICES],
        })
