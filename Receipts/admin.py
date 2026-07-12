from django.contrib import admin
from .models import (
    Receipt,
    ReceiptAllocation,
    ReceiptAttachment,
    CustomerCredit,
    CreditUtilization,
    CustomerLedgerEntry,
)


class ReceiptAllocationInline(admin.TabularInline):
    model = ReceiptAllocation
    extra = 1
    readonly_fields = ('invoice_number', 'invoice_date', 'invoice_amount', 'invoice_balance')
    
    def invoice_number(self, obj):
        return obj.invoice.invoice_number if obj.invoice else None
    
    def invoice_date(self, obj):
        return obj.invoice.invoice_date if obj.invoice else None
    
    def invoice_amount(self, obj):
        return obj.invoice.grand_total if obj.invoice else None
    
    def invoice_balance(self, obj):
        return obj.invoice.balance_amount if obj.invoice else None


class ReceiptAttachmentInline(admin.TabularInline):
    model = ReceiptAttachment
    extra = 1


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'receipt_date', 'customer_name', 'payment_mode', 'total_amount', 'authorized_status')
    list_filter = ('payment_mode', 'customer_type', 'authorized_status', 'receipt_date')
    search_fields = ('receipt_number', 'code', 'reference_number')
    readonly_fields = ('code', 'receipt_number', 'created_on', 'modified_on')
    inlines = [ReceiptAllocationInline, ReceiptAttachmentInline]
    
    def customer_name(self, obj):
        return obj.get_customer_name()


@admin.register(CustomerCredit)
class CustomerCreditAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'customer_type', 'credit_amount', 'available_amount', 'receipt_number', 'created_on')
    list_filter = ('customer_type', 'authorized_status', 'created_on')
    search_fields = ('code', 'retailer__name', 'distributor__name', 'superstockist__name')
    readonly_fields = ('code', 'created_on', 'modified_on')
    
    def customer_name(self, obj):
        if obj.customer_type == 'RETAILER' and obj.retailer:
            return obj.retailer.name
        elif obj.customer_type == 'DISTRIBUTOR' and obj.distributor:
            return obj.distributor.name
        elif obj.customer_type == 'SUPERSTOCKIST' and obj.superstockist:
            return obj.superstockist.name
        return None
    
    def receipt_number(self, obj):
        return obj.receipt.receipt_number if obj.receipt else 'N/A'


@admin.register(CreditUtilization)
class CreditUtilizationAdmin(admin.ModelAdmin):
    list_display = ('credit', 'receipt', 'utilized_amount', 'utilized_on')
    list_filter = ('utilized_on',)
    search_fields = ('credit__code', 'receipt__receipt_number')
    readonly_fields = ('utilized_on',)


@admin.register(CustomerLedgerEntry)
class CustomerLedgerEntryAdmin(admin.ModelAdmin):
    list_display = (
        'posting_date', 'document_type', 'document_number', 'customer_type',
        'debit_amount', 'credit_amount', 'entry_status'
    )
    list_filter = ('document_type', 'customer_type', 'entry_status', 'posting_date')
    search_fields = (
        'document_number', 'code', 'retailer__name', 'distributor__name',
        'superstockist__name'
    )
    readonly_fields = ('code', 'created_on', 'modified_on')
