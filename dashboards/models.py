"""Dashboard models."""
from django.db import models
from django.contrib.auth.models import Group
from Core.Users.models import BaseModel,CoreModel


class WidgetType(CoreModel):
    """
    Defines the types of widgets available for dashboards.

    Widget types include:
    - Stats cards (KPIs, counters)
    - Charts (bar, line, area, pie, donut)
    - Tables (data grids)
    - Lists (activity feeds, task lists)
    - Custom (embedded content)
    """

    CODE_PREFIX = 'WT'

    CATEGORY_CHOICES = [
        ('stats', 'Statistics'),
        ('chart', 'Charts'),
        ('table', 'Tables'),
        ('list', 'Lists'),
        ('custom', 'Custom'),
    ]

    name = models.CharField(
        max_length=100,
        help_text="Display name of the widget type"
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique identifier code (e.g., 'stats_card', 'bar_chart')"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of what this widget type displays"
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='stats',
        help_text="Category of the widget"
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Icon name (Lucide icon) for this widget type"
    )
    component_name = models.CharField(
        max_length=100,
        help_text="React component name to render this widget"
    )
    default_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Default configuration for this widget type"
    )
    available_data_sources = models.JSONField(
        default=list,
        blank=True,
        help_text="List of available data sources for this widget type"
    )
    min_width = models.PositiveIntegerField(
        default=1,
        help_text="Minimum grid width (1-12)"
    )
    min_height = models.PositiveIntegerField(
        default=1,
        help_text="Minimum grid height"
    )
    max_width = models.PositiveIntegerField(
        default=12,
        help_text="Maximum grid width (1-12)"
    )
    max_height = models.PositiveIntegerField(
        default=4,
        help_text="Maximum grid height"
    )
    default_width = models.PositiveIntegerField(
        default=3,
        help_text="Default grid width"
    )
    default_height = models.PositiveIntegerField(
        default=1,
        help_text="Default grid height"
    )
    is_system = models.BooleanField(
        default=False,
        help_text="System widgets cannot be deleted"
    )
    display_order = models.PositiveIntegerField(
        default=0,
        help_text="Order in widget selection palette"
    )

    class Meta:
        db_table = 'dashboard_widget_types'
        ordering = ['category', 'display_order', 'name']
        verbose_name = 'Widget Type'
        verbose_name_plural = 'Widget Types'

    def __str__(self):
        return f"{self.name} ({self.code})"


class Dashboard(CoreModel):
    """
    Dashboard entity that contains widgets.

    Dashboards can be: 
    - Assigned to roles (shown as tabs)
    - Personal (user-specific)
    - Shared across organization
    """

    CODE_PREFIX = 'DASH'

    VISIBILITY_CHOICES = [
        ('private', 'Private'),
        ('role', 'Role-Based'),
        ('organization', 'Organization'),
    ]

    name = models.CharField(
        max_length=100,
        help_text="Dashboard name"
    )
    description = models.TextField(
        blank=True,
        help_text="Dashboard description"
    )
    icon = models.CharField(
        max_length=50,
        default='LayoutDashboard',
        help_text="Icon name (Lucide icon) for this dashboard"
    )
    visibility = models.CharField(
        max_length=20,
        choices=VISIBILITY_CHOICES,
        default='role',
        help_text="Who can see this dashboard"
    )
    layout_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Layout configuration (columns, row height, etc.)"
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Default dashboard for new users"
    )
    is_system = models.BooleanField(
        default=False,
        help_text="System dashboards cannot be deleted"
    )
    display_order = models.PositiveIntegerField(
        default=0,
        help_text="Order when displayed as tabs"
    )
    theme = models.CharField(
        max_length=50,
        default='default',
        help_text="Dashboard color theme"
    )
    refresh_interval = models.PositiveIntegerField(
        default=0,
        help_text="Auto-refresh interval in seconds (0 = disabled)"
    )

    class Meta:
        db_table = 'dashboards'
        ordering = ['display_order', 'name']
        verbose_name = 'Dashboard'
        verbose_name_plural = 'Dashboards'

    def __str__(self):
        return self.name

    @property
    def widget_count(self):
        """Return the number of widgets on this dashboard."""
        return self.widgets.filter(is_deleted=False).count()

    def get_widgets_layout(self):
        """Return widgets with their layout positions."""
        return self.widgets.filter(is_deleted=False).order_by('position_y', 'position_x')


class DashboardWidget(CoreModel):
    """
    A widget instance placed on a dashboard.

    Contains:
    - Position and size in the grid
    - Widget-specific configuration
    - Data source and filters
    """

    CODE_PREFIX = 'DW'

    dashboard = models.ForeignKey(
        'dashboards.Dashboard',
        on_delete=models.CASCADE,
        related_name='widgets',
        help_text="Dashboard this widget belongs to"
    )
    widget_type = models.ForeignKey(
        'dashboards.WidgetType',
        on_delete=models.PROTECT,
        related_name='instances',
        help_text="Type of widget"
    )
    title = models.CharField(
        max_length=100,
        help_text="Widget title displayed in header"
    )
    subtitle = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optional subtitle"
    )
    position_x = models.PositiveIntegerField(
        default=0,
        help_text="X position in grid (0-11)"
    )
    position_y = models.PositiveIntegerField(
        default=0,
        help_text="Y position in grid (row number)"
    )
    width = models.PositiveIntegerField(
        default=3,
        help_text="Width in grid columns (1-12)"
    )
    height = models.PositiveIntegerField(
        default=1,
        help_text="Height in grid rows"
    )
    config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Widget-specific configuration"
    )
    data_source = models.CharField(
        max_length=100,
        blank=True,
        help_text="Data source identifier (e.g., 'tasks.status_count')"
    )
    filters = models.JSONField(
        default=dict,
        blank=True,
        help_text="Data filters (e.g., {'project': 'uuid', 'status': 'active'})"
    )
    style = models.JSONField(
        default=dict,
        blank=True,
        help_text="Style overrides (colors, borders, etc.)"
    )
    cache_duration = models.PositiveIntegerField(
        default=300,
        help_text="Cache duration in seconds (0 = no cache)"
    )
    is_visible = models.BooleanField(
        default=True,
        help_text="Whether widget is visible"
    )

    class Meta:
        db_table = 'dashboard_widgets'
        ordering = ['position_y', 'position_x']
        verbose_name = 'Dashboard Widget'
        verbose_name_plural = 'Dashboard Widgets'

    def __str__(self):
        return f"{self.title} on {self.dashboard.name}"

    def get_layout(self):
        """Return layout object for react-grid-layout."""
        return {
            'i': str(self.id),
            'x': self.position_x,
            'y': self.position_y,
            'w': self.width,
            'h': self.height,
            'minW': self.widget_type.min_width,
            'minH': self.widget_type.min_height,
            'maxW': self.widget_type.max_width,
            'maxH': self.widget_type.max_height,
        }


class DashboardGroup(CoreModel):
    """
    Associates dashboards with user groups.

    When a group has multiple dashboards assigned, they appear as tabs
    in the dashboard menu. The display_order determines tab order.
    """

    CODE_PREFIX = 'DG'

    dashboard = models.ForeignKey(
        'dashboards.Dashboard',
        on_delete=models.CASCADE,
        related_name='group_assignments',
        help_text="Dashboard being assigned"
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='dashboard_assignments',
        help_text="Group this dashboard is assigned to"
    )
    display_order = models.PositiveIntegerField(
        default=0,
        help_text="Order when displayed as tabs (lower = first)"
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Is this the default dashboard for this group"
    )
    can_customize = models.BooleanField(
        default=False,
        help_text="Can users customize this dashboard"
    )

    class Meta:
        db_table = 'dashboard_group_assignments'
        ordering = ['group', 'display_order']
        verbose_name = 'Dashboard Group Assignment'
        verbose_name_plural = 'Dashboard Group Assignments'
        unique_together = [['dashboard', 'group']]

    def __str__(self):
        return f"{self.dashboard.name} -> {self.group.name}"

    def save(self, *args, **kwargs):
        """Ensure only one default dashboard per group."""
        if self.is_default:
            DashboardGroup.objects.filter(
                group=self.group,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


__all__ = [
    'WidgetType',
    'Dashboard',
    'DashboardWidget',
    'DashboardGroup',
]
