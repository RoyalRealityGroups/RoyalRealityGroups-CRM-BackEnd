from django.contrib import admin
from .models import ProofOfDelivery, ProofOfDeliveryFile


@admin.register(ProofOfDelivery)
class ProofOfDeliveryAdmin(admin.ModelAdmin):
    list_display = ['code', 'invoice', 'sales_order', 'status', 'receiver_name', 'delivered_date']
    search_fields = ['code', 'invoice__invoice_number', 'sales_order__order_number', 'receiver_name']
    list_filter = ['status', 'delivered_date']


@admin.register(ProofOfDeliveryFile)
class ProofOfDeliveryFileAdmin(admin.ModelAdmin):
    list_display = ['proof', 'file', 'description']
    list_filter = ['created_on']
