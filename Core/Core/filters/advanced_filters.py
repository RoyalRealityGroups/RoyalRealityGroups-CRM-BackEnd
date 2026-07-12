"""
Advanced Filtering Utilities

Provides complex filtering capabilities for ViewSets including:
- Multiple field filtering
- Range filters (date, number)
- Complex query combinations
- Dynamic filter building
"""

from django_filters import rest_framework as filters
from django_filters import FilterSet, CharFilter, NumberFilter, DateFilter, BooleanFilter
from django.db.models import Q
import json


class BaseAdvancedFilter(FilterSet):
    """
    Base filter class with common advanced filtering capabilities.
    
    Usage:
        class MyModelFilter(BaseAdvancedFilter):
            class Meta:
                model = MyModel
                fields = {
                    'name': ['exact', 'icontains'],
                    'status': ['exact', 'in'],
                    'created_on': ['gte', 'lte'],
                }
    """
    
    # Date range filters
    start_date = DateFilter(field_name='created_on', lookup_expr='gte', label='From Date')
    end_date = DateFilter(field_name='created_on', lookup_expr='lte', label='To Date')
    
    # Search across multiple fields
    search = CharFilter(method='filter_search', label='Global Search')
    
    def filter_search(self, queryset, name, value):
        """
        Search across multiple fields defined in search_fields.
        Override search_fields in subclass.
        """
        if not value:
            return queryset
        
        search_fields = getattr(self.Meta, 'search_fields', [])
        if not search_fields:
            return queryset
        
        query = Q()
        for field in search_fields:
            query |= Q(**{f"{field}__icontains": value})
        
        return queryset.filter(query)


class DynamicFilterMixin:
    """
    Mixin to add dynamic filtering capabilities to ViewSets.
    
    Allows building filters from query parameters like:
    ?filter={"field":"value","field2__gte":"value2"}
    """
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Get dynamic filters from query params
        filter_json = self.request.query_params.get('filter', None)
        
        if filter_json:
            try:
                filters_dict = json.loads(filter_json)
                queryset = queryset.filter(**filters_dict)
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                # Log error but don't crash
                print(f"Invalid filter JSON: {e}")
        
        return queryset


def create_date_range_filter(field_name='created_on'):
    """
    Helper to create date range filter fields.
    
    Usage:
        class MyFilter(FilterSet):
            start_date, end_date = create_date_range_filter('order_date')
    """
    start_filter = DateFilter(
        field_name=field_name,
        lookup_expr='gte',
        label=f'{field_name.title()} From'
    )
    end_filter = DateFilter(
        field_name=field_name,
        lookup_expr='lte',
        label=f'{field_name.title()} To'
    )
    return start_filter, end_filter


def create_number_range_filter(field_name):
    """
    Helper to create number range filter fields.
    
    Usage:
        min_amount, max_amount = create_number_range_filter('total_amount')
    """
    min_filter = NumberFilter(
        field_name=field_name,
        lookup_expr='gte',
        label=f'Min {field_name.title()}'
    )
    max_filter = NumberFilter(
        field_name=field_name,
        lookup_expr='lte',
        label=f'Max {field_name.title()}'
    )
    return min_filter, max_filter
