from django.contrib import admin
from .models import DispatchPlan, DispatchItem


@admin.register(DispatchPlan)
class DispatchPlanAdmin(admin.ModelAdmin):
    list_display = ['dispatch_number', 'dispatch_date', 'location', 'status', 'total_orders', 'total_value']
    list_filter = ['status', 'location', 'dispatch_date']
    search_fields = ['dispatch_number', 'vehicle_details', 'driver_details']
    readonly_fields = ['dispatch_number', 'total_orders', 'total_value']


@admin.register(DispatchItem)
class DispatchItemAdmin(admin.ModelAdmin):
    list_display = ['dispatch_plan', 'sales_order', 'company', 'quantity_dispatched', 'status', 'delivery_sequence']
    list_filter = ['status', 'company', 'dispatch_plan__status']
    search_fields = ['dispatch_plan__dispatch_number', 'sales_order__order_number']
