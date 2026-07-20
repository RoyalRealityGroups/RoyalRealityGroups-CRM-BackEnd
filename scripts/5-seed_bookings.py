"""
Seed script: Create sample Bookings.

Usage:
    python manage.py shell < scripts/seed_bookings.py

Creates bookings linking leads to inventory units (plots/flats).
Requires: seed_leads.py, seed_projects.py, seed_inventory.py to be run first.
"""
import django
import os
import sys
import random
from datetime import date, timedelta
from decimal import Decimal

if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BaseProject.settings')
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    django.setup()

from django.contrib.auth import get_user_model
from Lead.models import Lead
from Masters.models import Project
from Inventory.models import PlotInventory, FlatInventory
from Booking.models import Booking, BOOKING_STATUS_CHOICES

User = get_user_model()

STATUSES = [s[0] for s in BOOKING_STATUS_CHOICES]


def seed_bookings():
    """Create sample bookings."""
    print(f"\n{'='*50}")
    print("  SEEDING BOOKINGS")
    print(f"{'='*50}\n")

    # Get sales users
    users = list(User.objects.filter(
        is_active=True, is_superuser=False,
        groups__name__in=['Director', 'Team Leader', 'Sales Executive']
    ).distinct())

    if not users:
        print("  No assignable users found. Run seed_groups_users.py first.")
        return

    # Get leads that are far enough in pipeline
    leads = list(Lead.objects.filter(
        is_deleted=False,
        status__in=['NEGOTIATION', 'BOOKING', 'REGISTRATION', 'SITE_VISIT_COMPLETED']
    ))

    if not leads:
        # Fallback — use any leads
        leads = list(Lead.objects.filter(is_deleted=False).order_by('?')[:10])

    if not leads:
        print("  No leads found. Run seed_leads.py first.")
        return

    # Check existing
    existing = Booking.objects.filter(is_deleted=False).count()
    if existing >= 10:
        print(f"  Already have {existing} bookings. Skipping.")
        return

    # Get available plots and flats
    available_plots = list(PlotInventory.objects.filter(
        is_deleted=False, status__in=['AVAILABLE', 'BLOCKED']
    ).select_related('project')[:30])

    available_flats = list(FlatInventory.objects.filter(
        is_deleted=False, status__in=['AVAILABLE', 'BLOCKED']
    ).select_related('project')[:30])

    if not available_plots and not available_flats:
        print("  No available inventory found. Run seed_inventory.py first.")
        return

    today = date.today()
    created_count = 0

    # Create bookings for ~60% of qualified leads
    for lead in leads:
        if random.random() > 0.6:
            continue

        executive = random.choice(users)
        days_ago = random.randint(1, 60)
        booking_date = today - timedelta(days=days_ago)

        # Decide plot or flat
        use_plot = random.random() < 0.5 and available_plots
        use_flat = not use_plot and available_flats

        if use_plot and available_plots:
            unit = available_plots.pop(random.randint(0, len(available_plots) - 1))
            project = unit.project
            agreed_price = unit.total_price or Decimal(random.randint(2000000, 8000000))
            unit_number = unit.plot_number
            unit_type = 'PLOT'
            plot_ref = unit
            flat_ref = None
        elif use_flat and available_flats:
            unit = available_flats.pop(random.randint(0, len(available_flats) - 1))
            project = unit.project
            agreed_price = unit.price or Decimal(random.randint(4000000, 15000000))
            unit_number = f"{unit.tower}-{unit.unit_number}"
            unit_type = 'FLAT'
            plot_ref = None
            flat_ref = unit
        else:
            continue

        # Booking amount is 10-20% of agreed price
        booking_amount = agreed_price * Decimal(random.randint(10, 20)) / Decimal(100)

        # Status weighted by age
        if days_ago > 40:
            status = random.choices(
                ['REGISTERED', 'AGREEMENT', 'CANCELLED'], weights=[0.4, 0.4, 0.2], k=1
            )[0]
        elif days_ago > 20:
            status = random.choices(
                ['AGREEMENT', 'BOOKED', 'REGISTERED'], weights=[0.5, 0.3, 0.2], k=1
            )[0]
        else:
            status = random.choices(
                ['BOOKED', 'AGREEMENT'], weights=[0.7, 0.3], k=1
            )[0]

        booking = Booking.objects.create(
            lead=lead,
            customer_name=lead.name,
            customer_mobile=lead.mobile,
            customer_email=lead.email,
            project=project,
            unit_type=unit_type,
            plot=plot_ref,
            flat=flat_ref,
            unit_number=unit_number,
            agreed_price=agreed_price,
            booking_amount=booking_amount,
            booking_date=booking_date,
            sales_executive=executive,
            status=status,
            remarks=f"Booking for {unit_number} in {project.name}",
            created_by_type='User',
            created_by_identifier=str(executive.id),
            modified_by_type='User',
            modified_by_identifier=str(executive.id),
        )

        # Update inventory status to BOOKED
        if plot_ref:
            plot_ref.status = 'BOOKED'
            plot_ref.save(update_fields=['status'])
        if flat_ref:
            flat_ref.status = 'BOOKED'
            flat_ref.save(update_fields=['status'])

        created_count += 1
        print(f"  Created: {lead.name} → {project.name} {unit_number} (₹{agreed_price:,.0f}, {status})")

    print(f"\n  Total created: {created_count}")


def run():
    seed_bookings()

    print(f"\n{'='*50}")
    print("  SUMMARY")
    print(f"{'='*50}\n")
    total = Booking.objects.filter(is_deleted=False).count()
    print(f"  Total Bookings: {total}")
    for status, label in BOOKING_STATUS_CHOICES:
        count = Booking.objects.filter(status=status, is_deleted=False).count()
        if count > 0:
            print(f"    {label}: {count}")

    # Revenue summary
    from django.db.models import Sum
    revenue = Booking.objects.filter(
        is_deleted=False
    ).exclude(status='CANCELLED').aggregate(
        total=Sum('agreed_price'),
        collected=Sum('booking_amount'),
    )
    print(f"\n  Total Revenue: ₹{float(revenue['total'] or 0):,.0f}")
    print(f"  Collected (Booking Amount): ₹{float(revenue['collected'] or 0):,.0f}")
    print()


if __name__ == '__main__' or True:
    run()
