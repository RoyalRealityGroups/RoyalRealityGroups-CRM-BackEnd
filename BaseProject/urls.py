"""BaseProject URL Configuration

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
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from BaseProject.views import index_view, privacy_view
from Core.Core.views.health import health_check
from Lead.views import SiteVisitViewSet

from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health'),  # Health check endpoint
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]

if not settings.DYNAMICS_SAFE_MODE:
    site_visit_router = DefaultRouter()
    site_visit_router.register(r'site-visits', SiteVisitViewSet, basename='site-visit')

    app_urlpatterns = [

        path('api/users/', include('Core.Users.urls')),
        path('api/system/', include('Core.System.urls')),
        path('api/reports/', include('Core.Reports.urls')),

        path('api/usermanagement/', include('Users.urls')),  # Changed from 'users/' to avoid conflict
        path('api/masters/', include('Masters.urls')),
    path('api/sales/', include('Sales.urls')),
    path('api/lead/', include('Lead.urls')),
    path('api/sitevisit/', include(site_visit_router.urls)),
    path('api/inventory/', include('Inventory.urls')),
    path('api/dispatch/', include('Dispatch.urls')),
        path('api/invoice/', include('Invoice.urls')),
        path('api/receipts/', include('Receipts.urls')),
        path('api/delivery/', include('Delivery.urls')),
        path('api/thirdparty/', include('thirdparty.urls')),
        path('api/general/', include('General.urls')),
        path('api/dashboards/', include('dashboards.urls')),
        # Phase 1 — new modules
        path('api/inventory/', include('Inventory.urls')),
        path('api/booking/', include('Booking.urls')),
        path('api/documents/', include('Documents.urls')),
        path('api/re-reports/', include('RealEstateReports.urls')),

    ]

    urlpatterns = urlpatterns + app_urlpatterns

if  settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) # Workes Only in Development    
else:
    urlpatterns += [ path('static/<path:path>', serve, {'document_root': settings.STATIC_ROOT}),]

if not settings.USE_S3:
    if settings.DEBUG:
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) # Workes Only in Development
    else:
        media_url = settings.MEDIA_URL.lstrip('/')
        if not media_url.endswith('/'):
            media_url += '/'
        urlpatterns += [path(f'{media_url}<path:path>', serve, {'document_root': settings.MEDIA_ROOT})]

urlpatterns += [ path('firebase-messaging-sw.js', serve, {'document_root': settings.STATIC_ROOT, 'path': 'firebase-messaging-sw.js'}),]

urlpatterns += [
    
    path('privacypolicy', privacy_view, name='privacy'),
    path('schema/BASEYTGKDIUUGKHDIUIKHDSOUDSIUHDGUOOISOUOU/', login_required(SpectacularAPIView.as_view()), name='schema'),
    path('swagger/BASEYTGKDIUUGKHDIUIKHDSOUDSIUHDGUOOISOUOU/', login_required(SpectacularSwaggerView.as_view(url_name='schema')),name='schema-swagger-ui'),
    path('redoc/',login_required(SpectacularRedocView.as_view(url_name='schema')), name='schema-redoc'),
    re_path(r'^(?!api/).*', index_view),  # Only serve frontend for non-API routes
]

