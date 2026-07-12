from django.urls import path
from .views import (
    ReceiptListView,
    ReceiptDetailView,
    ReceiptCreateView,
    PendingInvoicesForReceiptView,
    GenerateReceiptNumberView,
    CustomerCreditBalanceView,
    CustomerLedgerListView,
    CustomerLedgerSummaryView,
    ReceiptTotalAmountView,
    ReceiptLastWeekDailyTotalView,
)

urlpatterns = [
    path('', ReceiptListView.as_view(), name='receipt-list'),
    path('create/', ReceiptCreateView.as_view(), name='receipt-create'),
    path('<uuid:pk>/', ReceiptDetailView.as_view(), name='receipt-detail'),
    path('pending-invoices/', PendingInvoicesForReceiptView.as_view(), name='pending-invoices-for-receipt'),
    path('generate-number/', GenerateReceiptNumberView.as_view(), name='generate-receipt-number'),
    path('customer-credit-balance/', CustomerCreditBalanceView.as_view(), name='customer-credit-balance'),
    path('customer-ledger/', CustomerLedgerListView.as_view(), name='customer-ledger-list'),
    path('customer-ledger-summary/', CustomerLedgerSummaryView.as_view(), name='customer-ledger-summary'),
    path('total-amount/', ReceiptTotalAmountView.as_view(), name='receipt-total-amount'),
    path('last-week-daily-total/', ReceiptLastWeekDailyTotalView.as_view(), name='receipt-last-week-daily-total'),
]
