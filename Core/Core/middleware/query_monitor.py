"""
Query Monitoring Middleware

This middleware monitors database queries and logs slow requests/queries.
Useful for identifying performance bottlenecks.

Features:
- Tracks total queries per request
- Identifies slow requests (> 1 second)
- Logs individual slow queries (> 100ms)
- Adds debug headers (X-DB-Query-Count, X-Response-Time)

Usage:
    Add to MIDDLEWARE in settings.py:
    'Core.Core.middleware.query_monitor.QueryMonitorMiddleware'
"""

import time
import logging
from django.db import connection
from django.conf import settings

logger = logging.getLogger(__name__)


class QueryMonitorMiddleware:
    """Monitor slow database queries and requests"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.slow_request_threshold = 1.0  # seconds
        self.slow_query_threshold = 0.1  # seconds (100ms)
    
    def __call__(self, request):
        # Reset query log
        if hasattr(connection, 'queries_log'):
            connection.queries_log.clear()
        
        start_time = time.time()
        
        # Process request
        response = self.get_response(request)
        
        duration = time.time() - start_time
        
        # Only monitor in DEBUG mode or if explicitly enabled
        if settings.DEBUG or getattr(settings, 'ENABLE_QUERY_MONITORING', False):
            self._log_request_metrics(request, duration)
        
        # Add debug headers
        response['X-DB-Query-Count'] = str(len(connection.queries))
        response['X-Response-Time'] = f"{duration:.3f}"
        
        return response
    
    def _log_request_metrics(self, request, duration):
        """Log request metrics if slow"""
        query_count = len(connection.queries)
        
        # Log slow requests
        if duration > self.slow_request_threshold:
            logger.warning(
                f"Slow request: {request.method} {request.path} "
                f"Duration: {duration:.2f}s "
                f"Queries: {query_count}"
            )
            
            # Log individual slow queries
            for query in connection.queries:
                query_time = float(query['time'])
                if query_time > self.slow_query_threshold:
                    logger.warning(
                        f"Slow query ({query_time:.3f}s): "
                        f"{query['sql'][:200]}..."
                    )
        
        # Log requests with excessive queries
        elif query_count > 50:
            logger.warning(
                f"High query count: {request.method} {request.path} "
                f"Queries: {query_count} "
                f"Duration: {duration:.2f}s"
            )
    
    def process_exception(self, request, exception):
        """Log exceptions with query context"""
        if settings.DEBUG:
            logger.error(
                f"Exception in {request.method} {request.path} "
                f"Queries before error: {len(connection.queries)}"
            )
        return None
