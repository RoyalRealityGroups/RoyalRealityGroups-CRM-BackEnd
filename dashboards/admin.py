"""
Django admin configuration for Dashboards app.
"""
from django.contrib import admin
from .models import WidgetType, Dashboard, DashboardWidget, DashboardGroup


@admin.register(WidgetType)
class WidgetTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'category', 'is_system', 'is_deleted', 'display_order']
    list_filter = ['category', 'is_system', 'is_deleted']
    search_fields = ['name', 'code', 'description']
    ordering = ['category', 'display_order', 'name']


class DashboardWidgetInline(admin.TabularInline):
    model = DashboardWidget
    extra = 0
    fields = ['title', 'widget_type', 'position_x', 'position_y', 'width', 'height', 'is_visible']


class DashboardGroupInline(admin.TabularInline):
    model = DashboardGroup
    extra = 0
    fields = ['group', 'display_order', 'is_default', 'can_customize']


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ['name','visibility', 'is_default', 'is_system', 'is_deleted', 'display_order']
    list_filter = ['visibility', 'is_default', 'is_system', 'is_deleted']
    search_fields = ['name', 'description']
    ordering = ['display_order', 'name']
    inlines = [DashboardWidgetInline, DashboardGroupInline]


@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = ['title', 'dashboard', 'widget_type', 'position_x', 'position_y', 'width', 'height', 'is_visible']
    list_filter = ['dashboard', 'widget_type', 'is_visible', 'is_deleted']
    search_fields = ['title', 'subtitle', 'dashboard__name']
    ordering = ['dashboard', 'position_y', 'position_x']


@admin.register(DashboardGroup)
class DashboardGroupAdmin(admin.ModelAdmin):
    list_display = ['dashboard', 'group', 'display_order', 'is_default', 'can_customize']
    list_filter = ['group', 'is_default', 'can_customize']
    search_fields = ['dashboard__name', 'group__name']
    ordering = ['group', 'display_order']
