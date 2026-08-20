from rest_framework import serializers

from ProjectManagement.models import Project, ProjectImage, ProjectStatusHistory


class ProjectImageSerializer(serializers.ModelSerializer):
    image_type_display = serializers.CharField(source='get_image_type_display', read_only=True)

    class Meta:
        model = ProjectImage
        fields = ('id', 'project', 'image', 'image_type', 'image_type_display',
                  'title', 'description', 'order', 'created_on')
        read_only_fields = ('created_on',)


class ProjectSerializer(serializers.ModelSerializer):
    # Display fields (read-only) - kept for backward compatibility
    project_type_display = serializers.CharField(source='get_project_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approval_type_display = serializers.CharField(source='get_approval_type_display', read_only=True)

    # Legacy fields - optional, kept for backward compatibility
    project_type = serializers.CharField(allow_blank=True, required=False, default='PLOT')
    approval_type = serializers.CharField(allow_blank=True, required=False, default='PENDING')
    status = serializers.CharField(allow_blank=True, required=False, default='UPCOMING')
    sub = serializers.ImageField(allow_null=True, required=False)
    elevation_image = serializers.ImageField(allow_null=True, required=False)
    thumbnail = serializers.ImageField(allow_null=True, required=False)
    floor_plans = serializers.JSONField(required=False, default=list)
    gallery = serializers.JSONField(required=False, default=list)

    # Required/Used fields for current form
    name = serializers.CharField(required=True)
    developer_name = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    location = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    overview = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    description = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    amenities = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    specifications = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    floor_plans_text = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    brochure = serializers.FileField(allow_null=True, required=False)

    # Related images (elevation images uploaded separately via ProjectImage)
    images = serializers.SerializerMethodField()

    # Preview image - first elevation image for list/card views
    preview_image = serializers.SerializerMethodField()

    def get_images(self, obj):
        images = obj.images.all()
        return ProjectImageSerializer(images, many=True, context=self.context).data

    def get_preview_image(self, obj):
        """Return the URL of the first elevation image for preview"""
        first_elevation = obj.images.filter(image_type='ELEVATION').first()
        if first_elevation and first_elevation.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(first_elevation.image.url)
            return first_elevation.image.url
        return None

    class Meta:
        model = Project
        fields = (
            'id', 'code', 'name', 'developer_name', 'location',
            # Legacy fields (kept for backward compatibility)
            'project_type', 'project_type_display',
            'approval_type', 'approval_type_display',
            'status', 'status_display',
            'is_active', 'is_deleted',
            'sub', 'elevation_image', 'thumbnail',
            'floor_plans', 'gallery',
            # Current form fields
            'overview', 'description', 'amenities', 'specifications', 'floor_plans_text',
            'brochure', 'images', 'preview_image',
            'created_on', 'modified_on',
        )
        read_only_fields = ('code', 'is_deleted', 'created_on', 'modified_on', 'images', 'preview_image')

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


class ProjectMiniSerializer(serializers.ModelSerializer):
    """Minimal serializer for Project dropdowns (used by Site Visit, Booking, etc.)."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    project_type_display = serializers.CharField(source='get_project_type_display', read_only=True)

    class Meta:
        model = Project
        fields = ('id', 'code', 'name', 'status', 'status_display',
                  'project_type', 'project_type_display', 'is_active')
