from django.urls import path
from . import views
from .attachment_views import (
    SalesOrderAttachmentListView,
    SalesOrderAttachmentUploadView,
    SalesOrderAttachmentDeleteView
)

urlpatterns = [
    # Sales Order Reports
    path('reports/orders/', views.SalesOrderReportView.as_view(), name='sales-order-report'),
    path('reports/orders/export/', views.SalesOrderReportExportView.as_view(), name='sales-order-report-export'),
    
    # Sales Orders
    path('orders/', views.SalesOrderList.as_view(), name='sales-order-list'),
    path('orders/customer-dropdown/', views.SalesOrderCustomerDropdown.as_view(), name='sales-order-customer-dropdown'),
    path('orders/status-count/', views.SalesOrderStatusCountView.as_view(), name='sales-order-status-count'),
    path('orders/weekly-customer-count/', views.SalesOrderWeeklyCustomerTypeCountView.as_view(), name='sales-order-weekly-customer-count'),
    path('orders/generate-document-number/', views.GenerateSalesOrderNumber.as_view(), name='generate-sales-order-number'),
    path('orders/pending-orders/', views.GetCustomerPendingSalesOrdersView.as_view(), name='pending-sales-orders'),
    path('orders/frequent-items/', views.GetCustomerFrequentItemsView.as_view(), name='frequent-items'),
    path('orders/get-applicable-schemes/', views.GetApplicableSchemesView.as_view(), name='get-applicable-schemes'),
    path('orders/fulfilment-percentage/', views.OrderFulfilmentPercentageView.as_view(), name='order-fulfilment-percentage'),
    path('orders/<uuid:pk>/available-schemes/', views.SalesOrderAvailableSchemesView.as_view(), name='available-schemes'),
    path('orders/<uuid:pk>/', views.SalesOrderDetail.as_view(), name='sales-order-detail'),
    path('orders/<uuid:pk>/apply-schemes/', views.ApplySchemesToOrderView.as_view(), name='apply-schemes'),
    path('orders/<uuid:pk>/approve/', views.SalesOrderApprove.as_view(), name='sales-order-approve'),
    path('orders/<uuid:pk>/reject/', views.SalesOrderReject.as_view(), name='sales-order-reject'),
    path('orders/<uuid:pk>/process/', views.SalesOrderProcess.as_view(), name='sales-order-process'),
    path('orders/<uuid:pk>/invoice/', views.SalesOrderInvoice.as_view(), name='sales-order-invoice'),
    path('orders/<uuid:pk>/deliver/', views.SalesOrderApprove.as_view(), name='sales-order-deliver'),
    path('orders/<uuid:order_id>/history/', views.SalesOrderHistoryList.as_view(), name='sales-order-history'),
    
    # Sales Order Attachments
    path('orders/<uuid:pk>/attachments/', SalesOrderAttachmentListView.as_view(), name='sales-order-attachments'),
    path('orders/<uuid:pk>/upload_attachment/', SalesOrderAttachmentUploadView.as_view(), name='sales-order-upload-attachment'),
    path('orders/<uuid:pk>/attachments/<uuid:attachment_id>/', SalesOrderAttachmentDeleteView.as_view(), name='sales-order-delete-attachment'),
    
    # Item Price Cascade
    path('item-price/', views.GetItemPriceCascade.as_view(), name='item-price-cascade'),
]
