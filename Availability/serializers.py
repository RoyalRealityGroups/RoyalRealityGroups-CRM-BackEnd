from rest_framework import serializers
from .models import (
    AvailabilityProject, AvailabilityProjectImage,
    AvailabilityBlock, AvailabilityUnit,
    PROJECT_TYPE_CHOICES, PROJECT_STATUS_CHOICES,
    APPROVAL_TYPE_CHOICES, UNIT_STATUS_CHOICES,
    UNIT_TYPE_CHOICES, FACING_CHOICES,
)


# ──────────────────────────────────────────────────────────────────────────────
# UNIT
# ──────────────────────────────────────────────────────────────────────────────

class AvailabilityUnitSerializer(serializers.ModelSerializer):
    unit_type_display = serializers.CharField(source='get_unit_type_display', read_only=True)
    facing_display = serializers.CharField(source='get_facing_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    block_name = serializers.CharField(source='block.name', read_only=True)
    project_name = serializers.CharField(source='block.project.name', read_only=True)
    project_id = serializers.CharField(source='block.project.id', read_only=True)

    class Meta:
        model = AvailabilityUnit
        fields = [
            'id', 'block', 'block_name', 'project_id', 'project_name',
            'unit_number', 'unit_type', 'unit_type_display',
            'floor', 'area_sqft', 'area_sqyd', 'carpet_area_sqft',
            'facing', 'facing_display', 'price',
            'status', 'status_display', 'remarks',
            'created_on', 'modified_on',
        ]
        read_only_fields = ('created_on', 'modified_on')

    def _set_audit(self, validated_data, user, create=False):
        if create:
            validated_data['created_by_type'] = 'User'
            validated_data['created_by_identifier'] = str(user.id)
        validated_data['modified_by_type'] = 'User'
        validated_data['modified_by_identifier'] = str(user.id)
        return validated_data

    def create(self, validated_data):
        self._set_audit(validated_data, self.context['request'].user, create=True)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        self._set_audit(validated_data, self.context['request'].user)
        return super().update(instance, validated_data)


class AvailabilityUnitBulkSerializer(serializers.Serializer):
    """
    Accepts a list of units and creates/replaces them for a block.
    Used by the multi-step project creation wizard.
    """
    units = AvailabilityUnitSerializer(many=True)


# ──────────────────────────────────────────────────────────────────────────────
# BLOCK
# ──────────────────────────────────────────────────────────────────────────────

class AvailabilityBlockSerializer(serializers.ModelSerializer):
    units = AvailabilityUnitSerializer(many=True, read_only=True)
    # Computed summary counts
    total_units = serializers.IntegerField(read_only=True)
    available_units = serializers.IntegerField(read_only=True)
    booked_units = serializers.IntegerField(read_only=True)
    blocked_units = serializers.IntegerField(read_only=True)
    registered_units = serializers.IntegerField(read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model = AvailabilityBlock
        fields = [
            'id', 'project', 'project_name', 'name', 'description',
            'total_floors', 'order',
            'total_units', 'available_units', 'booked_units',
            'blocked_units', 'registered_units',
            'units',
            'created_on', 'modified_on',
        ]
        read_only_fields = ('created_on', 'modified_on')

    def _set_audit(self, validated_data, user, create=False):
        if create:
            validated_data['created_by_type'] = 'User'
            validated_data['created_by_identifier'] = str(user.id)
        validated_data['modified_by_type'] = 'User'
        validated_data['modified_by_identifier'] = str(user.id)
        return validated_data

    def create(self, validated_data):
        self._set_audit(validated_data, self.context['request'].user, create=True)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        self._set_audit(validated_data, self.context['request'].user)
        return super().update(instance, validated_data)


class AvailabilityBlockLightSerializer(serializers.ModelSerializer):
    """Lightweight block — no nested units. Used in project list/detail overview."""
    total_units = serializers.IntegerField(read_only=True)
    available_units = serializers.IntegerField(read_only=True)
    booked_units = serializers.IntegerField(read_only=True)
    blocked_units = serializers.IntegerField(read_only=True)
    registered_units = serializers.IntegerField(read_only=True)

    class Meta:
        model = AvailabilityBlock
        fields = [
            'id', 'project', 'name', 'description',
            'total_floors', 'order',
            'total_units', 'available_units', 'booked_units',
            'blocked_units', 'registered_units',
            'created_on', 'modified_on',
        ]
        read_only_fields = ('created_on', 'modified_on')


# ──────────────────────────────────────────────────────────────────────────────
# PROJECT IMAGE
# ──────────────────────────────────────────────────────────────────────────────

class AvailabilityProjectImageSerializer(serializers.ModelSerializer):
    image_type_display = serializers.CharField(source='get_image_type_display', read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = AvailabilityProjectImage
        fields = ['id', 'project', 'image', 'image_url', 'image_type',
                  'image_type_display', 'title', 'order', 'created_on']
        read_only_fields = ('created_on',)

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


# ──────────────────────────────────────────────────────────────────────────────
# PROJECT
# ──────────────────────────────────────────────────────────────────────────────

class AvailabilityProjectSerializer(serializers.ModelSerializer):
    project_type_display = serializers.CharField(source='get_project_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approval_type_display = serializers.CharField(source='get_approval_type_display', read_only=True)
    blocks = AvailabilityBlockLightSerializer(many=True, read_only=True)
    images = AvailabilityProjectImageSerializer(many=True, read_only=True)
    thumbnail_url = serializers.SerializerMethodField()
    brochure_url = serializers.SerializerMethodField()
    # Aggregate unit counts across all blocks
    total_units = serializers.IntegerField(read_only=True)
    available_units = serializers.IntegerField(read_only=True)
    booked_units = serializers.IntegerField(read_only=True)
    blocked_units = serializers.IntegerField(read_only=True)
    registered_units = serializers.IntegerField(read_only=True)

    class Meta:
        model = AvailabilityProject
        fields = [
            'id', 'code',
            'name', 'developer_name', 'project_type', 'project_type_display',
            'location', 'city', 'total_area',
            'price_range_min', 'price_range_max',
            'approval_type', 'approval_type_display', 'approval_number',
            'status', 'status_display',
            'possession_date', 'contact_person', 'contact_phone',
            'description', 'amenities', 'rera_number',
            'is_active',
            'thumbnail', 'thumbnail_url', 'brochure', 'brochure_url',
            'blocks', 'images',
            'total_units', 'available_units', 'booked_units',
            'blocked_units', 'registered_units',
            'created_on', 'modified_on',
        ]
        read_only_fields = ('code', 'created_on', 'modified_on')

    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        return None

    def get_brochure_url(self, obj):
        request = self.context.get('request')
        if obj.brochure and request:
            return request.build_absolute_uri(obj.brochure.url)
        return None

    def _set_audit(self, validated_data, user, create=False):
        if create:
            validated_data['created_by_type'] = 'User'
            validated_data['created_by_identifier'] = str(user.id)
        validated_data['modified_by_type'] = 'User'
        validated_data['modified_by_identifier'] = str(user.id)
        return validated_data

    def create(self, validated_data):
        self._set_audit(validated_data, self.context['request'].user, create=True)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        self._set_audit(validated_data, self.context['request'].user)
        return super().update(instance, validated_data)


class AvailabilityProjectListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for the project folder list (no nested units)."""
    project_type_display = serializers.CharField(source='get_project_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    thumbnail_url = serializers.SerializerMethodField()
    total_units = serializers.IntegerField(read_only=True)
    available_units = serializers.IntegerField(read_only=True)
    booked_units = serializers.IntegerField(read_only=True)
    blocked_units = serializers.IntegerField(read_only=True)
    registered_units = serializers.IntegerField(read_only=True)
    block_count = serializers.SerializerMethodField()

    class Meta:
        model = AvailabilityProject
        fields = [
            'id', 'code', 'name', 'developer_name',
            'project_type', 'project_type_display',
            'location', 'city', 'status', 'status_display',
            'is_active', 'thumbnail_url',
            'total_units', 'available_units', 'booked_units',
            'blocked_units', 'registered_units', 'block_count',
            'created_on',
        ]

    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        return None

    def get_block_count(self, obj):
        return obj.blocks.filter(is_deleted=False).count()


# ──────────────────────────────────────────────────────────────────────────────
# CHOICES PAYLOAD
# ──────────────────────────────────────────────────────────────────────────────

def build_choices():
    return {
        'project_types':  [{'value': k, 'label': v} for k, v in PROJECT_TYPE_CHOICES],
        'project_statuses': [{'value': k, 'label': v} for k, v in PROJECT_STATUS_CHOICES],
        'approval_types': [{'value': k, 'label': v} for k, v in APPROVAL_TYPE_CHOICES],
        'unit_statuses':  [{'value': k, 'label': v} for k, v in UNIT_STATUS_CHOICES],
        'unit_types':     [{'value': k, 'label': v} for k, v in UNIT_TYPE_CHOICES],
        'facings':        [{'value': k, 'label': v} for k, v in FACING_CHOICES],
    }
