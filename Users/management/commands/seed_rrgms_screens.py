from django.core.management.base import BaseCommand
from Users.models import Screen


class Command(BaseCommand):
    help = 'Seed RRGMS screens'

    def handle(self, *args, **options):
        screens = [
            {'code': 'LEAD', 'name': 'Lead Management', 'order': 1},
            {'code': 'CROSS_LEAD', 'name': 'Cross Lead Check', 'order': 2},
            {'code': 'FOLLOWUP', 'name': 'Follow-Up Management', 'order': 3},
            {'code': 'SITE_VISIT', 'name': 'Site Visit Management', 'order': 4},
            {'code': 'PROJECT', 'name': 'Project Management', 'order': 5},
            {'code': 'INVENTORY', 'name': 'Inventory Management', 'order': 6},
            {'code': 'BOOKING', 'name': 'Booking Management', 'order': 7},
            {'code': 'DOCUMENT', 'name': 'Document Management', 'order': 8},
            {'code': 'EMPLOYEE', 'name': 'Employee Management', 'order': 9},
            {'code': 'REPORTS', 'name': 'Reports', 'order': 10},
            {'code': 'DASHBOARD', 'name': 'Dashboards', 'order': 11},
            {'code': 'USER_PERMISSION', 'name': 'User & Permission Management', 'order': 12},
        ]
        
        for s in screens:
            Screen.objects.update_or_create(code=s['code'], defaults=s)
        
        self.stdout.write(self.style.SUCCESS(f'Seeded {len(screens)} screens'))
