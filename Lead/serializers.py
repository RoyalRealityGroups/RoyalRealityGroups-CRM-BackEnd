from rest_framework import serializers
from .models import Lead, LeadStatusHistory, LeadFollowUp, LeadCrossCheck, LEAD_SOURCE_CHOICES, LEAD_STATUS_CHOICES


class LeadSerializer(serializers.ModelSerializer):
    assigned_employee_name = serializers.CharField(source='assigned_employee.name', read_only=True)
    status_display = serializers.CharField(read_only=True)
    lead_source_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = Lead
        fields = [
            'id', 'code', 'name', 'mobile', 'alternate_number', 'email',
            'budget', 'preferred_area', 'property_requirement', 'lead_source',
            'lead_source_display', 'assigned_employee', 'assigned_employee_name',
            'status', 'status_display', 'remarks',
            'cross_lead_override', 'cross_lead_override_reason',
            'created_on', 'modified_on', 'created_by_type', 'created_by_identifier',
            'modified_by_type', 'modified_by_identifier'
        ]
        read_only_fields = ('code', 'created_on', 'modified_on')
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        emp = instance.assigned_employee
        data['assigned_employee'] = {'id': str(emp.id), 'name': getattr(emp, 'name', None) or emp.username} if emp else None
        return data
    
    def create(self, validated_data):
        # Set created_by_type and created_by_identifier for audit
        user = self.context['request'].user
        validated_data['created_by_type'] = 'User'
        validated_data['created_by_identifier'] = str(user.id)
        validated_data['modified_by_type'] = 'User'
        validated_data['modified_by_identifier'] = str(user.id)
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Store previous status for history tracking
        instance._previous_status = instance.status
        # Set modified_by_type and modified_by_identifier for audit
        user = self.context['request'].user
        validated_data['modified_by_type'] = 'User'
        validated_data['modified_by_identifier'] = str(user.id)
        return super().update(instance, validated_data)


class LeadStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.name', read_only=True)
    from_status_display = serializers.CharField(read_only=True)
    to_status_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = LeadStatusHistory
        fields = '__all__'


class LeadFollowUpSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField(read_only=True)
    follow_up_type_display = serializers.CharField(read_only=True)
    lead_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = LeadFollowUp
        fields = '__all__'
        read_only_fields = ('lead', 'created_by')
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        lead = instance.lead
        data['lead'] = {
            'id': str(lead.id),
            'name': lead.name,
            'code': lead.code,
            'mobile': lead.mobile,
            'status': lead.status,
            'assigned_employee': getattr(lead.assigned_employee, 'name', None) or (lead.assigned_employee.username if lead.assigned_employee else None),
        }
        return data
    
    def get_created_by_name(self, obj):
        if obj.created_by:
            return getattr(obj.created_by, 'name', None) or obj.created_by.username
        return None
    
    def create(self, validated_data):
        lead_id = validated_data.pop('lead_id', None)
        if lead_id:
            validated_data['lead'] = Lead.objects.get(id=lead_id)
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        lead_id = validated_data.pop('lead_id', None)
        if lead_id:
            validated_data['lead'] = Lead.objects.get(id=lead_id)
        return super().update(instance, validated_data)


class LeadCrossCheckSerializer(serializers.ModelSerializer):
    duplicate_of_name = serializers.CharField(source='duplicate_of.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    
    class Meta:
        model = LeadCrossCheck
        fields = '__all__'


# Cross Lead Check Serializer
class CrossLeadCheckRequestSerializer(serializers.Serializer):
    mobile = serializers.CharField(required=False, allow_blank=True)
    alternate_number = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)


class CrossLeadCheckResponseSerializer(serializers.Serializer):
    has_duplicate = serializers.BooleanField()
    duplicates = LeadSerializer(many=True, read_only=True)
    message = serializers.CharField()


# Choices for reference
LEAD_SOURCE_CHOICES_LIST = [{'value': k, 'label': v} for k, v in LEAD_SOURCE_CHOICES]
LEAD_STATUS_CHOICES_LIST = [{'value': k, 'label': v} for k, v in LEAD_STATUS_CHOICES]

FOLLOW_UP_TYPE_CHOICES = [
    ('CALL', 'Call'),
    ('WHATSAPP', 'WhatsApp'),
    ('MEETING', 'Meeting'),
    ('SITE_VISIT', 'Site Visit'),
]
FOLLOW_UP_TYPE_CHOICES_LIST = [{'value': k, 'label': v} for k, v in FOLLOW_UP_TYPE_CHOICES]
