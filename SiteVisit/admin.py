from django.contrib import admin
from .models import SiteVisit


@admin.register(SiteVisit)
class SiteVisitAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'project_name', 'visit_date', 'assigned_employee', 'status')
    list_filter = ('status', 'visit_date')
    search_fields = ('customer_name', 'project_name')