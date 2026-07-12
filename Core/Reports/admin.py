from django.contrib import admin
from import_export.admin import ImportExportMixin

from Core.Core.utils.utils import ac_filter
from Core.Reports.models import PdfTemplate, ScheduledEmail, ImportRequest
import json
from django import forms

class PdfTemplateAdminForm(forms.ModelForm):
    json_file = forms.FileField(required=False, label="Upload JSON File")
    # extract_vars = forms.BaseModelFormSet(default= True, required=False, label="Extract Variables from JSON File file")

    class Meta:
        model = PdfTemplate
        fields = ['screen', 'screen_name', 'is_active', 'template_data']

    def clean(self):
        cleaned_data = super().clean()
        uploaded_file = self.files.get('json_file')

        if uploaded_file:
            try:
                json_data = json.load(uploaded_file)
                cleaned_data['template_data'] = json_data
            except json.JSONDecodeError:
                raise forms.ValidationError("Invalid JSON file uploaded.")

        return cleaned_data
    

class PdfTemplateAdmin(ImportExportMixin, admin.ModelAdmin):
    form = PdfTemplateAdminForm

    fields = [
        'name', 'screen', 'screen_name', 'is_active', 'template_data', 'variables_data', 'json_file'
    ]

    list_display = (
        'id', 'name', 'screen', 'screen_name', 'is_active', 'template_data', 'variables_data',
        'created_on', 'modified_on'
    )

    list_filter = [
        ac_filter('screen'),
    ]

    ordering = ('created_on',)
    search_fields = ['screen_name', 'name']
    list_per_page = 25

    readonly_fields = ['created_on', 'modified_on']

    def has_delete_permission(self, request, obj=None):
        return False

# Register your models here.

admin.site.register(ScheduledEmail)
admin.site.register(ImportRequest)
admin.site.register(PdfTemplate, PdfTemplateAdmin)
