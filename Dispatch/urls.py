from django.urls import path
from . import views
from .views import DispatchPlanningReportView, DispatchPlanningReportExportView

urlpatterns = [
    # Dispatch Plans
    path('plans/', views.DispatchPlanList.as_view(), name='dispatch-plan-list'),
    path('plans/<uuid:pk>/', views.DispatchPlanDetail.as_view(), name='dispatch-plan-detail'),
    
    # Attachments
    path('<uuid:pk>/attachments/', views.DispatchPlanAttachmentList.as_view(), name='dispatch-plan-attachments'),
    path('<uuid:pk>/attachments/<uuid:att_pk>/', views.DispatchPlanAttachmentDetail.as_view(), name='dispatch-plan-attachment-detail'),
    
    # Available Orders
    path('available-orders/', views.AvailableOrdersForDispatch.as_view(), name='available-orders-dispatch'),
    
    # Utilities
    path('generate-number/', views.GenerateDispatchNumber.as_view(), name='generate-dispatch-number'),
    path('dispatchplan/status-count/', views.DispatchPlanStatusCountView.as_view(), name='dispatch-plan-status-count'),
    
    # Reports
    path('reports/planning/', DispatchPlanningReportView.as_view(), name='dispatch-planning-report'),
    path('reports/planning/export/', DispatchPlanningReportExportView.as_view(), name='dispatch-planning-report-export'),
]