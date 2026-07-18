from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LeadViewSet, LeadFollowUpViewSet, SiteVisitViewSet

router = DefaultRouter()
router.register(r'leads', LeadViewSet, basename='lead')
router.register(r'followups', LeadFollowUpViewSet, basename='lead-followup')
router.register(r'site-visits', SiteVisitViewSet, basename='site-visit')

urlpatterns = [
    path('', include(router.urls)),
]
