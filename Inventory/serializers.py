from rest_framework import serializers
from .models import PlotInventory, FlatInventory, INVENTORY_STATUS_CHOICES, FACING_CHOICES


class PlotInventorySerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    facing_display = serializers.CharField(source='get_facing_display', read_only=True)

    class Meta:
        model = PlotInventory
        fields = [
            'id', 'code', 'project', 'project_name',
            'plot_number', 'area_sqyd', 'area_sqft',
            'facing', 'facing_display', 'road_width',
            'price_per_sqyd', 'total_price',
            'status', 'status_display', 'remarks',
            'created_on', 'modified_on',
        ]
        read_only_fields = ('code', 'created_on', 'modified_on')

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


class FlatInventorySerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    facing_display = serializers.CharField(source='get_facing_display', read_only=True)

    class Meta:
        model = FlatInventory
        fields = [
            'id', 'code', 'project', 'project_name',
            'tower', 'floor', 'unit_number', 'flat_type',
            'area_sqft', 'carpet_area_sqft',
            'facing', 'facing_display', 'price',
            'status', 'status_display', 'remarks',
            'created_on', 'modified_on',
        ]
        read_only_fields = ('code', 'created_on', 'modified_on')

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


INVENTORY_STATUS_LIST = [{'value': k, 'label': v} for k, v in INVENTORY_STATUS_CHOICES]
FACING_LIST = [{'value': k, 'label': v} for k, v in FACING_CHOICES]
