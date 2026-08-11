from django.contrib import admin
from .models import (
    AvailabilityProject, AvailabilityProjectImage,
    AvailabilityBlock, AvailabilityUnit,
)


class AvailabilityProjectImageInline(admin.TabularInline):
    model = AvailabilityProjectImage
    extra = 0
    fields = ['image', 'image_type', 'title', 'order']


class AvailabilityBlockInline(admin.TabularInline):
    model = AvailabilityBlock
    extra = 0
    fields = ['name', 'description', 'total_floors', 'order']
    show_change_link = True


@admin.register(AvailabilityProject)
class AvailabilityProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'developer_name', 'project_type', 'location', 'status', 'is_active', 'created_on']
    list_filter = ['project_type', 'status', 'is_active', 'approval_type']
    search_fields = ['name', 'developer_name', 'location', 'code']
    readonly_fields = ['code', 'created_on', 'modified_on']
    inlines = [AvailabilityBlockInline, AvailabilityProjectImageInline]

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_deleted=False)


class AvailabilityUnitInline(admin.TabularInline):
    model = AvailabilityUnit
    extra = 0
    fields = ['unit_number', 'unit_type', 'floor', 'area_sqft', 'price', 'status']

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_deleted=False)


@admin.register(AvailabilityBlock)
class AvailabilityBlockAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'total_floors', 'order', 'created_on']
    list_filter = ['project']
    search_fields = ['name', 'project__name']
    readonly_fields = ['created_on', 'modified_on']
    inlines = [AvailabilityUnitInline]

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_deleted=False)


@admin.register(AvailabilityUnit)
class AvailabilityUnitAdmin(admin.ModelAdmin):
    list_display = ['unit_number', 'block', 'unit_type', 'floor', 'area_sqft', 'price', 'status']
    list_filter = ['status', 'unit_type', 'facing']
    search_fields = ['unit_number', 'block__name', 'block__project__name']
    readonly_fields = ['created_on', 'modified_on']

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_deleted=False)
