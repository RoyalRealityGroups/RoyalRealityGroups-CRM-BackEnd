from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LeadViewSet, LeadFollowUpViewSet, CallLogViewSet, PublicLeadCreateView

router = DefaultRouter()
router.register(r'leads', LeadViewSet, basename='lead')
router.register(r'followups', LeadFollowUpViewSet, basename='lead-followup')
router.register(r'call-logs', CallLogViewSet, basename='call-log')

urlpatterns = [
    path('public/create/', PublicLeadCreateView.as_view(), name='public-lead-create'),
    path('', include(router.urls)),
]
