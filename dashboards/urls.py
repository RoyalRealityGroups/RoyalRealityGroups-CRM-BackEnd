"""
URL configuration for Dashboards app.
"""
from django.urls import path
from .views import (
    WidgetTypeListCreateView,
    WidgetTypeDetailView,
    DashboardListCreateView,
    DashboardDetailView,
    DashboardDuplicateView,
    MyDashboardsView,
    DashboardWidgetListCreateView,
    DashboardWidgetDetailView,
    BulkUpdateWidgetLayoutView,
    DashboardGroupListCreateView,
    DashboardGroupDetailView,
    WidgetDataView,
)

urlpatterns = [
    # Widget Types
    path('widget-types/', WidgetTypeListCreateView.as_view(), name='widget-type-list'),
    path('widget-types/<uuid:pk>/', WidgetTypeDetailView.as_view(), name='widget-type-detail'),
    
    # Dashboards
    path('dashboards/', DashboardListCreateView.as_view(), name='dashboard-list'),
    path('dashboards/my-dashboards/', MyDashboardsView.as_view(), name='my-dashboards'),
    path('dashboards/<uuid:pk>/', DashboardDetailView.as_view(), name='dashboard-detail'),
    path('dashboards/<uuid:pk>/duplicate/', DashboardDuplicateView.as_view(), name='dashboard-duplicate'),
    
    # Dashboard Widgets
    path('widgets/', DashboardWidgetListCreateView.as_view(), name='widget-list'),
    path('widgets/bulk-update-layout/', BulkUpdateWidgetLayoutView.as_view(), name='widget-bulk-update-layout'),
    path('widgets/<uuid:pk>/', DashboardWidgetDetailView.as_view(), name='widget-detail'),
    
    # Dashboard Group Assignments
    path('group-assignments/', DashboardGroupListCreateView.as_view(), name='dashboard-group-list'),
    path('group-assignments/<uuid:pk>/', DashboardGroupDetailView.as_view(), name='dashboard-group-detail'),
    
    # Widget Data
    path('widget-data/', WidgetDataView.as_view(), name='widget-data'),
]


