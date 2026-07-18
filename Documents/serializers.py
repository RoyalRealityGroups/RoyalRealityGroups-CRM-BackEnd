from rest_framework import serializers
from .models import Document, DOCUMENT_TYPE_CHOICES, LINKED_TO_CHOICES

ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'xlsx', 'xls'}


class DocumentSerializer(serializers.ModelSerializer):
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    linked_to_display = serializers.CharField(source='get_linked_to_display', read_only=True)
    file_url = serializers.SerializerMethodField()
    file_extension = serializers.CharField(read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    lead_name = serializers.CharField(source='lead.name', read_only=True)
    booking_code = serializers.CharField(source='booking.code', read_only=True)
    uploaded_by = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id', 'code', 'title', 'document_type', 'document_type_display',
            'description', 'file', 'file_url', 'original_filename', 'file_size', 'file_extension',
            'linked_to', 'linked_to_display',
            'project', 'project_name',
            'lead', 'lead_name',
            'booking', 'booking_code',
            'is_public',
            'uploaded_by',
            'created_on', 'modified_on',
        ]
        read_only_fields = ('code', 'original_filename', 'file_size', 'created_on', 'modified_on')

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return obj.file_url

    def get_uploaded_by(self, obj):
        return obj.created_by_identifier or None

    def validate_file(self, value):
        ext = value.name.rsplit('.', 1)[-1].lower() if '.' in value.name else ''
        if ext not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"File type '.{ext}' not allowed. Supported: PDF, JPG, PNG, Excel."
            )
        # 25 MB max
        if value.size > 25 * 1024 * 1024:
            raise serializers.ValidationError("File size must not exceed 25 MB.")
        return value

    def validate(self, data):
        linked_to = data.get('linked_to', getattr(self.instance, 'linked_to', 'PROJECT'))
        if linked_to == 'PROJECT' and not data.get('project') and not getattr(self.instance, 'project', None):
            raise serializers.ValidationError({'project': 'Project is required when linked_to is PROJECT.'})
        if linked_to == 'LEAD' and not data.get('lead') and not getattr(self.instance, 'lead', None):
            raise serializers.ValidationError({'lead': 'Lead is required when linked_to is LEAD.'})
        if linked_to == 'BOOKING' and not data.get('booking') and not getattr(self.instance, 'booking', None):
            raise serializers.ValidationError({'booking': 'Booking is required when linked_to is BOOKING.'})
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by_type'] = 'User'
        validated_data['created_by_identifier'] = str(user.id)
        validated_data['modified_by_type'] = 'User'
        validated_data['modified_by_identifier'] = str(user.id)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by_type'] = 'User'
        validated_data['modified_by_identifier'] = str(user.id)
        return super().update(instance, validated_data)


DOCUMENT_TYPE_LIST = [{'value': k, 'label': v} for k, v in DOCUMENT_TYPE_CHOICES]
LINKED_TO_LIST = [{'value': k, 'label': v} for k, v in LINKED_TO_CHOICES]
