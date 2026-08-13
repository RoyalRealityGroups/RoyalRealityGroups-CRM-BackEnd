"""
Seed script: Availability List — 10 projects covering all scenarios.

Usage:
    python manage.py shell < scripts/7-seed_availability.py
  OR:
    cd RoyalRealityGroups-CRM-BackEnd
    source venv/bin/activate
    python manage.py shell -c "exec(open('scripts/7-seed_availability.py').read())"

Scenarios covered:
  1. FLATS project  — multiple towers (blocks), floors, mixed unit types
  2. PLOTS project  — single block with plots, varied areas + prices
  3. MIXED project  — both a tower block and a plots block
  4. FLATS project  — fully SOLD OUT (all units REGISTERED)
  5. FLATS project  — UPCOMING (all units AVAILABLE, no sales yet)
  6. PLOTS project  — partial sales (mix of every status)
  7. FLATS project  — large high-rise (3 towers × 15 floors × 4 units)
  8. PLOTS project  — small layout (1 block, 20 plots, mostly available)
  9. FLATS project  — luxury villas / duplex units, premium pricing
 10. MIXED project  — COMPLETED project, majority REGISTERED

Safe to re-run — skips existing projects by name.
"""
import django, os, sys, random
from decimal import Decimal
from datetime import date

if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BaseProject.settings')
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    django.setup()

from django.contrib.auth import get_user_model
from Availability.models import (
    AvailabilityProject, AvailabilityBlock, AvailabilityUnit,
)

User = get_user_model()

# ── helpers ───────────────────────────────────────────────────────────────────

FACINGS  = ['EAST', 'WEST', 'NORTH', 'SOUTH', 'NE', 'NW', 'SE', 'SW']
STATUSES = ['AVAILABLE', 'BLOCKED', 'BOOKED', 'REGISTERED']

def _user_audit(user):
    uid = str(user.id) if user else ''
    return dict(
        created_by_type='User', created_by_identifier=uid,
        modified_by_type='User', modified_by_identifier=uid,
    )

def _pick_status(weights=(0.50, 0.10, 0.25, 0.15)):
    """weights = [available, blocked, booked, registered]"""
    return random.choices(STATUSES, weights=weights, k=1)[0]

def _make_project(data, user):
    name = data['name']
    if AvailabilityProject.objects.filter(name=name, is_deleted=False).exists():
        p = AvailabilityProject.objects.get(name=name, is_deleted=False)
        print(f"  Exists  : {name}")
        return p, False
    p = AvailabilityProject.objects.create(**data, **_user_audit(user))
    print(f"  Created : {name}  [{data['project_type']} / {data['status']}]")
    return p, True

def _make_block(project, name, description='', total_floors=None, order=0, user=None):
    b, _ = AvailabilityBlock.objects.get_or_create(
        project=project, name=name,
        defaults=dict(
            description=description,
            total_floors=total_floors,
            order=order,
            **_user_audit(user),
        ),
    )
    return b

def _bulk_units(block, units_data, user):
    """Hard-replace all units in a block (mirrors the view logic)."""
    AvailabilityUnit.objects.filter(block=block).delete()
    objs = [AvailabilityUnit(block=block, **u, **_user_audit(user)) for u in units_data]
    AvailabilityUnit.objects.bulk_create(objs)
    return len(objs)


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 1 — Multi-tower apartment complex (FLATS / ACTIVE)
#   3 towers × 10 floors × 4 units  =  120 units
#   Mixed statuses, mixed flat types
# ─────────────────────────────────────────────────────────────────────────────
def seed_scenario_1(user):
    print("\n[1] Iconica Residency — multi-tower FLATS (ACTIVE)")
    p, _ = _make_project(dict(
        name='Iconica Residency',
        developer_name='Iconica Developers',
        project_type='FLATS',
        location='Gachibowli, Hyderabad',
        city='Hyderabad',
        total_area='3.2 Acres',
        price_range_min=Decimal('7500000'),
        price_range_max=Decimal('18000000'),
        approval_type='HMDA',
        approval_number='HMDA/2024/GCB/1102',
        status='ACTIVE',
        possession_date=date(2026, 12, 31),
        contact_person='Ramesh Kumar',
        contact_phone='9876543210',
        description='Premium apartments in the heart of Gachibowli with modern amenities.',
        amenities='Swimming Pool, Gym, Clubhouse, Children Play Area, 24/7 Security, Power Backup',
        rera_number='P02400006789',
        is_active=True,
    ), user)

    flat_types = ['2BHK', '2BHK', '3BHK', '3BHK', '4BHK']
    areas      = {'2BHK': 1150, '3BHK': 1650, '4BHK': 2200}

    towers = [
        ('Tower A', 'East-facing premium tower', 10),
        ('Tower B', 'West-facing tower with garden view', 10),
        ('Tower C', 'North-facing corner tower', 10),
    ]

    total = 0
    for t_name, t_desc, floors in towers:
        block = _make_block(p, t_name, t_desc, total_floors=floors, order=towers.index((t_name, t_desc, floors)), user=user)
        units = []
        for floor in range(1, floors + 1):
            for unit_pos in range(1, 5):   # 4 units per floor
                ft = flat_types[(floor + unit_pos) % len(flat_types)]
                area = Decimal(areas[ft] + random.randint(-50, 100))
                price = area * Decimal(random.randint(6500, 9500))
                units.append(dict(
                    unit_number=f'{floor:02d}{unit_pos:02d}',
                    unit_type=ft,
                    floor=floor,
                    area_sqft=area,
                    carpet_area_sqft=round(area * Decimal('0.72'), 2),
                    facing=random.choice(FACINGS),
                    price=price,
                    status=_pick_status((0.45, 0.10, 0.30, 0.15)),
                ))
        total += _bulk_units(block, units, user)
    print(f"    → {total} units across {len(towers)} towers")


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 2 — Open plot layout (PLOTS / ACTIVE)
#   1 block "Plots" with 60 plots, varied areas + weighted statuses
# ─────────────────────────────────────────────────────────────────────────────
def seed_scenario_2(user):
    print("\n[2] MVV Green Valley — plot layout (ACTIVE)")
    p, _ = _make_project(dict(
        name='MVV Green Valley',
        developer_name='MVV Constructions',
        project_type='PLOTS',
        location='Shadnagar, Hyderabad',
        city='Hyderabad',
        total_area='8.5 Acres',
        price_range_min=Decimal('1800000'),
        price_range_max=Decimal('5500000'),
        approval_type='DTCP',
        approval_number='DTCP/HYD/2024/441',
        status='ACTIVE',
        possession_date=date(2025, 6, 30),
        contact_person='Venkat Rao',
        contact_phone='9988776655',
        description='DTCP-approved gated community plots with wide roads and full amenities.',
        amenities='24/7 Security, Wide Roads, Electricity, Water Supply, Sewage, Parks',
        rera_number='P02400003321',
        is_active=True,
    ), user)

    block = _make_block(p, 'Phase 1 Plots', 'Main layout plots', order=0, user=user)
    units = []
    for i in range(1, 61):
        area_sqyd = Decimal(random.randint(100, 350))
        ppsqyd    = Decimal(random.randint(12000, 22000))
        units.append(dict(
            unit_number=f'PLT-{i:03d}',
            unit_type='PLOT',
            area_sqyd=area_sqyd,
            area_sqft=round(area_sqyd * Decimal('9'), 2),
            facing=random.choice(FACINGS),
            price=round(area_sqyd * ppsqyd, 2),
            status=_pick_status((0.50, 0.10, 0.25, 0.15)),
            remarks=f'Corner plot' if i % 10 == 0 else '',
        ))
    n = _bulk_units(block, units, user)
    print(f"    → {n} plots in 1 block")


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 3 — Mixed project: tower block + plot block (MIXED / ACTIVE)
# ─────────────────────────────────────────────────────────────────────────────
def seed_scenario_3(user):
    print("\n[3] MK Harmony Township — MIXED (flats + plots, ACTIVE)")
    p, _ = _make_project(dict(
        name='MK Harmony Township',
        developer_name='MK Builders',
        project_type='MIXED',
        location='Mokila, Hyderabad',
        city='Hyderabad',
        total_area='12 Acres',
        price_range_min=Decimal('2500000'),
        price_range_max=Decimal('14000000'),
        approval_type='HMDA',
        status='ACTIVE',
        possession_date=date(2027, 3, 31),
        contact_person='Mohan Krishnan',
        contact_phone='9123456789',
        description='Township with both apartment towers and villa plots in a gated community.',
        amenities='Clubhouse, Pool, Gym, Kids Zone, Walking Track, Landscaped Gardens',
        is_active=True,
    ), user)

    # block 1 — apartment tower
    tower = _make_block(p, 'Harmony Tower', 'G+12 luxury apartments', total_floors=12, order=0, user=user)
    t_units = []
    for floor in range(1, 13):
        for pos in range(1, 5):
            ft = ['2BHK', '3BHK', '3BHK', '4BHK'][pos - 1]
            area = Decimal(random.randint(1100, 2100))
            t_units.append(dict(
                unit_number=f'{floor:02d}{pos:02d}',
                unit_type=ft,
                floor=floor,
                area_sqft=area,
                carpet_area_sqft=round(area * Decimal('0.72'), 2),
                facing=random.choice(FACINGS),
                price=area * Decimal(random.randint(6000, 9000)),
                status=_pick_status((0.40, 0.10, 0.35, 0.15)),
            ))
    n1 = _bulk_units(tower, t_units, user)

    # block 2 — villa plots
    plots_blk = _make_block(p, 'Villa Plots', 'Premium villa plots around the township', order=1, user=user)
    p_units = []
    for i in range(1, 31):
        area_sqyd = Decimal(random.randint(150, 400))
        p_units.append(dict(
            unit_number=f'VP-{i:03d}',
            unit_type='VILLA',
            area_sqyd=area_sqyd,
            area_sqft=round(area_sqyd * Decimal('9'), 2),
            facing=random.choice(FACINGS),
            price=area_sqyd * Decimal(random.randint(18000, 35000)),
            status=_pick_status((0.45, 0.12, 0.28, 0.15)),
        ))
    n2 = _bulk_units(plots_blk, p_units, user)
    print(f"    → {n1} apartments + {n2} villa plots")


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 4 — Fully SOLD OUT project (all REGISTERED)
# ─────────────────────────────────────────────────────────────────────────────
def seed_scenario_4(user):
    print("\n[4] Heritage Heights — SOLD OUT (all REGISTERED)")
    p, _ = _make_project(dict(
        name='Heritage Heights',
        developer_name='Heritage Realty',
        project_type='FLATS',
        location='Kukatpally, Hyderabad',
        city='Hyderabad',
        total_area='1.8 Acres',
        price_range_min=Decimal('5500000'),
        price_range_max=Decimal('9500000'),
        approval_type='HMDA',
        status='SOLD_OUT',
        possession_date=date(2024, 3, 31),
        description='Completed and fully registered project. Handover done.',
        is_active=True,
    ), user)

    block = _make_block(p, 'Block A', 'Only block — G+8', total_floors=8, order=0, user=user)
    units = []
    for floor in range(1, 9):
        for pos in range(1, 5):
            area = Decimal(random.randint(1050, 1800))
            units.append(dict(
                unit_number=f'{floor:02d}{pos:02d}',
                unit_type=random.choice(['2BHK', '3BHK']),
                floor=floor,
                area_sqft=area,
                carpet_area_sqft=round(area * Decimal('0.72'), 2),
                facing=random.choice(FACINGS),
                price=area * Decimal(random.randint(5500, 7000)),
                status='REGISTERED',   # ← ALL REGISTERED
            ))
    n = _bulk_units(block, units, user)
    print(f"    → {n} units, all REGISTERED")


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 5 — UPCOMING project (all AVAILABLE, no sales)
# ─────────────────────────────────────────────────────────────────────────────
def seed_scenario_5(user):
    print("\n[5] Sapphire Towers — UPCOMING (all AVAILABLE)")
    p, _ = _make_project(dict(
        name='Sapphire Towers',
        developer_name='Sapphire Developers',
        project_type='FLATS',
        location='Narsingi, Hyderabad',
        city='Hyderabad',
        total_area='2.5 Acres',
        price_range_min=Decimal('8500000'),
        price_range_max=Decimal('22000000'),
        approval_type='HMDA',
        approval_number='HMDA/2025/NRS/2201',
        status='UPCOMING',
        possession_date=date(2028, 6, 30),
        contact_person='Suresh Mehta',
        contact_phone='9001122334',
        description='Pre-launch luxury towers. Booking open soon.',
        amenities='Rooftop Pool, Gym, Concierge, EV Charging, Smart Home',
        rera_number='P02400009988',
        is_active=True,
    ), user)

    towers = [('Tower S1', 12), ('Tower S2', 12)]
    total = 0
    for idx, (t_name, floors) in enumerate(towers):
        block = _make_block(p, t_name, f'Premium tower {idx+1}', total_floors=floors, order=idx, user=user)
        units = []
        for floor in range(1, floors + 1):
            for pos in range(1, 5):
                ft = ['2BHK', '3BHK', '3BHK', 'PENTHOUSE'][pos - 1]
                area = Decimal(random.randint(1200, 3500))
                units.append(dict(
                    unit_number=f'{floor:02d}{pos:02d}',
                    unit_type=ft,
                    floor=floor,
                    area_sqft=area,
                    carpet_area_sqft=round(area * Decimal('0.72'), 2),
                    facing=random.choice(FACINGS),
                    price=area * Decimal(random.randint(8000, 14000)),
                    status='AVAILABLE',  # ← ALL AVAILABLE
                ))
        total += _bulk_units(block, units, user)
    print(f"    → {total} units, all AVAILABLE")


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 6 — Partial sales plot layout (all 4 statuses represented)
# ─────────────────────────────────────────────────────────────────────────────
def seed_scenario_6(user):
    print("\n[6] Golden Meadows Phase 2 — PLOTS with all status types")
    p, _ = _make_project(dict(
        name='Golden Meadows Phase 2',
        developer_name='Golden Developers',
        project_type='PLOTS',
        location='Patancheru, Hyderabad',
        city='Hyderabad',
        total_area='6 Acres',
        price_range_min=Decimal('1500000'),
        price_range_max=Decimal('4000000'),
        approval_type='DTCP',
        approval_number='DTCP/PTR/2024/881',
        status='ACTIVE',
        possession_date=date(2025, 9, 30),
        contact_person='Girish Reddy',
        contact_phone='9876001234',
        description='Phase 2 of the popular Golden Meadows layout.',
        amenities='Concrete Roads, Parks, Street Lights, Drainage, Security',
        is_active=True,
    ), user)

    block = _make_block(p, 'Phase 2 Main Block', 'All 48 plots', order=0, user=user)

    # Explicitly seed each status in equal proportions to test the grid filtering
    statuses_cycle = (
        ['AVAILABLE'] * 20 +
        ['BLOCKED']   * 8  +
        ['BOOKED']    * 14 +
        ['REGISTERED'] * 6
    )
    random.shuffle(statuses_cycle)

    units = []
    for i, st in enumerate(statuses_cycle, start=1):
        area_sqyd = Decimal(random.randint(120, 300))
        units.append(dict(
            unit_number=f'PLT-{i:03d}',
            unit_type='PLOT',
            area_sqyd=area_sqyd,
            area_sqft=round(area_sqyd * Decimal('9'), 2),
            facing=random.choice(FACINGS),
            price=area_sqyd * Decimal(random.randint(13000, 20000)),
            status=st,
            remarks='Corner plot — premium' if i % 8 == 0 else '',
        ))
    n = _bulk_units(block, units, user)
    avail = sum(1 for u in units if u['status'] == 'AVAILABLE')
    print(f"    → {n} plots  (20 available, 8 blocked, 14 booked, 6 registered)")


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 7 — Large high-rise  3 towers × 15 floors × 4 units = 180 units
# ─────────────────────────────────────────────────────────────────────────────
def seed_scenario_7(user):
    print("\n[7] Skyline Grand — large high-rise FLATS (ACTIVE)")
    p, _ = _make_project(dict(
        name='Skyline Grand',
        developer_name='Skyline Realty',
        project_type='FLATS',
        location='Financial District, Hyderabad',
        city='Hyderabad',
        total_area='4.5 Acres',
        price_range_min=Decimal('9000000'),
        price_range_max=Decimal('28000000'),
        approval_type='HMDA',
        approval_number='HMDA/2024/FD/3310',
        status='ACTIVE',
        possession_date=date(2027, 9, 30),
        contact_person='Anil Sharma',
        contact_phone='9900112233',
        description='Tallest residential complex in the financial district corridor.',
        amenities='Sky Lounge, 3 Swimming Pools, Yoga Deck, Co-working Space, Concierge, Valet',
        rera_number='P02400007743',
        is_active=True,
    ), user)

    tower_configs = [
        ('Tower North', 'North-facing premium block', 15, 'north'),
        ('Tower South', 'South-facing lake-view block', 15, 'south'),
        ('Tower East',  'Sunrise-facing block',        15, 'east'),
    ]
    total = 0
    for idx, (t_name, t_desc, floors, _) in enumerate(tower_configs):
        block = _make_block(p, t_name, t_desc, total_floors=floors, order=idx, user=user)
        units = []
        for floor in range(1, floors + 1):
            for pos in range(1, 5):
                ft = ['2BHK', '3BHK', '3BHK', '4BHK'][pos - 1]
                area = Decimal(random.randint(1150, 2400))
                units.append(dict(
                    unit_number=f'{floor:02d}{pos:02d}',
                    unit_type=ft,
                    floor=floor,
                    area_sqft=area,
                    carpet_area_sqft=round(area * Decimal('0.72'), 2),
                    facing=random.choice(FACINGS),
                    price=area * Decimal(random.randint(8500, 13000)),
                    status=_pick_status((0.35, 0.08, 0.40, 0.17)),
                ))
        total += _bulk_units(block, units, user)
    print(f"    → {total} units across 3 towers × 15 floors")


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 8 — Small plot layout (1 block, 20 plots, mostly available)
# ─────────────────────────────────────────────────────────────────────────────
def seed_scenario_8(user):
    print("\n[8] Silver Oak Plots — small layout, mostly AVAILABLE")
    p, _ = _make_project(dict(
        name='Silver Oak Plots',
        developer_name='Silver Oak Developers',
        project_type='PLOTS',
        location='Yadagirigutta, Telangana',
        city='Yadagirigutta',
        total_area='2 Acres',
        price_range_min=Decimal('900000'),
        price_range_max=Decimal('2500000'),
        approval_type='PANCHAYAT',
        status='ACTIVE',
        possession_date=date(2025, 3, 31),
        contact_person='Ravi Nair',
        contact_phone='9811223344',
        description='Affordable gated community plots near the Yadagirigutta temple town.',
        amenities='Security, Concrete Roads, Water, Electricity',
        is_active=True,
    ), user)

    block = _make_block(p, 'Main Layout', '20 premium plots', order=0, user=user)
    units = []
    for i in range(1, 21):
        area_sqyd = Decimal(random.randint(80, 200))
        # mostly available — only 3–4 sold
        st = 'AVAILABLE' if i > 4 else random.choice(['BOOKED', 'REGISTERED'])
        units.append(dict(
            unit_number=f'P-{i:02d}',
            unit_type='PLOT',
            area_sqyd=area_sqyd,
            area_sqft=round(area_sqyd * Decimal('9'), 2),
            facing=random.choice(FACINGS),
            price=area_sqyd * Decimal(random.randint(9000, 14000)),
            status=st,
        ))
    n = _bulk_units(block, units, user)
    print(f"    → {n} plots (mostly available)")


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 9 — Luxury villas / duplex (premium pricing, PENTHOUSE + DUPLEX types)
# ─────────────────────────────────────────────────────────────────────────────
def seed_scenario_9(user):
    print("\n[9] Royal Orchid Villas — luxury FLATS (penthouse + duplex)")
    p, _ = _make_project(dict(
        name='Royal Orchid Villas',
        developer_name='Royal Realty Group',
        project_type='FLATS',
        location='Jubilee Hills, Hyderabad',
        city='Hyderabad',
        total_area='2 Acres',
        price_range_min=Decimal('25000000'),
        price_range_max=Decimal('80000000'),
        approval_type='HMDA',
        approval_number='HMDA/2024/JH/5501',
        status='ACTIVE',
        possession_date=date(2027, 12, 31),
        contact_person='Priya Kapoor',
        contact_phone='9955443322',
        description='Ultra-luxury residences in the most prestigious address in Hyderabad.',
        amenities='Private Pool per Villa, Home Theatre, Concierge, Helipad, Spa, Wine Cellar',
        rera_number='P02400011234',
        is_active=True,
    ), user)

    # 2 wings — Wing A (standard luxury flats) and Wing B (penthouses + duplexes)
    configs = [
        ('Wing A', 'Luxury 3BHK & 4BHK', 8, [
            ('3BHK', 2400, 3200), ('4BHK', 3200, 4500),
            ('4BHK', 3200, 4500), ('STUDIO', 900, 1100),
        ]),
        ('Wing B', 'Penthouse & Duplex — sky-level', 6, [
            ('PENTHOUSE', 5000, 8000), ('DUPLEX', 4000, 6000),
            ('PENTHOUSE', 5000, 8000), ('DUPLEX', 4000, 6000),
        ]),
    ]

    total = 0
    for idx, (w_name, w_desc, floors, unit_configs) in enumerate(configs):
        block = _make_block(p, w_name, w_desc, total_floors=floors, order=idx, user=user)
        units = []
        for floor in range(1, floors + 1):
            for pos, (ft, area_min, area_max) in enumerate(unit_configs, start=1):
                area = Decimal(random.randint(area_min, area_max))
                ppm  = Decimal(random.randint(22000, 40000))
                units.append(dict(
                    unit_number=f'{floor:02d}{pos:02d}',
                    unit_type=ft,
                    floor=floor,
                    area_sqft=area,
                    carpet_area_sqft=round(area * Decimal('0.75'), 2),
                    facing=random.choice(FACINGS),
                    price=area * ppm,
                    status=_pick_status((0.50, 0.15, 0.25, 0.10)),
                    remarks='Premium corner unit' if pos == 1 else '',
                ))
        total += _bulk_units(block, units, user)
    print(f"    → {total} luxury units across 2 wings")


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 10 — Completed MIXED project — majority REGISTERED
# ─────────────────────────────────────────────────────────────────────────────
def seed_scenario_10(user):
    print("\n[10] Palm Springs Township — COMPLETED, majority REGISTERED")
    p, _ = _make_project(dict(
        name='Palm Springs Township',
        developer_name='Palm Springs Developers',
        project_type='MIXED',
        location='Miyapur, Hyderabad',
        city='Hyderabad',
        total_area='10 Acres',
        price_range_min=Decimal('1800000'),
        price_range_max=Decimal('12000000'),
        approval_type='HMDA',
        approval_number='HMDA/2022/MYP/0771',
        status='COMPLETED',
        possession_date=date(2024, 6, 30),
        contact_person='Dinesh Pillai',
        contact_phone='9944332211',
        description='Successfully completed township. Handover of most units done.',
        amenities='Clubhouse, Pool, Park, School, Supermarket, Temple',
        rera_number='P02400001122',
        is_active=True,
    ), user)

    # Block 1 — Apartment tower (completed, mostly registered)
    apt_block = _make_block(p, 'Palm Tower', 'G+10 apartment block', total_floors=10, order=0, user=user)
    apt_units = []
    for floor in range(1, 11):
        for pos in range(1, 5):
            area = Decimal(random.randint(1000, 1800))
            # 70% registered, 15% booked, 10% blocked, 5% still available
            st = random.choices(
                STATUSES, weights=[0.05, 0.10, 0.15, 0.70], k=1
            )[0]
            apt_units.append(dict(
                unit_number=f'{floor:02d}{pos:02d}',
                unit_type=random.choice(['2BHK', '3BHK']),
                floor=floor,
                area_sqft=area,
                carpet_area_sqft=round(area * Decimal('0.72'), 2),
                facing=random.choice(FACINGS),
                price=area * Decimal(random.randint(5000, 7500)),
                status=st,
            ))
    n1 = _bulk_units(apt_block, apt_units, user)

    # Block 2 — Villa plots (completed, mostly registered)
    villa_block = _make_block(p, 'Villa Zone', 'Premium villa plots', order=1, user=user)
    v_units = []
    for i in range(1, 26):
        area_sqyd = Decimal(random.randint(150, 350))
        st = random.choices(STATUSES, weights=[0.04, 0.06, 0.10, 0.80], k=1)[0]
        v_units.append(dict(
            unit_number=f'VZ-{i:03d}',
            unit_type='VILLA',
            area_sqyd=area_sqyd,
            area_sqft=round(area_sqyd * Decimal('9'), 2),
            facing=random.choice(FACINGS),
            price=area_sqyd * Decimal(random.randint(20000, 35000)),
            status=st,
        ))
    n2 = _bulk_units(villa_block, v_units, user)
    print(f"    → {n1} apartments + {n2} villa plots (majority REGISTERED)")


# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY + RUNNER
# ─────────────────────────────────────────────────────────────────────────────

def print_summary():
    from django.db.models import Count
    print(f"\n{'='*60}")
    print("  AVAILABILITY SEED — FINAL SUMMARY")
    print(f"{'='*60}")

    projects = AvailabilityProject.objects.filter(is_deleted=False)
    print(f"\n  Projects  : {projects.count()}")
    print(f"  Blocks    : {AvailabilityBlock.objects.filter(is_deleted=False).count()}")
    print(f"  Units     : {AvailabilityUnit.objects.filter(is_deleted=False).count()}")

    print(f"\n  {'Project':<35} {'Type':<8} {'Status':<12} {'Blks':>4} {'Units':>6} {'Avail':>6}")
    print(f"  {'-'*35} {'-'*8} {'-'*12} {'-'*4} {'-'*6} {'-'*6}")

    for proj in projects.order_by('name'):
        blocks = AvailabilityBlock.objects.filter(project=proj, is_deleted=False).count()
        units  = AvailabilityUnit.objects.filter(block__project=proj, is_deleted=False)
        total  = units.count()
        avail  = units.filter(status='AVAILABLE').count()
        print(f"  {proj.name:<35} {proj.project_type:<8} {proj.status:<12} {blocks:>4} {total:>6} {avail:>6}")

    print(f"\n  Unit status breakdown:")
    for st in ['AVAILABLE', 'BLOCKED', 'BOOKED', 'REGISTERED']:
        cnt = AvailabilityUnit.objects.filter(status=st, is_deleted=False).count()
        bar = '█' * min(cnt // 5, 40)
        print(f"    {st:<12} {cnt:>5}  {bar}")
    print()


def run():
    random.seed(42)   # reproducible run
    print(f"\n{'='*60}")
    print("  SEEDING AVAILABILITY LIST — 10 scenarios")
    print(f"{'='*60}")

    user = User.objects.filter(is_superuser=True).first() \
        or User.objects.filter(is_active=True).first()

    if not user:
        print("\n  ERROR: No active user found. Run seed_groups_users.py first.")
        return

    print(f"  Using user: {user.username}")

    seed_scenario_1(user)   # multi-tower FLATS, active
    seed_scenario_2(user)   # plot layout, active
    seed_scenario_3(user)   # mixed (tower + plots)
    seed_scenario_4(user)   # sold out (all registered)
    seed_scenario_5(user)   # upcoming (all available)
    seed_scenario_6(user)   # all 4 statuses present
    seed_scenario_7(user)   # large high-rise 3×15 floors
    seed_scenario_8(user)   # small layout, mostly available
    seed_scenario_9(user)   # luxury / penthouse / duplex
    seed_scenario_10(user)  # completed, majority registered

    print_summary()


if __name__ == '__main__' or True:
    run()
