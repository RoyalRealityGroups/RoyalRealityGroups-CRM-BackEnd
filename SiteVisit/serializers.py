from rest_framework import serializers
from .models import SiteVisit


class SiteVisitSerializer(serializers.ModelSerializer):
    assigned_employee_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = SiteVisit
        fields = [
            'id', 'customer_name', 'project_name', 'visit_date',
            'assigned_employee', 'assigned_employee_name',
            'status', 'customer_feedback', 'remarks', 'photos',
            'created_by', 'created_by_name',
            'created_on', 'modified_on',
        ]
        read_only_fields = ['id', 'created_on', 'modified_on', 'created_by']

    def _full_name(self, user):
        if not user:
            return None
        full = f"{user.first_name} {user.last_name}".strip()
        return full or user.username

    def get_assigned_employee_name(self, obj):
        return self._full_name(obj.assigned_employee)

    def get_created_by_name(self, obj):
        return self._full_name(obj.created_by)