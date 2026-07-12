"""
Management command to seed default widget types for TDH Sales Application.

Usage:
    python manage.py seed_widget_types
"""
from django.core.management.base import BaseCommand
from dashboards.models import WidgetType


class Command(BaseCommand):
    help = 'Seeds the database with default widget types for the dashboard builder'

    def handle(self, *args, **options):
        widget_types = [
            # ============== Stats Widgets ==============
            {
                'name': 'Stats Card',
                'code': 'stats_card',
                'description': 'Display a single KPI with optional trend indicator',
                'category': 'stats',
                'icon': 'BarChart3',
                'component_name': 'StatsCardWidget',
                'default_config': {
                    'color': 'primary',
                    'showTrend': True,
                    'trendPeriod': '7d',
                },
                'available_data_sources': [
                    'sales.count',
                    'dispatch.count',
                    'invoice.count',
                    'receipts.count',
                    'delivery.count',
                    'masters.distributors_count',
                    'masters.retailers_count',
                    'masters.superstockists_count',
                    'custom',
                ],
                'min_width': 2, 'min_height': 1,
                'max_width': 4, 'max_height': 2,
                'default_width': 3, 'default_height': 1,
                'is_system': True,
                'display_order': 1,
            },

            # ============== Chart Widgets ==============
            {
                'name': 'Bar Chart',
                'code': 'bar_chart',
                'description': 'Vertical or horizontal bar chart',
                'category': 'chart',
                'icon': 'BarChart',
                'component_name': 'BarChartWidget',
                'default_config': {
                    'orientation': 'vertical',
                    'showLegend': True,
                    'showGrid': True,
                    'stacked': False,
                },
                'available_data_sources': [
                    'sales.by_status',
                    'dispatch.by_status',
                    'invoice.by_status',
                    'receipts.by_payment_mode',
                    'delivery.by_status',
                    'custom',
                ],
                'min_width': 4, 'min_height': 2,
                'max_width': 12, 'max_height': 4,
                'default_width': 6, 'default_height': 2,
                'is_system': True,
                'display_order': 10,
            },
            {
                'name': 'Line Chart',
                'code': 'line_chart',
                'description': 'Line chart for trends over time',
                'category': 'chart',
                'icon': 'TrendingUp',
                'component_name': 'LineChartWidget',
                'default_config': {
                    'showDots': True,
                    'showArea': False,
                    'showLegend': True,
                    'showGrid': True,
                    'smooth': True,
                },
                'available_data_sources': [
                    'sales.over_time',
                    'dispatch.over_time',
                    'invoice.over_time',
                    'custom',
                ],
                'min_width': 4, 'min_height': 2,
                'max_width': 12, 'max_height': 4,
                'default_width': 6, 'default_height': 2,
                'is_system': True,
                'display_order': 11,
            },
            {
                'name': 'Pie Chart',
                'code': 'pie_chart',
                'description': 'Pie chart for distribution visualization',
                'category': 'chart',
                'icon': 'PieChart',
                'component_name': 'PieChartWidget',
                'default_config': {
                    'showLegend': True,
                    'showLabels': True,
                    'innerRadius': 0,
                },
                'available_data_sources': [
                    'sales.by_status',
                    'dispatch.by_status',
                    'invoice.by_status',
                    'custom',
                ],
                'min_width': 3, 'min_height': 2,
                'max_width': 6, 'max_height': 4,
                'default_width': 4, 'default_height': 2,
                'is_system': True,
                'display_order': 13,
            },
            {
                'name': 'Donut Chart',
                'code': 'donut_chart',
                'description': 'Donut chart with center label',
                'category': 'chart',
                'icon': 'Circle',
                'component_name': 'DonutChartWidget',
                'default_config': {
                    'showLegend': True,
                    'showCenterLabel': True,
                    'innerRadius': 60,
                },
                'available_data_sources': [
                    'sales.by_status',
                    'dispatch.by_status',
                    'custom',
                ],
                'min_width': 3, 'min_height': 2,
                'max_width': 6, 'max_height': 4,
                'default_width': 4, 'default_height': 2,
                'is_system': True,
                'display_order': 14,
            },

            # ============== Table Widgets ==============
            {
                'name': 'Data Table',
                'code': 'data_table',
                'description': 'Tabular data display with sorting and pagination',
                'category': 'table',
                'icon': 'Table',
                'component_name': 'DataTableWidget',
                'default_config': {
                    'pageSize': 10,
                    'showPagination': True,
                    'sortable': True,
                    'compact': False,
                },
                'available_data_sources': [
                    'sales.list',
                    'sales.recent',
                    'dispatch.list',
                    'dispatch.recent',
                    'invoice.list',
                    'invoice.recent',
                    'custom',
                ],
                'min_width': 6, 'min_height': 2,
                'max_width': 12, 'max_height': 6,
                'default_width': 12, 'default_height': 3,
                'is_system': True,
                'display_order': 20,
            },

            # ============== List Widgets ==============
            {
                'name': 'Activity Feed',
                'code': 'activity_feed',
                'description': 'Recent activity stream',
                'category': 'list',
                'icon': 'Activity',
                'component_name': 'ActivityFeedWidget',
                'default_config': {
                    'limit': 10,
                    'showTimestamp': True,
                    'showUser': True,
                    'compact': False,
                },
                'available_data_sources': [
                    'activity.recent',
                ],
                'min_width': 4, 'min_height': 2,
                'max_width': 6, 'max_height': 6,
                'default_width': 4, 'default_height': 3,
                'is_system': True,
                'display_order': 30,
            },
            {
                'name': 'Sales Order List',
                'code': 'sales_list',
                'description': 'List of sales orders with status indicators',
                'category': 'list',
                'icon': 'ShoppingCart',
                'component_name': 'SalesListWidget',
                'default_config': {
                    'limit': 10,
                    'showStatus': True,
                    'showCustomer': True,
                    'showAmount': True,
                },
                'available_data_sources': [
                    'sales.recent',
                ],
                'min_width': 4, 'min_height': 2,
                'max_width': 8, 'max_height': 6,
                'default_width': 6, 'default_height': 3,
                'is_system': True,
                'display_order': 31,
            },
            {
                'name': 'Dispatch List',
                'code': 'dispatch_list',
                'description': 'List of dispatch plans with status',
                'category': 'list',
                'icon': 'Truck',
                'component_name': 'DispatchListWidget',
                'default_config': {
                    'limit': 5,
                    'showStatus': True,
                    'showDate': True,
                },
                'available_data_sources': [
                    'dispatch.recent',
                ],
                'min_width': 4, 'min_height': 2,
                'max_width': 8, 'max_height': 6,
                'default_width': 6, 'default_height': 3,
                'is_system': True,
                'display_order': 32,
            },
            {
                'name': 'Alerts List',
                'code': 'alerts_list',
                'description': 'Display alerts and notifications',
                'category': 'list',
                'icon': 'Bell',
                'component_name': 'AlertsListWidget',
                'default_config': {
                    'limit': 5,
                    'showDismiss': True,
                    'types': ['warning', 'error', 'info'],
                },
                'available_data_sources': [
                    'alerts.overview',
                ],
                'min_width': 3, 'min_height': 2,
                'max_width': 6, 'max_height': 4,
                'default_width': 4, 'default_height': 2,
                'is_system': True,
                'display_order': 33,
            },

            # ============== Custom Widgets ==============
            {
                'name': 'Quick Actions',
                'code': 'quick_actions',
                'description': 'Grid of quick action buttons',
                'category': 'custom',
                'icon': 'Zap',
                'component_name': 'QuickActionsWidget',
                'default_config': {
                    'actions': [
                        {'label': 'New Sales Order', 'action': 'create_sales_order', 'icon': 'Plus'},
                        {'label': 'New Dispatch', 'action': 'create_dispatch', 'icon': 'Truck'},
                    ],
                    'columns': 2,
                },
                'available_data_sources': [],
                'min_width': 2, 'min_height': 1,
                'max_width': 6, 'max_height': 3,
                'default_width': 4, 'default_height': 1,
                'is_system': True,
                'display_order': 40,
            },
            {
                'name': 'Welcome Card',
                'code': 'welcome_card',
                'description': 'Personalized welcome message',
                'category': 'custom',
                'icon': 'User',
                'component_name': 'WelcomeCardWidget',
                'default_config': {
                    'showGreeting': True,
                    'showDate': True,
                    'showQuote': False,
                },
                'available_data_sources': [],
                'min_width': 4, 'min_height': 1,
                'max_width': 12, 'max_height': 2,
                'default_width': 6, 'default_height': 1,
                'is_system': True,
                'display_order': 41,
            },
        ]

        created_count = 0
        updated_count = 0

        for widget_data in widget_types:
            widget, created = WidgetType.objects.update_or_create(
                code=widget_data['code'],
                defaults=widget_data
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created widget type: {widget.name}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'Updated widget type: {widget.name}'))

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Created: {created_count}, Updated: {updated_count}'
        ))
