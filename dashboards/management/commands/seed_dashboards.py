"""
Management command to seed default dashboards for Royal Reality Groups CRM.

Usage:
    python manage.py seed_dashboards
    python manage.py seed_dashboards --clear  # Remove ALL dashboards first
"""
from django.core.management.base import BaseCommand
from dashboards.models import Dashboard, DashboardWidget, WidgetType


class Command(BaseCommand):
    help = 'Seeds default dashboards for Royal Reality Groups CRM'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete ALL existing dashboards before seeding',
        )

    def handle(self, *args, **options):
        self.stdout.write('Seeding Real Estate CRM dashboards...')

        # Cache widget types by code
        widget_types = {}
        for wt in WidgetType.objects.filter(is_deleted=False):
            widget_types[wt.code] = wt

        if not widget_types:
            self.stdout.write(self.style.ERROR(
                'No widget types found. Run: python manage.py seed_widget_types'
            ))
            return

        if options.get('clear'):
            deleted_count = Dashboard.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f'Deleted {deleted_count} existing dashboards'))

        overview = self._create_overview_dashboard(widget_types)
        self.stdout.write(self.style.SUCCESS(f'Created: {overview.name}'))

        sales = self._create_sales_dashboard(widget_types)
        self.stdout.write(self.style.SUCCESS(f'Created: {sales.name}'))

        self.stdout.write(self.style.SUCCESS(
            '\nDone! Created 2 dashboards. Assign them to groups via admin or API.'
        ))

    def _create_overview_dashboard(self, wt):
        """Overview Dashboard — high-level real estate KPIs"""
        dashboard = Dashboard.objects.create(
            name='Overview Dashboard',
            description='High-level overview of leads, site visits, bookings, and projects',
            icon='LayoutDashboard',
            visibility='organization',
            is_default=True,
            is_system=True,
            display_order=1,
            theme='default',
            refresh_interval=300,
            layout_config={'columns': 12, 'rowHeight': 100, 'gap': 16},
        )

        widgets = [
            # Row 0: Welcome
            {
                'widget_type': 'welcome_card',
                'title': 'Real Estate CRM',
                'x': 0, 'y': 0, 'w': 12, 'h': 1,
                'config': {'showGreeting': True, 'showDate': True},
            },
            # Row 1: KPI cards
            {
                'widget_type': 'stats_card',
                'title': 'Total Leads',
                'x': 0, 'y': 1, 'w': 3, 'h': 1,
                'data_source': 'realestate.leads_count',
                'config': {'color': 'blue', 'icon': 'Users'},
            },
            {
                'widget_type': 'stats_card',
                'title': 'Site Visits',
                'x': 3, 'y': 1, 'w': 3, 'h': 1,
                'data_source': 'realestate.sitevisits_count',
                'config': {'color': 'green', 'icon': 'MapPin'},
            },
            {
                'widget_type': 'stats_card',
                'title': 'Bookings',
                'x': 6, 'y': 1, 'w': 3, 'h': 1,
                'data_source': 'realestate.bookings_count',
                'config': {'color': 'purple', 'icon': 'FileText'},
            },
            {
                'widget_type': 'stats_card',
                'title': 'Active Projects',
                'x': 9, 'y': 1, 'w': 3, 'h': 1,
                'data_source': 'realestate.projects_count',
                'config': {'color': 'orange', 'icon': 'Building'},
            },
            # Row 2-3: Charts
            {
                'widget_type': 'bar_chart',
                'title': 'Leads by Status',
                'subtitle': 'Lead pipeline status',
                'x': 0, 'y': 2, 'w': 6, 'h': 2,
                'data_source': 'realestate.leads_by_status',
                'config': {'orientation': 'vertical', 'showLegend': True},
            },
            {
                'widget_type': 'donut_chart',
                'title': 'Bookings by Project',
                'subtitle': 'Bookings distribution',
                'x': 6, 'y': 2, 'w': 6, 'h': 2,
                'data_source': 'realestate.bookings_by_project',
                'config': {'showLegend': True, 'showCenterLabel': True},
            },
        ]

        self._create_widgets(dashboard, wt, widgets)
        return dashboard

    def _create_sales_dashboard(self, wt):
        """Sales Dashboard — lead and booking conversion tracking"""
        dashboard = Dashboard.objects.create(
            name='Sales Dashboard',
            description='Lead follow-ups, site visits, and booking conversions',
            icon='TrendingUp',
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
                        {'label': 'New Lead', 'action': 'create_lead', 'icon': 'Plus'},
                        {'label': 'New Site Visit', 'action': 'create_sitevisit', 'icon': 'MapPin'},
                    ],
                    'columns': 2,
                },
            },
            # Row 1: KPI cards
            {
                'widget_type': 'stats_card',
                'title': 'Leads This Month',
                'x': 0, 'y': 1, 'w': 3, 'h': 1,
                'data_source': 'realestate.leads_count',
                'config': {'color': 'blue', 'icon': 'Users'},
            },
            {
                'widget_type': 'stats_card',
                'title': 'Site Visits This Month',
                'x': 3, 'y': 1, 'w': 3, 'h': 1,
                'data_source': 'realestate.sitevisits_count',
                'config': {'color': 'green', 'icon': 'MapPin'},
            },
            {
                'widget_type': 'stats_card',
                'title': 'Bookings This Month',
                'x': 6, 'y': 1, 'w': 3, 'h': 1,
                'data_source': 'realestate.bookings_count',
                'config': {'color': 'purple', 'icon': 'FileText'},
            },
            {
                'widget_type': 'stats_card',
                'title': 'Available Inventory',
                'x': 9, 'y': 1, 'w': 3, 'h': 1,
                'data_source': 'realestate.inventory_count',
                'config': {'color': 'orange', 'icon': 'Home'},
            },
            # Row 2-3: Charts
            {
                'widget_type': 'line_chart',
                'title': 'Lead Trend',
                'subtitle': 'Leads over time',
                'x': 0, 'y': 2, 'w': 6, 'h': 2,
                'data_source': 'realestate.leads_over_time',
                'config': {'showDots': True, 'showArea': True, 'showLegend': True},
            },
            {
                'widget_type': 'pie_chart',
                'title': 'Site Visit Status',
                'subtitle': 'Site visit outcomes',
                'x': 6, 'y': 2, 'w': 6, 'h': 2,
                'data_source': 'realestate.sitevisits_by_status',
                'config': {'showLegend': True},
            },
        ]

        self._create_widgets(dashboard, wt, widgets)
        return dashboard

    def _create_widgets(self, dashboard, wt, widgets):
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
