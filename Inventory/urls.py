from rest_framework.routers import DefaultRouter
from .views import PlotViewSet, FlatViewSet

router = DefaultRouter()
router.register(r'plots', PlotViewSet, basename='plot')
router.register(r'flats', FlatViewSet, basename='flat')

urlpatterns = router.urls