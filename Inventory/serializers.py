from rest_framework import serializers
from .models import Plot, Flat


class PlotSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model = Plot
        fields = [
            'id', 'plot_number', 'project', 'project_name',
            'area', 'price', 'status', 'facing', 'notes',
            'created_on', 'modified_on',
        ]
        read_only_fields = ['id', 'created_on', 'modified_on']


class FlatSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model = Flat
        fields = [
            'id', 'project', 'project_name',
            'tower', 'floor', 'unit_number',
            'area', 'facing', 'price', 'status', 'notes',
            'created_on', 'modified_on',
        ]
        read_only_fields = ['id', 'created_on', 'modified_on']