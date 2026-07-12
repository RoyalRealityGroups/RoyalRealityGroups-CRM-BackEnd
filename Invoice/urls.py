from django.urls import path
from .views import (
    InvoiceListCreateView,
    InvoiceDetailView,
    GenerateInvoiceFromDispatchView,
    GenerateInvoiceFromOrderView,
    AvailableDispatchPlansView,
    AvailableOrdersForInvoiceView,
    AvailableCustomersForInvoiceView,
    GenerateInvoiceNumberView,
    CancelInvoiceView,
    GetCustomerPendingInvoicesView,
    InvoiceStatusCountView,
    InvoiceReportView,
    InvoiceReportExportView,
)

urlpatterns = [
    # Invoice Reports
    path('reports/invoices/', InvoiceReportView.as_view(), name='invoice-report'),
    path('reports/invoices/export/', InvoiceReportExportView.as_view(), name='invoice-report-export'),
    
    # Invoices
    path('invoices/', InvoiceListCreateView.as_view(), name='invoice-list'),
    path('invoices/status-count/', InvoiceStatusCountView.as_view(), name='invoice-status-count'),
    path('invoices/generate-from-dispatch/', GenerateInvoiceFromDispatchView.as_view(), name='generate-invoice-from-dispatch'),
    path('invoices/generate-from-order/', GenerateInvoiceFromOrderView.as_view(), name='generate-invoice-from-order'),
    path('invoices/available-dispatches/', AvailableDispatchPlansView.as_view(), name='available-dispatches'),
    path('invoices/available-orders/', AvailableOrdersForInvoiceView.as_view(), name='available-orders'),
    path('invoices/available-customers/', AvailableCustomersForInvoiceView.as_view(), name='available-customers'),
    path('invoices/generate-number/', GenerateInvoiceNumberView.as_view(), name='generate-invoice-number'),
    path('invoices/pending-invoices/', GetCustomerPendingInvoicesView.as_view(), name='pending-invoices'),
    path('invoices/<uuid:pk>/', InvoiceDetailView.as_view(), name='invoice-detail'),
    path('invoices/<uuid:pk>/cancel/', CancelInvoiceView.as_view(), name='cancel-invoice'),
]
