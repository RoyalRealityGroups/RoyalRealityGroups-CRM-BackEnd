"""
Seed realistic today's dashboard data for testing.

Creates:
  - 2 test employees (sales executives) + uses existing superuser as director
  - Call logs spread across different hours of today
  - Leads entered today from various sources
  - Follow-ups for today
  - A site visit for today

Usage:
    python manage.py seed_dashboard_data           # Create seed data
    python manage.py seed_dashboard_data --clear   # Remove seeded data first
    python manage.py seed_dashboard_data --password mypass123  # Custom password for test users

Test users created:
    username: raju_sales    password: Test@1234 (or --password value)
    username: priya_sales   password: Test@1234 (or --password value)

Login as raju_sales to see scoped (own) data.
Login as superuser to see all data (admin view).
"""
import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = 'Seed today\'s dashboard test data (call logs, leads, follow-ups, site visits)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Remove previously seeded test data before creating new data',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='Test@1234',
            help='Password for test employee accounts (default: Test@1234)',
        )

    def handle(self, *args, **options):
        from Users.models import User
        from Lead.models import Lead, LeadFollowUp, CallLog
        from SiteVisit.models import SiteVisit
        from ProjectManagement.models import Project
        from Core.Core.context.Context import set_user

        clear = options['clear']
        password = options['password']
        now = timezone.now()
        today = now.date()

        # =====================================================================
        # CLEAR previous seed data (identified by remarks/description markers)
        # =====================================================================
        SEED_MARKER = '[SEED_DATA]'

        if clear:
            self.stdout.write('Clearing previous seed data...')
            CallLog.objects.filter(device_platform='seed_test').delete()
            Lead.objects.filter(remarks__contains=SEED_MARKER).delete()
            LeadFollowUp.objects.filter(discussion_notes__contains=SEED_MARKER).delete()
            SiteVisit.objects.filter(remarks__contains=SEED_MARKER).delete()
            # Don't delete users/projects — they might be in use
            self.stdout.write(self.style.SUCCESS('Cleared.'))

        # =====================================================================
        # CREATE OR GET TEST EMPLOYEES
        # =====================================================================
        self.stdout.write('Creating/getting test employees...')

        # Create or get a "Sales" group
        sales_group, _ = Group.objects.get_or_create(name='Sales')

        raju, raju_created = User.objects.get_or_create(
            username='raju_sales',
            defaults={
                'first_name': 'Raju',
                'last_name': 'Kumar',
                'email': 'raju@royalrealitygroup.com',
                'phone': '9876543210',
                'designation': 'Sales Executive',
                'is_active': True,
                'lead_data_scope': 'OWN',
                'followup_data_scope': 'OWN',
                'sitevisit_data_scope': 'OWN',
                'booking_data_scope': 'OWN',
            }
        )
        if raju_created:
            raju.set_password(password)
            raju.save()
            raju.groups.add(sales_group)
            self.stdout.write(f'  Created: raju_sales (password: {password})')
        else:
            self.stdout.write(f'  Exists:  raju_sales')

        priya, priya_created = User.objects.get_or_create(
            username='priya_sales',
            defaults={
                'first_name': 'Priya',
                'last_name': 'Sharma',
                'email': 'priya@royalrealitygroup.com',
                'phone': '9876543211',
                'designation': 'Sales Executive',
                'is_active': True,
                'lead_data_scope': 'OWN',
                'followup_data_scope': 'OWN',
                'sitevisit_data_scope': 'OWN',
                'booking_data_scope': 'OWN',
            }
        )
        if priya_created:
            priya.set_password(password)
            priya.save()
            priya.groups.add(sales_group)
            self.stdout.write(f'  Created: priya_sales (password: {password})')
        else:
            self.stdout.write(f'  Exists:  priya_sales')

        employees = [raju, priya]

        # =====================================================================
        # GET OR CREATE A TEST PROJECT
        # =====================================================================
        project, _ = Project.objects.get_or_create(
            name='Green Valley Phase 2',
            defaults={
                'project_type': 'PLOT',
                'status': 'ACTIVE',
                'location': 'Vizag',
                'approval_type': 'VMRDA',
            }
        )
        self.stdout.write(f'  Project: {project.name} ({project.code})')

        # =====================================================================
        # SEED CALL LOGS (spread across today's hours)
        # =====================================================================
        self.stdout.write('Seeding call logs...')

        phone_numbers = [
            '9001234567', '9001234568', '9001234569', '9001234570',
            '9001234571', '9001234572', '9001234573', '9001234574',
            '9001234575', '9001234576', '9001234577', '9001234578',
            '9001234579', '9001234580', '9001234581', '9001234582',
            '9001234583', '9001234584', '9001234585', '9001234586',
            '9001234587', '9001234588', '9001234589', '9001234590',
            '9001234591', '9001234592', '9001234593', '9001234594',
            '9001234595', '9001234596', '9001234597', '9001234598',
        ]

        call_types = ['outgoing', 'outgoing', 'outgoing', 'incoming', 'missed']
        # Realistic hour distribution: more calls during 10-13 and 15-18
        hour_weights = {
            9: 3, 10: 6, 11: 8, 12: 5, 13: 4, 14: 3,
            15: 6, 16: 7, 17: 5, 18: 3, 19: 2, 20: 1,
        }

        calls_created = 0
        phone_idx = 0

        for emp in employees:
            for hour, weight in hour_weights.items():
                # Create `weight` number of calls for this hour
                num_calls = weight if emp == raju else max(1, weight - 2)
                for i in range(num_calls):
                    minute = random.randint(0, 59)
                    second = random.randint(0, 59)
                    call_time = timezone.make_aware(
                        timezone.datetime(today.year, today.month, today.day, hour, minute, second)
                    )

                    # Only create if the time is in the past
                    if call_time > now:
                        continue

                    phone = phone_numbers[phone_idx % len(phone_numbers)]
                    phone_idx += 1

                    call_type = random.choice(call_types)
                    duration = random.randint(5, 300) if call_type in ('outgoing', 'incoming') else 0

                    CallLog.objects.get_or_create(
                        phone_number=phone,
                        called_at=call_time,
                        called_by=emp,
                        defaults={
                            'call_type': call_type,
                            'duration_secs': duration,
                            'device_platform': 'seed_test',
                        }
                    )
                    calls_created += 1

        self.stdout.write(f'  Call logs: {calls_created} created/verified')

        # =====================================================================
        # SEED LEADS (entered today)
        # =====================================================================
        self.stdout.write('Seeding leads...')

        lead_data = [
            {'name': 'Ramesh Reddy', 'mobile': '9001234567', 'source': 'WEBSITE', 'emp': raju},
            {'name': 'Sunita Devi', 'mobile': '9001234568', 'source': 'FACEBOOK', 'emp': raju},
            {'name': 'Venkat Rao', 'mobile': '9001234569', 'source': 'GOOGLE_ADS', 'emp': raju},
            {'name': 'Lakshmi Naidu', 'mobile': '9001234570', 'source': 'REFERRALS', 'emp': raju},
            {'name': 'Anil Kumar', 'mobile': '9001234571', 'source': 'WHATSAPP', 'emp': raju},
            {'name': 'Kavitha P', 'mobile': '9001234572', 'source': '99ACRES', 'emp': priya},
            {'name': 'Suresh Babu', 'mobile': '9001234573', 'source': 'MAGICBRICKS', 'emp': priya},
            {'name': 'Divya Sri', 'mobile': '9001234574', 'source': 'INSTAGRAM', 'emp': priya},
        ]

        leads_created = 0
        created_leads = []
        for ld in lead_data:
            # Set thread-local user context so BaseModel.save() populates
            # created_by_identifier (required by post_save signal for status history)
            set_user(ld['emp'])

            lead, created = Lead.objects.get_or_create(
                mobile=ld['mobile'],
                assigned_employee=ld['emp'],
                defaults={
                    'name': ld['name'],
                    'lead_source': ld['source'],
                    'status': 'ONGOING',
                    'budget': f'{random.randint(20, 80)} Lakhs',
                    'preferred_area': random.choice(['Madhurawada', 'Gajuwaka', 'Rushikonda', 'Pendurthi']),
                    'property_requirement': random.choice(['Plot', 'Flat 2BHK', 'Flat 3BHK', 'Villa']),
                    'interested_project': project,
                    'remarks': f'{SEED_MARKER} Test lead for dashboard',
                }
            )
            created_leads.append(lead)
            if created:
                leads_created += 1

        self.stdout.write(f'  Leads: {leads_created} created, {len(created_leads)} total')

        # =====================================================================
        # SEED FOLLOW-UPS (for today)
        # =====================================================================
        self.stdout.write('Seeding follow-ups...')

        fu_types = ['CALL', 'WHATSAPP', 'MEETING', 'SITE_VISIT']
        fus_created = 0

        for lead in created_leads[:6]:  # First 6 leads get follow-ups
            emp = lead.assigned_employee
            set_user(emp)
            fu_type = random.choice(fu_types)
            hour = random.randint(9, 17)
            minute = random.randint(0, 59)

            _, created = LeadFollowUp.objects.get_or_create(
                lead=lead,
                follow_up_date=today,
                created_by=emp,
                defaults={
                    'follow_up_type': fu_type,
                    'follow_up_time': timezone.datetime(2000, 1, 1, hour, minute).time(),
                    'discussion_notes': f'{SEED_MARKER} Discussed project details, customer interested in plots.',
                    'next_follow_up_date': today + timedelta(days=random.randint(1, 5)),
                }
            )
            if created:
                fus_created += 1

        self.stdout.write(f'  Follow-ups: {fus_created} created')

        # =====================================================================
        # SEED SITE VISIT (for today)
        # =====================================================================
        self.stdout.write('Seeding site visits...')

        set_user(raju)
        sv, sv_created = SiteVisit.objects.get_or_create(
            customer_name='Ramesh Reddy',
            visit_date=today,
            assigned_employee=raju,
            defaults={
                'project': project,
                'project_name': project.name,
                'status': 'SCHEDULED',
                'remarks': f'{SEED_MARKER} Test site visit',
            }
        )

        set_user(priya)
        sv2, sv2_created = SiteVisit.objects.get_or_create(
            customer_name='Kavitha P',
            visit_date=today,
            assigned_employee=priya,
            defaults={
                'project': project,
                'project_name': project.name,
                'status': 'COMPLETED',
                'customer_feedback': 'Very impressed with the layout and amenities.',
                'remarks': f'{SEED_MARKER} Test site visit',
            }
        )

        sv_count = sum([sv_created, sv2_created])
        self.stdout.write(f'  Site visits: {sv_count} created')

        # =====================================================================
        # SUMMARY
        # =====================================================================
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Dashboard seed data ready!'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')
        self.stdout.write(f'  Test accounts:')
        self.stdout.write(f'    raju_sales  / {password}  (Sales Executive - sees own data)')
        self.stdout.write(f'    priya_sales / {password}  (Sales Executive - sees own data)')
        self.stdout.write(f'    [your superuser]          (Director - sees all data)')
        self.stdout.write('')
        self.stdout.write(f'  What to test:')
        self.stdout.write(f'    1. Login as superuser → Dashboard shows ALL employees data')
        self.stdout.write(f'    2. Login as raju_sales → Dashboard shows only Raju\'s calls/leads')
        self.stdout.write(f'    3. Click "Today\'s Insights" card → Detailed breakdown page')
        self.stdout.write(f'    4. Check hourly calling trend chart (peak around 10-11 AM)')
        self.stdout.write(f'    5. Employee Performance table shows Calls Today column')
        self.stdout.write('')
        self.stdout.write(f'  To clean up later:')
        self.stdout.write(f'    python manage.py seed_dashboard_data --clear')
        self.stdout.write('')
