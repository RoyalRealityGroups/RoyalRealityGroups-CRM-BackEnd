from django.contrib import admin
from .models import SalesOrder, SalesOrderItem, SalesOrderHistory
from .attachment_models import SalesOrderAttachment


class SalesOrderItemInline(admin.TabularInline):
    model = SalesOrderItem
    extra = 0
    readonly_fields = ('created_on', 'modified_on')


@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'order_date', 'customer_type', 'get_customer_name', 'status', 'grand_total', 'created_on')
    list_filter = ('status', 'customer_type', 'order_date')
    search_fields = ('order_number', 'remarks')
    readonly_fields = ('order_number', 'created_on', 'modified_on', 'created_by_type', 'created_by_identifier')
    inlines = [SalesOrderItemInline]
    date_hierarchy = 'order_date'
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'order_date', 'status')
        }),
        ('Customer Information', {
            'fields': ('customer_type', 'retailer', 'distributor', 'superstockist', 'credit_days')
        }),
        ('Billing Address', {
            'fields': ('billing_state', 'billing_city', 'billing_area', 'billing_address')
        }),
        ('Shipping Address', {
            'fields': ('shipping_state', 'shipping_city', 'shipping_area', 'shipping_address', 'same_as_billing')
        }),
        ('Financial', {
            'fields': ('subtotal', 'discount_amount', 'taxable_amount', 'tax_amount', 
                      'freight_charges', 'other_charges', 'round_off', 'grand_total')
        }),
        ('Additional Information', {
            'fields': ('remarks', 'internal_notes', 'attachment')
        }),
        ('Approval', {
            'fields': ('approved_by', 'approved_at', 'rejection_reason')
        }),
        ('Audit', {
            'fields': ('created_on', 'modified_on', 'created_by_type', 'created_by_identifier'),
            'classes': ('collapse',)
        }),
    )
    
    def get_customer_name(self, obj):
        return obj.get_customer_name()
    get_customer_name.short_description = 'Customer'


@admin.register(SalesOrderHistory)
class SalesOrderHistoryAdmin(admin.ModelAdmin):
    list_display = ('order', 'action', 'old_status', 'new_status', 'changed_by', 'changed_at')
    list_filter = ('action', 'changed_at')
    search_fields = ('order__order_number', 'remarks')
    readonly_fields = ('order', 'action', 'old_status', 'new_status', 'changes', 'remarks', 'changed_by', 'changed_at')
    date_hierarchy = 'changed_at'


@admin.register(SalesOrderAttachment)
class SalesOrderAttachmentAdmin(admin.ModelAdmin):
    list_display = ('sales_order', 'original_filename', 'created_on')
    list_filter = ('created_on',)
    search_fields = ('sales_order__order_number', 'original_filename', 'description')
    readonly_fields = ('created_on', 'modified_on')
    date_hierarchy = 'created_on'
    
    fieldsets = (
        ('Attachment Information', {
            'fields': ('sales_order', 'file', 'original_filename', 'description')
        }),
        ('Audit', {
            'fields': ('created_on', 'modified_on'),
            'classes': ('collapse',)
        }),
    )
