"""UserManagement URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from . import views
from .test_views import TestUserSerializerView
from django.urls import path

urlpatterns = [

    # Specific routes first (before catch-all pattern)
    path('create/', views.UserCreate.as_view(), name='user_create'),
    path('list/', views.UserList.as_view(), name='user_list'),
    path('mini/users/', views.UserMini.as_view()),
    path('mini/users/<str:user_type>/', views.UserMiniByUserType.as_view()),
    path('userpermissions/', views.UserPermissionList.as_view(), name='userpermissions'),
    
    # Test endpoint
    path('test/<str:user_id>/', TestUserSerializerView.as_view(), name='test_user_serializer'),
    
    # Channel Partner endpoints
    path('channel-partners/superstockists/', views.SuperstockistListView.as_view(), name='superstockists_list'),
    path('channel-partners/distributors/', views.DistributorListView.as_view(), name='distributors_list'),
    path('channel-partners/retailers/', views.RetailerListView.as_view(), name='retailers_list'),
    
    path('dropdowns/companies/', views.CompanyDropdownView.as_view(), name='companies_dropdown'),
    path('dropdowns/locations/', views.LocationDropdownView.as_view(), name='locations_dropdown'),
    
    path('screens/', views.ScreenListView.as_view(), name='screen_list'),
    path('permissions/my/', views.MyPermissionsView.as_view(), name='my_permissions'),
    path('permissions/<uuid:user_id>/', views.UserPermissionView.as_view(), name='user_permissions'),
    path('permissions/<uuid:user_id>/audit/', views.PermissionAuditLogView.as_view(), name='permission_audit'),

    # Catch-all pattern MUST be last
    path('<str:pk>/', views.UserDetails.as_view(), name='users'),

]


