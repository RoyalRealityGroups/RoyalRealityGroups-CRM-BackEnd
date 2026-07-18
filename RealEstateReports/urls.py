from django.urls import path
from .views import (
    LeadReportBySourceView,
    LeadReportByEmployeeView,
    LeadReportByProjectView,
    LeadReportByStatusView,
    SiteVisitReportView,
    BookingReportView,
    RevenueReportView,
    EmployeePerformanceReportView,
    DashboardSummaryView,
)

urlpatterns = [
    # Lead Reports
    path('leads/by-source/', LeadReportBySourceView.as_view(), name='report-lead-by-source'),
    path('leads/by-employee/', LeadReportByEmployeeView.as_view(), name='report-lead-by-employee'),
    path('leads/by-project/', LeadReportByProjectView.as_view(), name='report-lead-by-project'),
    path('leads/by-status/', LeadReportByStatusView.as_view(), name='report-lead-by-status'),

    # Site Visit Reports
    path('site-visits/', SiteVisitReportView.as_view(), name='report-site-visits'),

    # Sales / Booking Reports
    path('bookings/', BookingReportView.as_view(), name='report-bookings'),
    path('revenue/', RevenueReportView.as_view(), name='report-revenue'),

    # Employee Performance
    path('employee-performance/', EmployeePerformanceReportView.as_view(), name='report-employee-performance'),

    # Combined dashboard summary
    path('dashboard-summary/', DashboardSummaryView.as_view(), name='report-dashboard-summary'),
]
