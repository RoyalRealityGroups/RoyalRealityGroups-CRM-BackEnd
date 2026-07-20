"""
Seed script: Create sample Plot and Flat inventory.

Usage:
    python manage.py shell < scripts/seed_inventory.py

Creates plots for Plot-type projects and flats for Flat-type projects.
Requires: seed_projects.py to be run first.
"""
import django
import os
import sys
import random
from decimal import Decimal

if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BaseProject.settings')
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    django.setup()

from django.contrib.auth import get_user_model
from Masters.models import Project
from Inventory.models import PlotInventory, FlatInventory, INVENTORY_STATUS_CHOICES, FACING_CHOICES

User = get_user_model()

FACINGS = [f[0] for f in FACING_CHOICES]
STATUSES = [s[0] for s in INVENTORY_STATUS_CHOICES]
FLAT_TYPES = ['2BHK', '3BHK', '3BHK', '4BHK']
TOWERS = ['Tower A', 'Tower B', 'Tower C']


def seed_plots():
    """Create plots for Plot/Villa/Mixed projects."""
    print(f"\n{'='*50}")
    print("  SEEDING PLOT INVENTORY")
    print(f"{'='*50}\n")

    user = User.objects.filter(is_active=True).first()
    user_id = str(user.id) if user else ''

    plot_projects = Project.objects.filter(
        is_deleted=False,
        project_type__in=['PLOT', 'VILLA', 'MIXED']
    )

    if not plot_projects.exists():
        print("  No Plot/Villa/Mixed projects found. Run seed_projects.py first.")
        return

    created_count = 0

    for project in plot_projects:
        # Create 15-25 plots per project
        num_plots = random.randint(15, 25)
        existing = PlotInventory.objects.filter(project=project, is_deleted=False).count()

        if existing >= 10:
            print(f"  Skipping {project.name} — already has {existing} plots")
            continue

        for i in range(1, num_plots + 1):
            plot_number = f"P-{i:03d}"

            if PlotInventory.objects.filter(project=project, plot_number=plot_number).exists():
                continue

            area_sqyd = Decimal(random.randint(120, 400))
            area_sqft = area_sqyd * Decimal('9')  # approx conversion
            price_per_sqyd = Decimal(random.randint(8000, 25000))
            total_price = area_sqyd * price_per_sqyd

            # Weight status: mostly available, some booked/blocked
            status_weights = [0.5, 0.15, 0.25, 0.1]  # AVAILABLE, BLOCKED, BOOKED, REGISTERED
            status = random.choices(STATUSES, weights=status_weights, k=1)[0]

            PlotInventory.objects.create(
                project=project,
                plot_number=plot_number,
                area_sqyd=area_sqyd,
                area_sqft=area_sqft,
                facing=random.choice(FACINGS),
                road_width=random.choice(['30 feet', '40 feet', '60 feet']),
                price_per_sqyd=price_per_sqyd,
                total_price=total_price,
                status=status,
                created_by_type='User',
                created_by_identifier=user_id,
                modified_by_type='User',
                modified_by_identifier=user_id,
            )
            created_count += 1

        print(f"  {project.name}: {num_plots} plots created")

    print(f"\n  Total plots created: {created_count}")


def seed_flats():
    """Create flats for Flat/Mixed projects."""
    print(f"\n{'='*50}")
    print("  SEEDING FLAT INVENTORY")
    print(f"{'='*50}\n")

    user = User.objects.filter(is_active=True).first()
    user_id = str(user.id) if user else ''

    flat_projects = Project.objects.filter(
        is_deleted=False,
        project_type__in=['FLAT', 'MIXED']
    )

    if not flat_projects.exists():
        print("  No Flat/Mixed projects found. Run seed_projects.py first.")
        return

    created_count = 0

    for project in flat_projects:
        existing = FlatInventory.objects.filter(project=project, is_deleted=False).count()

        if existing >= 10:
            print(f"  Skipping {project.name} — already has {existing} flats")
            continue

        # 2-3 towers, 5-10 floors, 2-4 units per floor
        towers = random.sample(TOWERS, k=random.randint(2, 3))
        num_floors = random.randint(5, 10)
        units_per_floor = random.randint(2, 4)

        for tower in towers:
            for floor in range(1, num_floors + 1):
                for unit in range(1, units_per_floor + 1):
                    unit_number = f"{floor}{str(unit).zfill(2)}"

                    if FlatInventory.objects.filter(project=project, tower=tower, unit_number=unit_number).exists():
                        continue

                    flat_type = random.choice(FLAT_TYPES)
                    area_map = {'2BHK': (1000, 1300), '3BHK': (1400, 1800), '4BHK': (2000, 2600)}
                    area_range = area_map.get(flat_type, (1200, 1600))
                    area_sqft = Decimal(random.randint(*area_range))
                    carpet_area = area_sqft * Decimal('0.7')
                    price = area_sqft * Decimal(random.randint(5000, 9000))

                    status_weights = [0.5, 0.15, 0.25, 0.1]
                    status = random.choices(STATUSES, weights=status_weights, k=1)[0]

                    FlatInventory.objects.create(
                        project=project,
                        tower=tower,
                        floor=floor,
                        unit_number=unit_number,
                        flat_type=flat_type,
                        area_sqft=area_sqft,
                        carpet_area_sqft=carpet_area,
                        facing=random.choice(FACINGS),
                        price=price,
                        status=status,
                        created_by_type='User',
                        created_by_identifier=user_id,
                        modified_by_type='User',
                        modified_by_identifier=user_id,
                    )
                    created_count += 1

        print(f"  {project.name}: {len(towers)} towers × {num_floors} floors created")

    print(f"\n  Total flats created: {created_count}")


def run():
    seed_plots()
    seed_flats()

    print(f"\n{'='*50}")
    print("  SUMMARY")
    print(f"{'='*50}\n")
    print(f"  Total Plots: {PlotInventory.objects.filter(is_deleted=False).count()}")
    print(f"  Total Flats: {FlatInventory.objects.filter(is_deleted=False).count()}")
    print(f"\n  By status:")
    for status, label in INVENTORY_STATUS_CHOICES:
        plots = PlotInventory.objects.filter(status=status, is_deleted=False).count()
        flats = FlatInventory.objects.filter(status=status, is_deleted=False).count()
        print(f"    {label}: {plots} plots, {flats} flats")
    print()


if __name__ == '__main__' or True:
    run()
