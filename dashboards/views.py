"""
Views for Dashboards app - Adapted for TDH Sales Application.
"""
from rest_framework import generics, permissions, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend

from .models import WidgetType, Dashboard, DashboardWidget, DashboardGroup
from .serializers import (
    WidgetTypeListSerializer, WidgetTypeDetailSerializer, WidgetTypeCreateUpdateSerializer,
    DashboardListSerializer, DashboardDetailSerializer, DashboardCreateSerializer, DashboardUpdateSerializer,
    DashboardWidgetSerializer, DashboardWidgetCreateSerializer, DashboardWidgetUpdateSerializer,
    DashboardWidgetLayoutSerializer,
    DashboardGroupSerializer, DashboardGroupCreateSerializer,
    UserDashboardSerializer,
)


# ============== Widget Type Views ==============

class WidgetTypeListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = WidgetType.objects.filter(is_deleted=False)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'category']
    ordering_fields = ['name', 'category', 'display_order']
    ordering = ['category', 'display_order']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return WidgetTypeCreateUpdateSerializer
        return WidgetTypeListSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({'success': True, 'data': serializer.data})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            'success': True,
            'data': WidgetTypeDetailSerializer(serializer.instance).data,
            'message': 'Widget type created successfully'
        }, status=status.HTTP_201_CREATED)


class WidgetTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = WidgetType.objects.filter(is_deleted=False)

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return WidgetTypeCreateUpdateSerializer
        return WidgetTypeDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'success': True, 'data': serializer.data})

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            'success': True,
            'data': WidgetTypeDetailSerializer(instance).data,
            'message': 'Widget type updated successfully'
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_deleted=True
        instance.save()
        return Response({'success': True, 'message': 'Widget type deleted successfully'})


# ============== Dashboard Views ==============

class DashboardListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Dashboard.objects.filter(is_deleted=False)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'display_order', 'created_on']
    ordering = ['display_order', 'name']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DashboardCreateSerializer
        return DashboardListSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({'success': True, 'data': serializer.data})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(
            created_by_identifier=str(request.user.id),
        )
        return Response({
            'success': True,
            'data': DashboardDetailSerializer(instance).data,
            'message': 'Dashboard created successfully'
        }, status=status.HTTP_201_CREATED)


class DashboardDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Dashboard.objects.filter(is_deleted=False).prefetch_related('widgets', 'group_assignments')

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return DashboardUpdateSerializer
        return DashboardDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'success': True, 'data': serializer.data})

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            'success': True,
            'data': DashboardDetailSerializer(instance).data,
            'message': 'Dashboard updated successfully'
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_deleted=True
        instance.save()
        return Response({'success': True, 'message': 'Dashboard deleted successfully'})


class DashboardDuplicateView(APIView):
    """Duplicate a dashboard with all its widgets."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            source = Dashboard.objects.get(pk=pk, is_deleted=False)
        except Dashboard.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Dashboard not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if system dashboard
        if source.is_system:
            return Response({
                'success': False,
                'message': 'System dashboards cannot be duplicated'
            }, status=status.HTTP_403_FORBIDDEN)


        # Create new dashboard
        new_dashboard = Dashboard.objects.create(
            name=f"{source.name} (Copy)",
            description=source.description,
            icon=source.icon,
            visibility=source.visibility,
            layout_config=source.layout_config,
            is_default=False,
            is_system=False,
            display_order=0,
            theme=source.theme,
            refresh_interval=source.refresh_interval,
            created_by_identifier=str(request.user.id),
            created_by_type=request.user.__class__.__name__,
            modified_by_identifier=str(request.user.id),
            modified_by_type=request.user.__class__.__name__,
        )

        # Copy all active widgets
        for widget in source.widgets.filter(is_deleted=False):
            DashboardWidget.objects.create(
                dashboard=new_dashboard,
                widget_type=widget.widget_type,
                title=widget.title,
                subtitle=widget.subtitle,
                position_x=widget.position_x,
                position_y=widget.position_y,
                width=widget.width,
                height=widget.height,
                config=widget.config,
                data_source=widget.data_source,
                filters=widget.filters,
                style=widget.style,
                cache_duration=widget.cache_duration,
                is_visible=widget.is_visible,
                created_by_identifier=str(request.user.id),
                created_by_type=request.user.__class__.__name__,
                modified_by_identifier=str(request.user.id),
                modified_by_type=request.user.__class__.__name__,
            )

        serializer = DashboardDetailSerializer(new_dashboard)
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Dashboard duplicated successfully'
        }, status=status.HTTP_201_CREATED)


class MyDashboardsView(generics.ListAPIView):
    """Get dashboards accessible to current user based on their groups"""
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        # if self.request.query_params.get('detailed') == 'true':
        #     return DashboardDetailSerializer
        return DashboardDetailSerializer    #UserDashboardSerializer

    def get_queryset(self):
        user = self.request.user
        user_group_ids = list(user.groups.values_list('id', flat=True))

        dashboard_ids = DashboardGroup.objects.filter(
            group_id__in=user_group_ids,
            is_deleted=False
        ).values_list('dashboard_id', flat=True)

        dashboards = Dashboard.objects.filter(
            Q(id__in=dashboard_ids) | Q(visibility='organization'),
            is_deleted=False
        ).distinct().prefetch_related('widgets', 'group_assignments').order_by('display_order', 'name')

        dashboard_list = []
        for dashboard in dashboards:
            group_assignment = DashboardGroup.objects.filter(
                dashboard=dashboard,
                group_id__in=user_group_ids,
                is_deleted=False
            ).first()
            dashboard._can_customize = group_assignment.can_customize if group_assignment else False
            dashboard._is_default = group_assignment.is_default if group_assignment else False
            dashboard_list.append(dashboard)

        return dashboard_list

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'success': True, 'data': serializer.data})


# ============== Dashboard Widget Views ==============

class DashboardWidgetListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['position_y', 'position_x', 'created_on']
    ordering = ['position_y', 'position_x']

    def get_queryset(self):
        queryset = DashboardWidget.objects.filter(is_deleted=False).select_related('widget_type', 'dashboard')
        dashboard_id = self.request.query_params.get('dashboard')
        if dashboard_id:
            queryset = queryset.filter(dashboard_id=dashboard_id)
        return queryset

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DashboardWidgetCreateSerializer
        return DashboardWidgetSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({'success': True, 'data': serializer.data})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            'success': True,
            'data': DashboardWidgetSerializer(serializer.instance).data,
            'message': 'Widget created successfully'
        }, status=status.HTTP_201_CREATED)


class DashboardWidgetDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = DashboardWidget.objects.filter(is_deleted=False).select_related('widget_type', 'dashboard')

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return DashboardWidgetUpdateSerializer
        return DashboardWidgetSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'success': True, 'data': serializer.data})

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            'success': True,
            'data': DashboardWidgetSerializer(instance).data,
            'message': 'Widget updated successfully'
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_deleted=True
        instance.save()
        return Response({'success': True, 'message': 'Widget deleted successfully'})


class BulkUpdateWidgetLayoutView(APIView):
    """Bulk update widget positions/layouts"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        layouts = request.data.get('layouts', [])
        serializer = DashboardWidgetLayoutSerializer(data=layouts, many=True)
        serializer.is_valid(raise_exception=True)

        updated_count = 0
        for layout_data in serializer.validated_data:
            widget_id = layout_data['id']
            try:
                widget = DashboardWidget.objects.get(id=widget_id, is_deleted=False)
                widget.position_x = layout_data['x']
                widget.position_y = layout_data['y']
                widget.width = layout_data['w']
                widget.height = layout_data['h']
                widget.save()
                updated_count += 1
            except DashboardWidget.DoesNotExist:
                continue

        return Response({
            'success': True,
            'message': f'{updated_count} widgets updated successfully'
        })


# ============== Dashboard Group Views ==============

class DashboardGroupListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = DashboardGroup.objects.filter(is_deleted=False).select_related('dashboard', 'group')
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['display_order', 'created_on']
    ordering = ['group', 'display_order']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DashboardGroupCreateSerializer
        return DashboardGroupSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({'success': True, 'data': serializer.data})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            'success': True,
            'data': DashboardGroupSerializer(serializer.instance).data,
            'message': 'Dashboard group assignment created successfully'
        }, status=status.HTTP_201_CREATED)


class DashboardGroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = DashboardGroup.objects.filter(is_deleted=False).select_related('dashboard', 'group')
    serializer_class = DashboardGroupSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'success': True, 'data': serializer.data})

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = DashboardGroupCreateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            'success': True,
            'data': DashboardGroupSerializer(instance).data,
            'message': 'Dashboard group assignment updated successfully'
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_deleted=True
        instance.save()
        return Response({'success': True, 'message': 'Dashboard group assignment deleted successfully'})


# ============== Widget Data View ==============

class WidgetDataView(APIView):
    """Fetch data for a widget based on widget_id or data_source parameter"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from .data_service import WidgetDataService
        
        widget_id = request.query_params.get('widget_id')
        data_source = request.query_params.get('data_source')
        
        # Option 1: Get data by widget_id (reads data_source and filters from DashboardWidget)
        if widget_id:
            try:
                widget = DashboardWidget.objects.get(id=widget_id, is_deleted=False)
                data_source = widget.data_source
                filters = widget.filters or {}
                
                if not data_source:
                    return Response({
                        'success': False,
                        'message': 'Widget does not have a data_source configured'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
            except DashboardWidget.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Widget not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Option 2: Get data by data_source directly (with optional query param filters)
        elif data_source:
            filters = {k: v for k, v in request.query_params.items() if k != 'data_source'}
        
        else:
            return Response({
                'success': False,
                'message': 'Either widget_id or data_source parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = WidgetDataService.get_data(
                data_source=data_source,
                filters=filters,
                user=request.user
            )
            
            if 'error' in result:
                return Response({
                    'success': False,
                    'message': result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({'success': True, 'data': result})
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
