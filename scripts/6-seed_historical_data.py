"""
Seed script: Generate 10 years of historical data for realistic dashboard charts.

Usage:
    python manage.py shell < scripts/6-seed_historical_data.py

Creates leads, site visits, and bookings spread across 10 years (2016-2026)
with realistic seasonal patterns, growth trends, and ups/downs.

Requires: 0-seed_groups_users.py and 2-seed_projects.py to be run first.
"""
import django
import os
import sys
import random
import math
from datetime import date, timedelta
from decimal import Decimal

if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BaseProject.settings')
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from Lead.models import Lead, LEAD_SOURCE_CHOICES, LEAD_STATUS_CHOICES
from SiteVisit.models import SiteVisit
from Booking.models import Booking
from Masters.models import Project
from Inventory.models import PlotInventory, FlatInventory

User = get_user_model()

# ============================================================================
# CONFIG
# ============================================================================

START_YEAR = 2016
END_YEAR = 2026  # current year

FIRST_NAMES = [
    'Venkat', 'Lakshmi', 'Suresh', 'Anitha', 'Ramesh', 'Padma', 'Naresh', 'Swathi',
    'Ganesh', 'Kavitha', 'Mahesh', 'Divya', 'Ravi', 'Sunitha', 'Srinivas', 'Meena',
    'Anil', 'Bhavani', 'Chandra', 'Deepika', 'Harish', 'Jyothi', 'Karthik', 'Lavanya',
    'Mohan', 'Nandini', 'Pavan', 'Radha', 'Sai', 'Uma', 'Vijay', 'Priya',
    'Rajesh', 'Sushma', 'Arvind', 'Pooja', 'Dinesh', 'Rekha', 'Satish', 'Anusha',
    'Prakash', 'Sindhu', 'Sudhir', 'Vasantha', 'Ashok', 'Geetha', 'Bhaskar', 'Nirmala',
    'Tarun', 'Shilpa', 'Manoj', 'Rani', 'Yogesh', 'Madhavi', 'Kishore', 'Savitha',
    'Srikanth', 'Aruna', 'Nagendra', 'Pallavi', 'Sunil', 'Vidya', 'Ramana', 'Durga',
    'Krishna', 'Saraswathi', 'Siddharth', 'Aarti', 'Gopal', 'Latha', 'Vishnu', 'Kamala',
    'Raju', 'Prema', 'Santosh', 'Jayanthi', 'Murali', 'Revathi', 'Venu', 'Hema',
    'Rahul', 'Deepa', 'Ajay', 'Saroja', 'Naveen', 'Pushpa', 'Lokesh', 'Manjula',
    'Sreedhar', 'Anuradha', 'Prasad', 'Usha', 'Ranga', 'Sailaja', 'Sekhar', 'Varalakshmi',
]

LAST_NAMES = [
    'Rao', 'Devi', 'Babu', 'Kumari', 'Reddy', 'Kumar', 'Sharma', 'Prasad',
    'Nair', 'Gupta', 'Joshi', 'Patel', 'Naidu', 'Verma', 'Choudhary', 'Gowda',
    'Shetty', 'Iyer', 'Pillai', 'Menon', 'Saxena', 'Mishra', 'Singh', 'Agarwal',
    'Kapoor', 'Das', 'Bhat', 'Hegde', 'Teja', 'Varma',
]

AREAS = [
    'Madhapur', 'Gachibowli', 'Kondapur', 'Kukatpally', 'Banjara Hills',
    'Jubilee Hills', 'Miyapur', 'Bachupally', 'Kompally', 'Shamshabad',
    'Patancheru', 'Nallagandla', 'Tellapur', 'Mokila', 'Narsingi',
]

BUDGETS = ['20-30L', '30-40L', '40-50L', '50-60L', '60-80L', '80L-1Cr', '1-1.5Cr', '1.5-2Cr']
PROPERTY_TYPES = ['2BHK', '3BHK', 'Plot 150sqyd', 'Plot 200sqyd', 'Plot 300sqyd', 'Villa', '4BHK']
SOURCES = [s[0] for s in LEAD_SOURCE_CHOICES]
STATUSES = [s[0] for s in LEAD_STATUS_CHOICES]
VISIT_STATUSES = ['COMPLETED', 'CANCELLED', 'SCHEDULED', 'CONFIRMED']
BOOKING_STATUSES = ['BOOKED', 'AGREEMENT', 'REGISTERED', 'CANCELLED']


def get_monthly_volume(year, month, base, growth_rate=0.05):
    """
    Calculate monthly volume with:
    - Year-over-year growth
    - Seasonal pattern (peaks in Oct-Dec, Jan-Mar; dips in Jun-Aug monsoon)
    - Random noise for realistic ups/downs
    """
    years_from_start = year - START_YEAR
    # Exponential growth
    growth = base * ((1 + growth_rate) ** years_from_start)

    # Seasonal multiplier (Indian real estate: peaks in festival season & year-end)
    seasonal = {
        1: 1.15, 2: 1.10, 3: 1.20,   # Q4 FY — year-end rush
        4: 0.90, 5: 0.85, 6: 0.70,   # Summer + start monsoon
        7: 0.65, 8: 0.60, 9: 0.80,   # Monsoon dip
        10: 1.25, 11: 1.30, 12: 1.10, # Festival season (Dussehra, Diwali)
    }
    multiplier = seasonal.get(month, 1.0)

    # COVID dip in 2020-2021
    if year == 2020 and month >= 4:
        multiplier *= 0.3
    elif year == 2020 and month < 4:
        multiplier *= 0.9
    elif year == 2021 and month <= 6:
        multiplier *= 0.5
    elif year == 2021 and month > 6:
        multiplier *= 0.8

    # Random noise ±20%
    noise = random.uniform(0.8, 1.2)

    volume = int(growth * multiplier * noise)
    return max(1, volume)


def random_date_in_month(year, month):
    """Get a random date within a given month."""
    if month == 12:
        max_day = 31
    else:
        next_month = date(year, month + 1, 1)
        max_day = (next_month - timedelta(days=1)).day
    day = random.randint(1, max_day)
    return date(year, month, day)


def run():
    print(f"\n{'='*60}")
    print("  SEEDING 10 YEARS OF HISTORICAL DATA (2016-2026)")
    print(f"{'='*60}\n")

    # Get dependencies
    users = list(User.objects.filter(
        is_active=True, is_superuser=False,
        groups__name__in=['Director', 'Team Leader', 'Sales Executive']
    ).distinct())
    if not users:
        users = list(User.objects.filter(is_active=True)[:3])
    if not users:
        print("  ERROR: No users found. Run 0-seed_groups_users.py first.")
        return

    projects = list(Project.objects.filter(is_deleted=False))
    if not projects:
        print("  ERROR: No projects found. Run 2-seed_projects.py first.")
        return

    print(f"  Users: {len(users)}")
    print(f"  Projects: {len(projects)}")

    today = date.today()
    total_leads = 0
    total_visits = 0
    total_bookings = 0

    # Base monthly volumes
    LEAD_BASE = 8       # ~8 leads/month in 2016, grows to ~15+ by 2026
    VISIT_BASE = 4      # ~4 visits/month in 2016
    BOOKING_BASE = 2    # ~2 bookings/month in 2016

    print(f"\n  Generating data month by month...\n")

    for year in range(START_YEAR, END_YEAR + 1):
        max_month = 12
        if year == END_YEAR:
            max_month = today.month  # Don't go beyond current month

        year_leads = 0
        year_visits = 0
        year_bookings = 0

        for month in range(1, max_month + 1):
            # Skip future dates
            month_date = date(year, month, 1)
            if month_date > today:
                break

            # Calculate volumes for this month
            num_leads = get_monthly_volume(year, month, LEAD_BASE, growth_rate=0.06)
            num_visits = get_monthly_volume(year, month, VISIT_BASE, growth_rate=0.05)
            num_bookings = get_monthly_volume(year, month, BOOKING_BASE, growth_rate=0.04)

            # Ensure visits <= leads and bookings <= visits
            num_visits = min(num_visits, int(num_leads * 0.7))
            num_bookings = min(num_bookings, int(num_visits * 0.6))

            # --- CREATE LEADS ---
            for _ in range(num_leads):
                lead_date = random_date_in_month(year, month)
                if lead_date > today:
                    continue

                fname = random.choice(FIRST_NAMES)
                lname = random.choice(LAST_NAMES)
                name = f"{fname} {lname}"
                mobile = f"9{random.randint(100000000, 999999999)}"
                user = random.choice(users)
                project = random.choice(projects)

                lead = Lead(
                    name=name,
                    mobile=mobile,
                    email=f"{fname.lower()}{random.randint(1,999)}@gmail.com",
                    budget=random.choice(BUDGETS),
                    preferred_area=random.choice(AREAS),
                    property_requirement=random.choice(PROPERTY_TYPES),
                    lead_source=random.choice(SOURCES),
                    assigned_employee=user,
                    interested_project=project,
                    status=random.choice(STATUSES),
                    remarks=f"Historical lead from {lead_date.strftime('%b %Y')}",
                    created_by_type='User',
                    created_by_identifier=str(user.id),
                    modified_by_type='User',
                    modified_by_identifier=str(user.id),
                )
                lead.save()
                # Backdate created_on
                Lead.objects.filter(pk=lead.pk).update(
                    created_on=timezone.make_aware(
                        timezone.datetime(lead_date.year, lead_date.month, lead_date.day,
                                          random.randint(8, 18), random.randint(0, 59))
                    )
                )
                total_leads += 1
                year_leads += 1

            # --- CREATE SITE VISITS ---
            for _ in range(num_visits):
                visit_date = random_date_in_month(year, month)
                if visit_date > today:
                    continue

                fname = random.choice(FIRST_NAMES)
                lname = random.choice(LAST_NAMES)
                user = random.choice(users)
                project = random.choice(projects)

                # Past visits are mostly completed
                if visit_date < today - timedelta(days=7):
                    status = random.choices(
                        ['COMPLETED', 'CANCELLED'], weights=[0.85, 0.15], k=1
                    )[0]
                else:
                    status = random.choice(VISIT_STATUSES)

                sv = SiteVisit(
                    customer_name=f"{fname} {lname}",
                    project=project,
                    project_name=project.name,
                    visit_date=visit_date,
                    assigned_employee=user,
                    status=status,
                    customer_feedback='Positive response.' if status == 'COMPLETED' else '',
                    remarks=f"Historical visit from {visit_date.strftime('%b %Y')}",
                    created_by_type='User',
                    created_by_identifier=str(user.id),
                    modified_by_type='User',
                    modified_by_identifier=str(user.id),
                )
                sv.save()
                total_visits += 1
                year_visits += 1

            # --- CREATE BOOKINGS ---
            for _ in range(num_bookings):
                booking_date = random_date_in_month(year, month)
                if booking_date > today:
                    continue

                fname = random.choice(FIRST_NAMES)
                lname = random.choice(LAST_NAMES)
                user = random.choice(users)
                project = random.choice(projects)

                # Older bookings more likely registered
                days_old = (today - booking_date).days
                if days_old > 365:
                    status = random.choices(
                        ['REGISTERED', 'CANCELLED'], weights=[0.8, 0.2], k=1
                    )[0]
                elif days_old > 180:
                    status = random.choices(
                        ['REGISTERED', 'AGREEMENT', 'CANCELLED'], weights=[0.5, 0.3, 0.2], k=1
                    )[0]
                elif days_old > 60:
                    status = random.choices(
                        ['AGREEMENT', 'REGISTERED', 'BOOKED'], weights=[0.4, 0.3, 0.3], k=1
                    )[0]
                else:
                    status = random.choices(
                        ['BOOKED', 'AGREEMENT'], weights=[0.6, 0.4], k=1
                    )[0]

                # Price grows over years (real estate appreciation)
                base_price = random.randint(2000000, 8000000)
                appreciation = 1 + (0.08 * (year - START_YEAR))  # 8% per year
                agreed_price = Decimal(int(base_price * appreciation))
                booking_amount = agreed_price * Decimal(random.randint(10, 20)) / Decimal(100)

                unit_type = random.choice(['PLOT', 'FLAT'])
                unit_number = f"{'P' if unit_type == 'PLOT' else 'F'}-{random.randint(1, 200):03d}"

                booking = Booking(
                    customer_name=f"{fname} {lname}",
                    customer_mobile=f"9{random.randint(100000000, 999999999)}",
                    customer_email=f"{fname.lower()}{random.randint(1,999)}@gmail.com",
                    project=project,
                    unit_type=unit_type,
                    unit_number=unit_number,
                    agreed_price=agreed_price,
                    booking_amount=booking_amount,
                    booking_date=booking_date,
                    sales_executive=user,
                    status=status,
                    cancellation_reason='Changed plans.' if status == 'CANCELLED' else '',
                    cancelled_date=booking_date + timedelta(days=random.randint(10, 30)) if status == 'CANCELLED' else None,
                    remarks=f"Historical booking from {booking_date.strftime('%b %Y')}",
                    created_by_type='User',
                    created_by_identifier=str(user.id),
                    modified_by_type='User',
                    modified_by_identifier=str(user.id),
                )
                booking.save()
                total_bookings += 1
                year_bookings += 1

        print(f"  {year}: Leads={year_leads}, Visits={year_visits}, Bookings={year_bookings}")

    print(f"\n{'='*60}")
    print("  COMPLETE!")
    print(f"{'='*60}\n")
    print(f"  Total Leads Created:    {total_leads}")
    print(f"  Total Visits Created:   {total_visits}")
    print(f"  Total Bookings Created: {total_bookings}")
    print(f"\n  Grand Totals in DB:")
    print(f"    Leads:    {Lead.objects.filter(is_deleted=False).count()}")
    print(f"    Visits:   {SiteVisit.objects.filter(is_deleted=False).count()}")
    print(f"    Bookings: {Booking.objects.filter(is_deleted=False).count()}")
    print()


if __name__ == '__main__' or True:
    run()
