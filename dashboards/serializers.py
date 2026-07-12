"""
Serializers for Dashboards app.
"""
from rest_framework import serializers
from .models import WidgetType, Dashboard, DashboardWidget, DashboardGroup


# ============== Widget Type Serializers ==============

class WidgetTypeListSerializer(serializers.ModelSerializer):
    """Serializer for widget type list."""

    class Meta:
        model = WidgetType
        fields = [
            'id', 'name', 'code', 'description', 'category', 'icon',
            'component_name', 'default_config', 'available_data_sources',
            'min_width', 'min_height', 'max_width', 'max_height',
            'default_width', 'default_height', 'is_system', 'display_order'
        ]


class WidgetTypeDetailSerializer(serializers.ModelSerializer):
    """Serializer for widget type detail."""

    class Meta:
        model = WidgetType
        fields = [
            'id', 'name', 'code', 'description', 'category', 'icon',
            'component_name', 'default_config', 'available_data_sources',
            'min_width', 'min_height', 'max_width', 'max_height',
            'default_width', 'default_height', 'is_system', 'display_order',
            'created_on', 'modified_on'
        ]


class WidgetTypeCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating widget types."""

    class Meta:
        model = WidgetType
        fields = [
            'name', 'code', 'description', 'category', 'icon',
            'component_name', 'default_config', 'available_data_sources',
            'min_width', 'min_height', 'max_width', 'max_height',
            'default_width', 'default_height', 'display_order'
        ]


# ============== Dashboard Widget Serializers ==============

class DashboardWidgetSerializer(serializers.ModelSerializer):
    """Serializer for dashboard widgets."""
    widget_type_code = serializers.CharField(source='widget_type.code', read_only=True)
    widget_type_name = serializers.CharField(source='widget_type.name', read_only=True)
    component_name = serializers.CharField(source='widget_type.component_name', read_only=True)
    layout = serializers.SerializerMethodField()

    class Meta:
        model = DashboardWidget
        fields = [
            'id', 'dashboard', 'widget_type', 'widget_type_code', 'widget_type_name',
            'component_name', 'title', 'subtitle',
            'position_x', 'position_y', 'width', 'height',
            'config', 'data_source', 'filters', 'style',
            'cache_duration', 'is_visible', 'layout',
            'created_on', 'modified_on'
        ]
        read_only_fields = ['id', 'created_on', 'modified_on']

    def get_layout(self, obj):
        return obj.get_layout()


class DashboardWidgetCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating dashboard widgets."""

    class Meta:
        model = DashboardWidget
        fields = [
            'dashboard', 'widget_type', 'title', 'subtitle',
            'position_x', 'position_y', 'width', 'height',
            'config', 'data_source', 'filters', 'style',
            'cache_duration', 'is_visible'
        ]


class DashboardWidgetUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating dashboard widgets."""

    class Meta:
        model = DashboardWidget
        fields = [
            'title', 'subtitle', 'position_x', 'position_y', 'width', 'height',
            'config', 'data_source', 'filters', 'style',
            'cache_duration', 'is_visible'
        ]


class DashboardWidgetLayoutSerializer(serializers.Serializer):
    """Serializer for bulk updating widget layouts."""
    id = serializers.UUIDField()
    x = serializers.IntegerField(required=False)
    y = serializers.IntegerField(required=False)
    w = serializers.IntegerField(required=False)
    h = serializers.IntegerField(required=False)


# ============== Dashboard Group Serializers ==============

class DashboardGroupSerializer(serializers.ModelSerializer):
    """Serializer for dashboard group assignments."""
    group_name = serializers.CharField(source='group.name', read_only=True)
    dashboard_name = serializers.CharField(source='dashboard.name', read_only=True)

    class Meta:
        model = DashboardGroup
        fields = [
            'id', 'dashboard', 'dashboard_name', 'group', 'group_name',
            'display_order', 'is_default', 'can_customize',
            'created_on', 'modified_on'
        ]
        read_only_fields = ['id', 'created_on', 'modified_on']


class DashboardGroupCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating dashboard group assignments."""

    class Meta:
        model = DashboardGroup
        fields = ['dashboard', 'group', 'display_order', 'is_default', 'can_customize']


# ============== Dashboard Serializers ==============

class DashboardListSerializer(serializers.ModelSerializer):
    """Serializer for dashboard list."""
    widget_count = serializers.SerializerMethodField()

    class Meta:
        model = Dashboard
        fields = [
            'id', 'name', 'description', 'icon', 'visibility',
            'is_default', 'is_system', 'display_order', 'widget_count',
            'created_by_identifier', 'created_on', 'modified_on'
        ]

    def get_widget_count(self, obj):
        """Return count of active widgets."""
        return obj.widgets.filter(is_deleted=False).count()


class DashboardDetailSerializer(serializers.ModelSerializer):
    """Serializer for dashboard detail with widgets."""
    widgets = serializers.SerializerMethodField()
    group_assignments = serializers.SerializerMethodField()
    widget_count = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Dashboard
        fields = [
            'id', 'name', 'description','icon', 'visibility',
            'layout_config', 'is_default', 'is_system', 'display_order',
            'theme', 'refresh_interval', 'widgets', 'group_assignments',
            'widget_count', 'created_by_identifier', 'created_by_name',
            'created_on', 'modified_on'
        ]

    def get_widgets(self, obj):
        """Return only active widgets with widget_type data."""
        active_widgets = obj.widgets.filter(is_deleted=False).select_related('widget_type')
        return DashboardWidgetSerializer(active_widgets, many=True).data

    def get_group_assignments(self, obj):
        """Return only active group assignments."""
        active_assignments = obj.group_assignments.filter(is_deleted=False).select_related('group')
        return DashboardGroupSerializer(active_assignments, many=True).data

    def get_widget_count(self, obj):
        """Return count of active widgets."""
        return obj.widgets.filter(is_deleted=False).count()

    def get_created_by_name(self, obj):
        # In TDH project, we use created_by_identifier
        return None


class DashboardCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating dashboards."""

    class Meta:
        model = Dashboard
        fields = [
            'name', 'description', 'icon', 'visibility',
            'layout_config', 'is_default', 'display_order',
            'theme', 'refresh_interval'
        ]


class DashboardUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating dashboards."""

    class Meta:
        model = Dashboard
        fields = [
            'name', 'description', 'icon', 'visibility',
            'layout_config', 'is_default', 'display_order',
            'theme', 'refresh_interval'
        ]


# ============== User Dashboard Access Serializer ==============

class UserDashboardSerializer(serializers.ModelSerializer):
    """
    Serializer for dashboards accessible to a user.
    Used for the dashboard tabs in the menu.
    """
    is_customizable = serializers.SerializerMethodField()
    is_default_for_user = serializers.SerializerMethodField()

    class Meta:
        model = Dashboard
        fields = [
            'id', 'name', 'icon', 'display_order',
            'is_default', 'is_customizable', 'is_default_for_user'
        ]

    def get_is_customizable(self, obj):
        """Check if user can customize this dashboard."""
        return getattr(obj, '_can_customize', False)

    def get_is_default_for_user(self, obj):
        """Check if this is the default dashboard for user's group."""
        return getattr(obj, '_is_default', False)
