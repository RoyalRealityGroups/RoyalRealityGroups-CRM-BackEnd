"""
Saved Filters API Views
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.utils import timezone

from .filter_models import SavedFilter, FilterPreset
from .filter_serializers import SavedFilterSerializer, FilterPresetSerializer
from django_filters import FilterSet


class SavedFilterFilter(FilterSet):
    class Meta:
        model = SavedFilter
        fields = ['screen_name', 'is_public', 'is_default']


class SavedFilterListCreate(generics.ListCreateAPIView):
    """
    List user's saved filters or create new filter.
    GET: Returns filters created by user + public filters
    POST: Create new saved filter
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SavedFilterSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = SavedFilterFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_on', 'usage_count']
    
    def get_queryset(self):
        user = self.request.user
        screen_name = self.request.query_params.get('screen_name', None)
        
        # Get user's own filters + public filters
        queryset = SavedFilter.objects.filter(
            is_deleted=False
        ).filter(
            models.Q(created_by_identifier=str(user.id), created_by_type='User') |
            models.Q(is_public=True)
        )
        
        if screen_name:
            queryset = queryset.filter(screen_name=screen_name)
        
        return queryset.order_by('-is_default', '-usage_count', '-created_on')
    
    def perform_create(self, serializer):
        serializer.save()


class SavedFilterDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a saved filter.
    Only owner can modify their filters.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SavedFilterSerializer
    
    def get_queryset(self):
        user = self.request.user
        return SavedFilter.objects.filter(
            is_deleted=False,
            created_by_identifier=str(user.id),
            created_by_type='User'
        )
    
    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def apply_saved_filter(request, pk):
    """
    Apply a saved filter and increment usage count.
    POST /api/saved-filters/{id}/apply/
    """
    try:
        saved_filter = SavedFilter.objects.get(pk=pk, is_deleted=False)
        
        # Update usage stats
        saved_filter.usage_count += 1
        saved_filter.last_used = timezone.now()
        saved_filter.save(update_fields=['usage_count', 'last_used'])
        
        return Response({
            'filter_config': saved_filter.filter_config,
            'name': saved_filter.name
        }, status=status.HTTP_200_OK)
    
    except SavedFilter.DoesNotExist:
        return Response(
            {'error': 'Saved filter not found'},
            status=status.HTTP_404_NOT_FOUND
        )


class FilterPresetList(generics.ListAPIView):
    """
    List available filter presets for a screen.
    GET: Returns all active presets
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FilterPresetSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'description']
    
    def get_queryset(self):
        screen_name = self.request.query_params.get('screen_name', None)
        
        queryset = FilterPreset.objects.filter(
            is_deleted=False,
            is_active=True
        )
        
        if screen_name:
            queryset = queryset.filter(screen_name=screen_name)
        
        return queryset.order_by('sort_order', 'name')


class FilterPresetDetail(generics.RetrieveAPIView):
    """Get details of a specific filter preset"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FilterPresetSerializer
    queryset = FilterPreset.objects.filter(is_deleted=False, is_active=True)
