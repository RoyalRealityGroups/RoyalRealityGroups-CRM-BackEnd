from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlotInventoryViewSet, FlatInventoryViewSet

router = DefaultRouter()
router.register(r'plots', PlotInventoryViewSet, basename='plot')
router.register(r'flats', FlatInventoryViewSet, basename='flat')

urlpatterns = [
    path('', include(router.urls)),
]
