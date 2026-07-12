from rest_framework import serializers
from django.db.models import Q
from django.apps import apps
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
        user = self.context['request'].user
        mobile = (validated_data.get('mobile') or '').strip()
        alt = (validated_data.get('alternate_number') or '').strip()
        email = (validated_data.get('email') or '').strip()
        override = validated_data.get('cross_lead_override', False)

        duplicates = self._find_duplicates(mobile, alt, email, exclude_id=None)
        if duplicates and not override:
            dup_payload = [self._duplicate_payload(d, mobile, alt, email) for d in duplicates]
            raise serializers.ValidationError({
                'non_field_errors': ['Duplicate lead(s) exist. Provide an override reason to proceed.'],
                'has_duplicates': True,
                'duplicates': dup_payload,
            })

        validated_data['created_by_type'] = 'User'
        validated_data['created_by_identifier'] = str(user.id)
        validated_data['modified_by_type'] = 'User'
        validated_data['modified_by_identifier'] = str(user.id)
        lead = super().create(validated_data)

        if duplicates:
            self._create_duplicate_notification(lead, duplicates, user)
        return lead

    def _find_duplicates(self, mobile, alt, email, exclude_id=None):
        if not any([mobile, alt, email]):
            return []
        qs = Lead.objects.all()
        if exclude_id:
            qs = qs.exclude(id=exclude_id)
        dup_filters = Q()
        if mobile:
            dup_filters = dup_filters | Q(mobile=mobile)
        if alt:
            dup_filters = dup_filters | Q(alternate_number=alt)
        if email:
            dup_filters = dup_filters | Q(email__iexact=email)
        return list(qs.filter(dup_filters).distinct()[:10])

    def _duplicate_payload(self, dup, mobile, alt, email):
        if mobile and dup.mobile == mobile:
            match_field, match_value = 'mobile', mobile
        elif alt and dup.alternate_number == alt:
            match_field, match_value = 'alternate_number', alt
        elif email and dup.email and dup.email.lower() == email.lower():
            match_field, match_value = 'email', email
        else:
            match_field, match_value = 'unknown', ''
        last_fu = dup.follow_ups.order_by('-follow_up_date').values_list('follow_up_date', flat=True).first()
        owner = dup.assigned_employee
        owner_name = ''
        if owner:
            owner_name = f"{owner.first_name} {owner.last_name}".strip() or owner.username
        return {
            'lead': {
                'id': str(dup.id),
                'code': dup.code,
                'name': dup.name,
                'status': dup.get_status_display(),
                'status_code': dup.status,
                'last_follow_up_date': last_fu.isoformat() if last_fu else None,
                'assigned_employee': {'name': owner_name} if owner_name else None,
            },
            'match_field': match_field,
            'match_value': match_value,
        }

    def _create_duplicate_notification(self, lead, duplicates, user):
        try:
            Notif = apps.get_model('System', 'Notification')
            NU = apps.get_model('System', 'NotificationUsers')
        except Exception:
            return
        dup_text = ', '.join(d.name for d in duplicates[:3])
        more = f' and {len(duplicates) - 3} more' if len(duplicates) > 3 else ''
        try:
            notif = Notif.objects.create(
                subject='Duplicate Lead Detected',
                body=f'Lead "{lead.name}" matches existing: {dup_text}{more}',
                type='lead_duplicate',
                ref=str(lead.id),
                web_navigation_url=f'/lead/view/{lead.id}',
                message_priority=2,
                notification_type=1,
            )
            NU.objects.create(
                user_identifier=str(user.id),
                user_type='User',
                notification=notif,
                seen=0,
            )
        except Exception:
            pass
    
    def update(self, instance, validated_data):
        # Store previous status for history tracking
        instance._previous_status = instance.status
        # Set modified_by_type and modified_by_identifier for audit
        user = self.context['request'].user
        validated_data['modified_by_type'] = 'User'
        validated_data['modified_by_identifier'] = str(user.id)

        # Cross lead check on update too (exclude the current instance)
        mobile = (validated_data.get('mobile') or instance.mobile or '').strip()
        alt = (validated_data.get('alternate_number') or instance.alternate_number or '').strip()
        email = (validated_data.get('email') or instance.email or '').strip()
        override = validated_data.get('cross_lead_override', False)

        duplicates = self._find_duplicates(mobile, alt, email, exclude_id=instance.id)
        if duplicates and not override:
            dup_payload = [self._duplicate_payload(d, mobile, alt, email) for d in duplicates]
            fields = sorted({d['match_field'] for d in dup_payload if d['match_field'] != 'unknown'})
            field_text = ', '.join(fields) if fields else 'mobile/email/alternate_number'
            raise serializers.ValidationError({
                'non_field_errors': [
                    f"Duplicate lead(s) found on {field_text}. Provide an override reason to proceed."
                ],
                'has_duplicates': True,
                'duplicates': dup_payload,
                'matched_fields': fields,
            })
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
