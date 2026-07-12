"""
Saved Filters Serializers
"""

from rest_framework import serializers
from .filter_models import SavedFilter, FilterPreset


class SavedFilterSerializer(serializers.ModelSerializer):
    """Serializer for SavedFilter model"""
    
    class Meta:
        model = SavedFilter
        fields = [
            'id', 'code', 'name', 'description', 'filter_config',
            'screen_name', 'is_public', 'is_default',
            'usage_count', 'last_used',
            'created_on', 'modified_on'
        ]
        read_only_fields = ['id', 'code', 'usage_count', 'last_used', 'created_on', 'modified_on']
    
    def validate_filter_config(self, value):
        """Validate filter configuration is valid JSON"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("filter_config must be a valid JSON object")
        return value


class FilterPresetSerializer(serializers.ModelSerializer):
    """Serializer for FilterPreset model"""
    
    class Meta:
        model = FilterPreset
        fields = [
            'id', 'code', 'name', 'description', 'icon',
            'filter_config', 'screen_name', 'sort_order',
            'is_active', 'created_on'
        ]
        read_only_fields = ['id', 'code', 'created_on']
