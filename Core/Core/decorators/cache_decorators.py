"""
API Response Caching Decorators
Provides reusable decorators for caching API responses with automatic invalidation
"""

from django.core.cache import cache
from functools import wraps
from rest_framework.response import Response
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


def cache_api_response(timeout=300, key_prefix='api', vary_on_user=True, vary_on_company=True):
    """
    Cache API response decorator for Django REST Framework ViewSets
    
    Args:
        timeout (int): Cache timeout in seconds (default 5 minutes)
        key_prefix (str): Prefix for cache key
        vary_on_user (bool): Include user ID in cache key
        vary_on_company (bool): Include company ID in cache key
    
    Usage:
        @cache_api_response(timeout=600, key_prefix='items')
        def list(self, request):
            return super().list(request)
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            # Skip caching for non-GET requests
            if request.method != 'GET':
                return view_func(self, request, *args, **kwargs)
            
            # Build cache key data
            cache_key_data = {
                'path': request.path,
                'query': dict(request.GET),
            }
            
            # Add user to cache key if authenticated
            if vary_on_user and request.user.is_authenticated:
                cache_key_data['user'] = request.user.id
            
            # Add company to cache key if available
            if vary_on_company and hasattr(request.user, 'company_id'):
                cache_key_data['company'] = request.user.company_id
            
            # Generate cache key hash
            cache_key_hash = hashlib.md5(
                json.dumps(cache_key_data, sort_keys=True).encode()
            ).hexdigest()
            cache_key = f"{key_prefix}:{cache_key_hash}"
            
            # Try to get from cache
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return Response(cached_data)
            
            # Cache miss - execute view
            logger.debug(f"Cache MISS: {cache_key}")
            response = view_func(self, request, *args, **kwargs)
            
            # Cache successful responses only
            if response.status_code == 200 and isinstance(response, Response):
                cache.set(cache_key, response.data, timeout)
                logger.debug(f"Cached response: {cache_key} for {timeout}s")
            
            return response
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern):
    """
    Invalidate all cache keys matching pattern
    Works with Redis backend only
    
    Args:
        pattern (str): Pattern to match (e.g., 'items:*', 'pricebook:*')
    
    Usage:
        invalidate_cache_pattern('items:*')
    """
    try:
        from django_redis import get_redis_connection
        conn = get_redis_connection("default")
        
        # Get all keys matching pattern
        full_pattern = f"sales_app:{pattern}"
        keys = conn.keys(full_pattern)
        
        if keys:
            conn.delete(*keys)
            logger.info(f"Invalidated {len(keys)} cache keys matching: {pattern}")
    except ImportError:
        logger.warning("Cache invalidation requires Redis backend")
    except Exception as e:
        logger.error(f"Error invalidating cache pattern {pattern}: {e}")


# Recommended cache timeouts by resource type
CACHE_TIMEOUTS = {
    'states': 3600,      # 1 hour
    'cities': 3600,      # 1 hour
    'categories': 3600,  # 1 hour
    'brands': 3600,      # 1 hour
    'items': 600,        # 10 minutes
    'pricebook': 300,    # 5 minutes
    'sales_orders': 60,  # 1 minute
}
