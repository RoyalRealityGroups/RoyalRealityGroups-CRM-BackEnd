"""
Management command to seed default dashboards for TDH Sales Application.

Usage:
    python manage.py seed_dashboards
    python manage.py seed_dashboards --clear  # Remove ALL dashboards first
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from dashboards.models import Dashboard, DashboardWidget, DashboardGroup, WidgetType


class Command(BaseCommand):
    help = 'Seeds default dashboards for TDH Sales Application'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete ALL existing dashboards before seeding',
        )

    def handle(self, *args, **options):
        self.stdout.write('Seeding TDH Sales dashboards...')

        # Cache widget types by code
        widget_types = {}
        for wt in WidgetType.objects.filter(is_deleted=False):
            widget_types[wt.code] = wt

        if not widget_types:
            self.stdout.write(self.style.ERROR(
                'No widget types found. Run: python manage.py seed_widget_types'
            ))
            return

        # Delete existing dashboards if requested
        if options.get('clear'):
            deleted_count = Dashboard.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f'Deleted {deleted_count} existing dashboards'))

        # Create Sales Dashboard
        sales_dashboard = self._create_sales_dashboard(widget_types)
        self.stdout.write(self.style.SUCCESS(f'Created: {sales_dashboard.name}'))

        # Create Dispatch Dashboard
        dispatch_dashboard = self._create_dispatch_dashboard(widget_types)
        self.stdout.write(self.style.SUCCESS(f'Created: {dispatch_dashboard.name}'))

        # Create Overview Dashboard
        overview_dashboard = self._create_overview_dashboard(widget_types)
        self.stdout.write(self.style.SUCCESS(f'Created: {overview_dashboard.name}'))

        self.stdout.write(self.style.SUCCESS(
            '\nDone! Created 3 dashboards. Assign them to groups via admin or API.'
        ))

    def _create_sales_dashboard(self, wt):
        """Sales Dashboard - Sales orders, invoices, receipts"""
        dashboard = Dashboard.objects.create(
            name='Sales Dashboard',
            description='Sales orders, invoices, and receipts overview',
            icon='TrendingUp',
            visibility='role',
            is_default=True,
            is_system=True,
            display_order=1,
            theme='default',
            refresh_interval=300,
            layout_config={'columns': 12, 'rowHeight': 100, 'gap': 16},
        )

        widgets = [
            # Row 0: Welcome + Quick Actions
            {
                'widget_type': 'welcome_card',
                'title': 'Sales Dashboard',
                'x': 0, 'y': 0, 'w': 8, 'h': 1,
                'config': {'showGreeting': True, 'showDate': True},
            },
            {
                'widget_type': 'quick_actions',
                'title': 'Quick Actions',
                'x': 8, 'y': 0, 'w': 4, 'h': 1,
                'config': {
                    'actions': [
                        {'label': 'New Sales Order', 'action': 'create_sales_order', 'icon': 'Plus'},
                        {'label': 'New Invoice', 'action': 'create_invoice', 'icon': 'FileText'},
                    ],
                    'columns': 2,
                },
            },
            # Row 1: Stats cards
            {
                'widget_type': 'stats_card',
                'title': 'Total Sales Orders',
                'x': 0, 'y': 1, 'w': 3, 'h': 1,
                'data_source': 'sales.count',
                'config': {'color': 'blue', 'icon': 'ShoppingCart'},
            },
            {
                'widget_type': 'stats_card',
                'title': 'Total Invoices',
                'x': 3, 'y': 1, 'w': 3, 'h': 1,
                'data_source': 'invoice.count',
                'config': {'color': 'green', 'icon': 'FileText'},
            },
            {
                'widget_type': 'stats_card',
                'title': 'Total Receipts',
                'x': 6, 'y': 1, 'w': 3, 'h': 1,
                'data_source': 'receipts.count',
                'config': {'color': 'purple', 'icon': 'DollarSign'},
            },
            {
                'widget_type': 'stats_card',
                'title': 'Total Distributors',
                'x': 9, 'y': 1, 'w': 3, 'h': 1,
                'data_source': 'masters.distributors_count',
                'config': {'color': 'orange', 'icon': 'Users'},
            },
            # Row 2-3: Charts
            {
                'widget_type': 'bar_chart',
                'title': 'Sales by Status',
                'subtitle': 'Order status distribution',
                'x': 0, 'y': 2, 'w': 6, 'h': 2,
                'data_source': 'sales.by_status',
                'config': {'orientation': 'vertical', 'showLegend': True},
            },
            {
                'widget_type': 'donut_chart',
                'title': 'Invoice Status',
                'subtitle': 'Invoice distribution',
                'x': 6, 'y': 2, 'w': 6, 'h': 2,
                'data_source': 'invoice.by_status',
                'config': {'showLegend': True, 'showCenterLabel': True},
            },
            # Row 4-5: Recent lists
            {
                'widget_type': 'sales_list',
                'title': 'Recent Sales Orders',
                'subtitle': 'Latest orders',
                'x': 0, 'y': 4, 'w': 12, 'h': 2,
                'data_source': 'sales.recent',
                'config': {'limit': 10, 'showStatus': True},
            },
        ]

        for widget_def in widgets:
            wt_code = widget_def['widget_type']
            if wt_code not in wt:
                continue

            DashboardWidget.objects.create(
                dashboard=dashboard,
                widget_type=wt[wt_code],
                title=widget_def['title'],
                subtitle=widget_def.get('subtitle', ''),
                position_x=widget_def['x'],
                position_y=widget_def['y'],
                width=widget_def['w'],
                height=widget_def['h'],
                data_source=widget_def.get('data_source', ''),
                config=widget_def.get('config', {}),
                cache_duration=300,
                is_visible=True,
            )

        return dashboard

    def _create_dispatch_dashboard(self, wt):
        """Dispatch Dashboard - Dispatch plans and delivery"""
        dashboard = Dashboard.objects.create(
            name='Dispatch Dashboard',
            description='Dispatch plans and delivery tracking',
            icon='Truck',
            visibility='role',
            is_default=False,
            is_system=True,
            display_order=2,
            theme='default',
            refresh_interval=300,
            layout_config={'columns': 12, 'rowHeight': 100, 'gap': 16},
        )

        widgets = [
            # Row 0: Welcome + Quick Actions
            {
                'widget_type': 'welcome_card',
                'title': 'Dispatch Dashboard',
                'x': 0, 'y': 0, 'w': 8, 'h': 1,
                'config': {'showGreeting': True, 'showDate': True},
            },
            {
                'widget_type': 'quick_actions',
                'title': 'Quick Actions',
                'x': 8, 'y': 0, 'w': 4, 'h': 1,
                'config': {
                    'actions': [
                        {'label': 'New Dispatch', 'action': 'create_dispatch', 'icon': 'Truck'},
                        {'label': 'New POD', 'action': 'create_pod', 'icon': 'FileCheck'},
                    ],
                    'columns': 2,
                },
            },
            # Row 1: Stats cards
            {
                'widget_type': 'stats_card',
                'title': 'Total Dispatch Plans',
                'x': 0, 'y': 1, 'w': 4, 'h': 1,
                'data_source': 'dispatch.count',
                'config': {'color': 'blue', 'icon': 'Truck'},
            },
            {
                'widget_type': 'stats_card',
                'title': 'Total PODs',
                'x': 4, 'y': 1, 'w': 4, 'h': 1,
                'data_source': 'delivery.count',
                'config': {'color': 'green', 'icon': 'FileCheck'},
            },
            {
                'widget_type': 'stats_card',
                'title': 'Total Retailers',
                'x': 8, 'y': 1, 'w': 4, 'h': 1,
                'data_source': 'masters.retailers_count',
                'config': {'color': 'purple', 'icon': 'Store'},
            },
            # Row 2-3: Charts
            {
                'widget_type': 'bar_chart',
                'title': 'Dispatch by Status',
                'subtitle': 'Dispatch plan status',
                'x': 0, 'y': 2, 'w': 6, 'h': 2,
                'data_source': 'dispatch.by_status',
                'config': {'orientation': 'vertical', 'showLegend': True},
            },
            {
                'widget_type': 'pie_chart',
                'title': 'Delivery Status',
                'subtitle': 'POD status distribution',
                'x': 6, 'y': 2, 'w': 6, 'h': 2,
                'data_source': 'delivery.by_status',
                'config': {'showLegend': True},
            },
            # Row 4-5: Recent lists
            {
                'widget_type': 'dispatch_list',
                'title': 'Recent Dispatch Plans',
                'subtitle': 'Latest dispatches',
                'x': 0, 'y': 4, 'w': 12, 'h': 2,
                'data_source': 'dispatch.recent',
                'config': {'limit': 10, 'showStatus': True},
            },
        ]

        for widget_def in widgets:
            wt_code = widget_def['widget_type']
            if wt_code not in wt:
                continue

            DashboardWidget.objects.create(
                dashboard=dashboard,
                widget_type=wt[wt_code],
                title=widget_def['title'],
                subtitle=widget_def.get('subtitle', ''),
                position_x=widget_def['x'],
                position_y=widget_def['y'],
                width=widget_def['w'],
                height=widget_def['h'],
                data_source=widget_def.get('data_source', ''),
                config=widget_def.get('config', {}),
                cache_duration=300,
                is_visible=True,
            )

        return dashboard

    def _create_overview_dashboard(self, wt):
        """Overview Dashboard - Complete overview"""
        dashboard = Dashboard.objects.create(
            name='Overview Dashboard',
            description='Complete overview of sales, dispatch, and delivery',
            icon='LayoutDashboard',
            visibility='organization',
            is_default=False,
            is_system=True,
            display_order=3,
            theme='default',
            refresh_interval=300,
            layout_config={'columns': 12, 'rowHeight': 100, 'gap': 16},
        )

        widgets = [
            # Row 0: Welcome
            {
                'widget_type': 'welcome_card',
                'title': 'Overview Dashboard',
                'x': 0, 'y': 0, 'w': 12, 'h': 1,
                'config': {'showGreeting': True, 'showDate': True},
            },
            # Row 1: Stats cards
            {
                'widget_type': 'stats_card',
                'title': 'Sales Orders',
                'x': 0, 'y': 1, 'w': 3, 'h': 1,
                'data_source': 'sales.count',
                'config': {'color': 'blue', 'icon': 'ShoppingCart'},
            },
            {
                'widget_type': 'stats_card',
                'title': 'Dispatch Plans',
                'x': 3, 'y': 1, 'w': 3, 'h': 1,
                'data_source': 'dispatch.count',
                'config': {'color': 'green', 'icon': 'Truck'},
            },
            {
                'widget_type': 'stats_card',
                'title': 'Invoices',
                'x': 6, 'y': 1, 'w': 3, 'h': 1,
                'data_source': 'invoice.count',
                'config': {'color': 'purple', 'icon': 'FileText'},
            },
            {
                'widget_type': 'stats_card',
                'title': 'PODs',
                'x': 9, 'y': 1, 'w': 3, 'h': 1,
                'data_source': 'delivery.count',
                'config': {'color': 'orange', 'icon': 'FileCheck'},
            },
            # Row 2-3: Charts
            {
                'widget_type': 'bar_chart',
                'title': 'Sales by Status',
                'x': 0, 'y': 2, 'w': 4, 'h': 2,
                'data_source': 'sales.by_status',
                'config': {'orientation': 'vertical', 'showLegend': True},
            },
            {
                'widget_type': 'donut_chart',
                'title': 'Dispatch Status',
                'x': 4, 'y': 2, 'w': 4, 'h': 2,
                'data_source': 'dispatch.by_status',
                'config': {'showLegend': True, 'showCenterLabel': True},
            },
            {
                'widget_type': 'pie_chart',
                'title': 'Invoice Status',
                'x': 8, 'y': 2, 'w': 4, 'h': 2,
                'data_source': 'invoice.by_status',
                'config': {'showLegend': True},
            },
        ]

        for widget_def in widgets:
            wt_code = widget_def['widget_type']
            if wt_code not in wt:
                continue

            DashboardWidget.objects.create(
                dashboard=dashboard,
                widget_type=wt[wt_code],
                title=widget_def['title'],
                subtitle=widget_def.get('subtitle', ''),
                position_x=widget_def['x'],
                position_y=widget_def['y'],
                width=widget_def['w'],
                height=widget_def['h'],
                data_source=widget_def.get('data_source', ''),
                config=widget_def.get('config', {}),
                cache_duration=300,
                is_visible=True,
            )

        return dashboard
