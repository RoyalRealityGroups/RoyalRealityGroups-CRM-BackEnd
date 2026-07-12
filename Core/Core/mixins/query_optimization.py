"""
Query Optimization Mixin for ViewSets

This mixin provides automatic query optimization capabilities including:
- select_related() for foreign key relationships
- prefetch_related() for many-to-many and reverse FK relationships
- only() for field selection to reduce data transfer

Usage:
    class OrderViewSet(OptimizedQueryMixin, viewsets.ModelViewSet):
        serializer_class = OrderSerializer
        
        # Define optimization
        select_related_fields = ['retailer', 'warehouse', 'created_by']
        prefetch_related_fields = ['order_items', 'order_items__item']
        
        # For list views with limited fields
        def get_only_fields_for_list(self):
            return [
                'id', 'order_number', 'order_date', 'total_amount', 
                'order_status', 'retailer__name', 'retailer__code'
            ]
        
        def list(self, request, *args, **kwargs):
            # Apply field limiting for list view
            self.only_fields = self.get_only_fields_for_list()
            return super().list(request, *args, **kwargs)
"""

from django.db.models import QuerySet
from rest_framework import viewsets


class OptimizedQueryMixin:
    """
    Mixin to add query optimization to viewsets.
    
    Automatically applies select_related, prefetch_related, and only()
    based on class attributes to prevent N+1 queries and reduce data transfer.
    """
    
    # Define which relations to prefetch (set in viewset)
    select_related_fields = []
    prefetch_related_fields = []
    only_fields = []
    
    def get_queryset(self) -> QuerySet:
        """
        Override get_queryset to apply optimizations.
        
        Returns:
            QuerySet: Optimized queryset with eager loading
        """
        queryset = super().get_queryset()
        
        # Apply select_related for foreign keys (reduces queries)
        if self.select_related_fields:
            queryset = queryset.select_related(*self.select_related_fields)
        
        # Apply prefetch_related for many-to-many and reverse FK
        if self.prefetch_related_fields:
            queryset = queryset.prefetch_related(*self.prefetch_related_fields)
        
        # Apply only() to select specific fields (reduces data transfer)
        if self.only_fields:
            queryset = queryset.only(*self.only_fields)
        
        return queryset
    
    def get_select_related_fields(self):
        """
        Get fields for select_related.
        Override this method for dynamic selection.
        
        Returns:
            list: Field names for select_related
        """
        return self.select_related_fields
    
    def get_prefetch_related_fields(self):
        """
        Get fields for prefetch_related.
        Override this method for dynamic selection.
        
        Returns:
            list: Field names for prefetch_related
        """
        return self.prefetch_related_fields
    
    def get_only_fields(self):
        """
        Get fields for only().
        Override this method for dynamic selection.
        
        Returns:
            list: Field names for only()
        """
        return self.only_fields


class CachedQueryMixin:
    """
    Mixin to add caching capabilities to viewsets.
    
    Caches querysets based on cache_key_prefix and cache_timeout.
    """
    
    cache_key_prefix = None
    cache_timeout = 300  # 5 minutes default
    
    def get_cache_key(self, **kwargs):
        """
        Generate cache key for the queryset.
        
        Args:
            **kwargs: Additional parameters for cache key
            
        Returns:
            str: Cache key
        """
        if not self.cache_key_prefix:
            return None
        
        params = '_'.join([f"{k}_{v}" for k, v in sorted(kwargs.items())])
        return f"{self.cache_key_prefix}_{params}"
    
    def get_cached_queryset(self, cache_key, fetch_func):
        """
        Get queryset from cache or fetch if not cached.
        
        Args:
            cache_key: Key for caching
            fetch_func: Function to fetch data if not cached
            
        Returns:
            QuerySet or list: Cached or fresh data
        """
        from django.core.cache import cache
        
        if not cache_key:
            return fetch_func()
        
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data
        
        data = fetch_func()
        cache.set(cache_key, data, self.cache_timeout)
        
        return data

