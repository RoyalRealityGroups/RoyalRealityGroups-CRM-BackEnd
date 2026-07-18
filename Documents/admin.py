from django.contrib import admin
from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'document_type', 'linked_to', 'project', 'lead', 'booking', 'is_public', 'created_on')
    list_filter = ('document_type', 'linked_to', 'is_public')
    search_fields = ('title', 'code', 'original_filename')
    ordering = ('-created_on',)
    raw_id_fields = ('project', 'lead', 'booking')
