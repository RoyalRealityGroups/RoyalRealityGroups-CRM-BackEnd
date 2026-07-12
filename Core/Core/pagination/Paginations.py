from rest_framework.pagination import PageNumberPagination, CursorPagination
from rest_framework.response import Response


class LargeResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000
    
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'results': data
        })

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 10000

    def get_paginated_response(self, data):
        return Response({
            # 'links': {
            #     'next': self.get_next_link(),
            #     'previous': self.get_previous_link()
            # },
            'count': self.page.paginator.count,
            'results': data
        })


class CursorSetPagination(CursorPagination):
    """
    Cursor-based pagination for large datasets.
    
    Better performance than offset-based pagination for:
    - Large datasets (millions of records)
    - Real-time data (prevents page drift)
    - Sequential navigation
    
    Usage:
        class MyViewSet(viewsets.ModelViewSet):
            pagination_class = CursorSetPagination
            
    Note: Requires an ordering field (usually created_on or id)
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    ordering = '-created_on'  # Default ordering (can be overridden in viewset)
    cursor_query_param = 'cursor'
    
    def get_paginated_response(self, data):
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })