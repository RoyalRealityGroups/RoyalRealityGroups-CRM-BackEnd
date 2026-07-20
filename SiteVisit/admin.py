from django.contrib import admin
from .models import SiteVisit, SiteVisitPhoto


class SiteVisitPhotoInline(admin.TabularInline):
    model = SiteVisitPhoto
    extra = 0


@admin.register(SiteVisit)
class SiteVisitAdmin(admin.ModelAdmin):
    list_display = ['code', 'customer_name', 'project_name', 'visit_date', 'assigned_employee', 'status']
    list_filter = ['status', 'visit_date']
    search_fields = ['customer_name', 'project_name', 'code']
    inlines = [SiteVisitPhotoInline]
    readonly_fields = ['code', 'created_on', 'modified_on']
