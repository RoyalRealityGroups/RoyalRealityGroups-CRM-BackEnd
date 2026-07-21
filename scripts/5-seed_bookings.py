"""
Seed script: Create 50+ sample Bookings.

Usage:
    python manage.py shell < scripts/5-seed_bookings.py

Creates bookings linking leads to inventory units (plots/flats).
Requires: 1-seed_leads.py, 2-seed_projects.py, 4-seed_inventory.py to be run first.
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
    """Create 50+ sample bookings."""
    print(f"\n{'='*50}")
    print("  SEEDING BOOKINGS (50+ records)")
    print(f"{'='*50}\n")

    # Get sales users
    users = list(User.objects.filter(
        is_active=True, is_superuser=False,
        groups__name__in=['Director', 'Team Leader', 'Sales Executive']
    ).distinct())

    if not users:
        print("  No assignable users found. Run 0-seed_groups_users.py first.")
        return

    # Get all leads
    leads = list(Lead.objects.filter(is_deleted=False))
    if not leads:
        print("  No leads found. Run 1-seed_leads.py first.")
        return

    # Get available plots and flats
    available_plots = list(PlotInventory.objects.filter(
        is_deleted=False, status__in=['AVAILABLE', 'BLOCKED']
    ).select_related('project'))

    available_flats = list(FlatInventory.objects.filter(
        is_deleted=False, status__in=['AVAILABLE', 'BLOCKED']
    ).select_related('project'))

    if not available_plots and not available_flats:
        print("  No available inventory found. Run 4-seed_inventory.py first.")
        return

    print(f"  Available plots: {len(available_plots)}")
    print(f"  Available flats: {len(available_flats)}")
    print(f"  Leads available: {len(leads)}")

    today = date.today()
    created_count = 0
    target_count = 55

    # Shuffle leads — some leads may get multiple bookings (different projects)
    booking_leads = leads.copy()
    random.shuffle(booking_leads)
    # Extend with repeats if needed
    while len(booking_leads) < target_count:
        booking_leads.extend(random.sample(leads, min(20, len(leads))))

    for i in range(target_count):
        lead = booking_leads[i]
        executive = random.choice(users)
        days_ago = random.randint(1, 90)
        booking_date = today - timedelta(days=days_ago)

        # Decide plot or flat
        use_plot = random.random() < 0.5 and available_plots
        use_flat = not use_plot and available_flats

        if use_plot and available_plots:
            unit = available_plots.pop(random.randint(0, min(len(available_plots) - 1, 50)))
            project = unit.project
            agreed_price = unit.total_price or Decimal(random.randint(2000000, 8000000))
            unit_number = unit.plot_number
            unit_type = 'PLOT'
            plot_ref = unit
            flat_ref = None
        elif available_flats:
            unit = available_flats.pop(random.randint(0, min(len(available_flats) - 1, 50)))
            project = unit.project
            agreed_price = unit.price or Decimal(random.randint(4000000, 15000000))
            unit_number = f"{unit.tower}-{unit.unit_number}" if unit.tower else unit.unit_number
            unit_type = 'FLAT'
            plot_ref = None
            flat_ref = unit
        elif available_plots:
            unit = available_plots.pop(random.randint(0, min(len(available_plots) - 1, 20)))
            project = unit.project
            agreed_price = unit.total_price or Decimal(random.randint(2000000, 8000000))
            unit_number = unit.plot_number
            unit_type = 'PLOT'
            plot_ref = unit
            flat_ref = None
        else:
            print(f"  Ran out of inventory at {created_count} bookings.")
            break

        # Booking amount is 10-25% of agreed price
        booking_amount = agreed_price * Decimal(random.randint(10, 25)) / Decimal(100)

        # Status weighted by age
        if days_ago > 60:
            status = random.choices(
                ['REGISTERED', 'AGREEMENT', 'CANCELLED'], weights=[0.5, 0.3, 0.2], k=1
            )[0]
        elif days_ago > 30:
            status = random.choices(
                ['AGREEMENT', 'REGISTERED', 'BOOKED', 'CANCELLED'], weights=[0.4, 0.25, 0.2, 0.15], k=1
            )[0]
        elif days_ago > 14:
            status = random.choices(
                ['BOOKED', 'AGREEMENT', 'REGISTERED'], weights=[0.5, 0.35, 0.15], k=1
            )[0]
        else:
            status = random.choices(
                ['BOOKED', 'AGREEMENT'], weights=[0.75, 0.25], k=1
            )[0]

        cancellation_reason = ''
        cancelled_date = None
        if status == 'CANCELLED':
            cancellation_reason = random.choice([
                'Customer found better deal elsewhere.',
                'Unable to arrange finances.',
                'Family decided against the location.',
                'Personal reasons.',
                'Changed requirement to different property type.',
            ])
            cancelled_date = booking_date + timedelta(days=random.randint(5, 20))

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
            cancellation_reason=cancellation_reason,
            cancelled_date=cancelled_date,
            remarks=f"Booking for {unit_number} in {project.name}",
            created_by_type='User',
            created_by_identifier=str(executive.id),
            modified_by_type='User',
            modified_by_identifier=str(executive.id),
        )

        # Update inventory status
        if status != 'CANCELLED':
            inv_status = 'REGISTERED' if status == 'REGISTERED' else 'BOOKED'
            if plot_ref:
                plot_ref.status = inv_status
                plot_ref.save(update_fields=['status'])
            if flat_ref:
                flat_ref.status = inv_status
                flat_ref.save(update_fields=['status'])

        created_count += 1

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
