from rest_framework import serializers
from .models import SiteVisit, SiteVisitPhoto, SITE_VISIT_STATUS_CHOICES, SITE_VISIT_STATUS_TRANSITIONS


class SiteVisitPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteVisitPhoto
        fields = ['id', 'photo', 'caption', 'uploaded_on']


class SiteVisitSerializer(serializers.ModelSerializer):
    """
    Site Visit serializer — Module 5.

    Schedule fields: customer_name, project, visit_date, assigned_employee
    Completion fields: customer_feedback, remarks, photos (read-only nested)
    """
    lead_name = serializers.CharField(source='lead.name', read_only=True)
    project_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    assigned_employee_name = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    photos = SiteVisitPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = SiteVisit
        fields = [
            'id', 'code',
            'lead', 'lead_name',
            'customer_name',
            'project', 'project_name',
            'visit_date',
            'assigned_employee', 'assigned_employee_name',
            'status', 'status_display',
            'customer_feedback', 'remarks',
            'photos',
            'created_on', 'modified_on',
            'created_by_type', 'created_by_identifier',
        ]
        read_only_fields = ('code', 'created_on', 'modified_on')

    def get_assigned_employee_name(self, obj):
        if obj.assigned_employee:
            return (
                f"{obj.assigned_employee.first_name} {obj.assigned_employee.last_name}".strip()
                or obj.assigned_employee.username
            )
        return None

    def validate_status(self, value):
        """Enforce status transition rules on update."""
        instance = self.instance
        if instance is None:
            return value
        if value == instance.status:
            return value
        allowed = SITE_VISIT_STATUS_TRANSITIONS.get(instance.status, set())
        if value not in allowed:
            raise serializers.ValidationError(
                f"Cannot transition from {instance.status} to {value}. "
                f"Allowed transitions: {sorted(allowed) or 'none (terminal state)'}."
            )
        return value

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Fallback to FK project name if stored project_name is empty
        if not data.get('project_name') and instance.project:
            data['project_name'] = instance.project.name
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by_type'] = 'User'
        validated_data['created_by_identifier'] = str(user.id)
        validated_data['modified_by_type'] = 'User'
        validated_data['modified_by_identifier'] = str(user.id)
        # Auto-populate project_name from FK if not provided
        project = validated_data.get('project')
        if project and not validated_data.get('project_name'):
            validated_data['project_name'] = project.name
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by_type'] = 'User'
        validated_data['modified_by_identifier'] = str(user.id)
        # Auto-populate project_name from FK if not provided
        project = validated_data.get('project')
        if project and not validated_data.get('project_name'):
            validated_data['project_name'] = project.name
        return super().update(instance, validated_data)


# Choices list for API responses
SITE_VISIT_STATUS_CHOICES_LIST = [{'value': k, 'label': v} for k, v in SITE_VISIT_STATUS_CHOICES]
