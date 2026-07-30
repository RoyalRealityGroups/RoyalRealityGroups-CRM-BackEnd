from django.contrib import admin
from .models import Project, ProjectStatusHistory, ProjectImage


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'developer_name', 'project_type',
                    'approval_type', 'status', 'location', 'is_active', 'is_deleted',
                    'created_on')
    list_filter = ('status', 'project_type', 'approval_type', 'is_active', 'is_deleted')
    search_fields = ('code', 'name', 'developer_name')
    ordering = ('name',)
    list_per_page = 25
    readonly_fields = ('code', 'created_on', 'modified_on',
                       'created_by_identifier', 'modified_by_identifier')

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ProjectStatusHistory)
class ProjectStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('project', 'from_status', 'to_status', 'changed_by_identifier', 'created_on')
    list_filter = ('to_status',)
    search_fields = ('project__code', 'project__name', 'changed_by_identifier')
    readonly_fields = ('project', 'from_status', 'to_status', 'changed_by_identifier', 'remarks', 'created_on')
    ordering = ('-created_on',)
    list_per_page = 25

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ProjectImage)
class ProjectImageAdmin(admin.ModelAdmin):
    list_display = ('project', 'image_type', 'title', 'order', 'created_on')
    list_filter = ('image_type',)
    search_fields = ('project__code', 'project__name', 'title')
