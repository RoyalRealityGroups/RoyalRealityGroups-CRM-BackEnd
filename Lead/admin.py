from django.contrib import admin
from .models import Lead, LeadStatusHistory, LeadFollowUp, LeadCrossCheck


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'mobile', 'status', 'lead_source', 'assigned_employee', 'created_on')
    list_filter = ('status', 'lead_source', 'created_on')
    search_fields = ('name', 'mobile', 'email', 'code')
    readonly_fields = ('code', 'created_on', 'modified_on', 'created_by_type', 'created_by_identifier')
    date_hierarchy = 'created_on'
    raw_id_fields = ('assigned_employee',)


@admin.register(LeadStatusHistory)
class LeadStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('lead', 'from_status', 'to_status', 'changed_by', 'created_on')
    list_filter = ('to_status', 'created_on')
    search_fields = ('lead__name',)
    raw_id_fields = ('lead', 'changed_by')


@admin.register(LeadFollowUp)
class LeadFollowUpAdmin(admin.ModelAdmin):
    list_display = ('lead', 'follow_up_date', 'follow_up_type', 'next_follow_up_date', 'created_by')
    list_filter = ('follow_up_type', 'follow_up_date', 'next_follow_up_date')
    search_fields = ('lead__name', 'discussion_notes')
    raw_id_fields = ('lead', 'created_by')
    date_hierarchy = 'follow_up_date'


@admin.register(LeadCrossCheck)
class LeadCrossCheckAdmin(admin.ModelAdmin):
    list_display = ('original_lead', 'duplicate_of', 'match_field', 'created_by', 'created_on')
    search_fields = ('original_lead__name', 'duplicate_of__name')
    raw_id_fields = ('original_lead', 'duplicate_of', 'created_by')
