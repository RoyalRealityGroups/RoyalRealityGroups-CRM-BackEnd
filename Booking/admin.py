from django.contrib import admin
from .models import Booking, BookingStatusHistory


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('code', 'customer_name', 'project', 'unit_number', 'booking_amount', 'booking_date', 'status', 'sales_executive')
    list_filter = ('status', 'project', 'unit_type')
    search_fields = ('customer_name', 'customer_mobile', 'code', 'unit_number')
    ordering = ('-booking_date',)
    raw_id_fields = ('lead', 'plot', 'flat', 'sales_executive')


@admin.register(BookingStatusHistory)
class BookingStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('booking', 'from_status', 'to_status', 'changed_by', 'changed_on')
    list_filter = ('to_status',)
    ordering = ('-changed_on',)
