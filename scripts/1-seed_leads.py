"""
Seed script: Create sample Leads and Follow-ups.

Usage:
    python manage.py shell < scripts/1-seed_leads.py

Assigns leads to users who have access (Sales Executive, Team Leader, Director).
Creates follow-ups for leads that have progressed in the pipeline.
"""
import django
import os
import sys
import random
from datetime import date, timedelta

if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BaseProject.settings')
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    django.setup()

from django.contrib.auth import get_user_model
from Lead.models import Lead, LeadFollowUp, LEAD_SOURCE_CHOICES, LEAD_STATUS_CHOICES

User = get_user_model()

# ============================================================================
# SAMPLE DATA — 60 unique customers
# ============================================================================

FIRST_NAMES = [
    'Venkat', 'Lakshmi', 'Suresh', 'Anitha', 'Ramesh', 'Padma', 'Naresh', 'Swathi',
    'Ganesh', 'Kavitha', 'Mahesh', 'Divya', 'Ravi', 'Sunitha', 'Srinivas', 'Meena',
    'Anil', 'Bhavani', 'Chandra', 'Deepika', 'Harish', 'Jyothi', 'Karthik', 'Lavanya',
    'Mohan', 'Nandini', 'Pavan', 'Radha', 'Sai', 'Uma', 'Vijay', 'Priya',
    'Rajesh', 'Sushma', 'Arvind', 'Pooja', 'Dinesh', 'Rekha', 'Satish', 'Anusha',
    'Prakash', 'Sindhu', 'Sudhir', 'Vasantha', 'Ashok', 'Geetha', 'Bhaskar', 'Nirmala',
    'Tarun', 'Shilpa', 'Manoj', 'Rani', 'Yogesh', 'Madhavi', 'Kishore', 'Savitha',
    'Srikanth', 'Aruna', 'Nagendra', 'Pallavi',
]

LAST_NAMES = [
    'Rao', 'Devi', 'Babu', 'Kumari', 'Reddy', 'Priya', 'Kumar', 'Sharma',
    'Prasad', 'Nair', 'Gupta', 'Joshi', 'Teja', 'Patel', 'Naidu', 'Verma',
    'Choudhary', 'Gowda', 'Shetty', 'Iyer', 'Pillai', 'Menon', 'Saxena', 'Mishra',
    'Singh', 'Agarwal', 'Kapoor', 'Das', 'Bhat', 'Hegde',
]

CUSTOMER_NAMES = [f"{FIRST_NAMES[i]} {LAST_NAMES[i % len(LAST_NAMES)]}" for i in range(60)]

MOBILES = [f'98{random.randint(10000000, 99999999)}' for _ in range(60)]
# Ensure unique
MOBILES = list(set(MOBILES))[:60]
while len(MOBILES) < 60:
    MOBILES.append(f'97{random.randint(10000000, 99999999)}')

BUDGETS = ['20-30 Lakhs', '30-40 Lakhs', '40-50 Lakhs', '50-60 Lakhs', '60-80 Lakhs', '80 Lakhs - 1 Cr', '1-1.5 Cr', '1.5-2 Cr', '2-3 Cr']

AREAS = [
    'Madhapur', 'Gachibowli', 'Kondapur', 'Kukatpally', 'Banjara Hills',
    'Jubilee Hills', 'Miyapur', 'Bachupally', 'Kompally', 'Shamshabad',
    'Patancheru', 'Nallagandla', 'Tellapur', 'Mokila', 'Narsingi',
]

PROPERTY_TYPES = [
    '2BHK Flat', '3BHK Flat', 'Plot 150 sq.yd', 'Plot 200 sq.yd',
    'Plot 250 sq.yd', 'Plot 300 sq.yd', 'Villa', '4BHK Flat', 'Duplex',
    'Penthouse', '3BHK Villa',
]

FOLLOW_UP_NOTES = [
    'Customer is interested, asked about payment plans.',
    'Discussed project details, will visit site this weekend.',
    'Not reachable, will try again tomorrow.',
    'Wants to bring family for site visit.',
    'Comparing with other projects, needs time.',
    'Budget confirmed, ready to proceed.',
    'Asked about loan assistance options.',
    'Requested project brochure via WhatsApp.',
    'Wants corner plot, checking availability.',
    'Happy with location, discussing pricing.',
    'Customer wants east-facing unit specifically.',
    'Negotiating on per sq.yd rate.',
    'Interested in EMI payment plan.',
    'Wants to visit again with parents.',
    'Confirmed budget, waiting for preferred plot.',
    'Asked about registration charges and timeline.',
    'Customer referred by existing buyer.',
    'Wants gated community with clubhouse.',
    'Inquired about possession timeline.',
    'Discussed road connectivity and metro access.',
]

SOURCES = [s[0] for s in LEAD_SOURCE_CHOICES]
STATUSES = [s[0] for s in LEAD_STATUS_CHOICES]
FOLLOWUP_TYPES = ['CALL', 'WHATSAPP', 'MEETING', 'SITE_VISIT']

# Status distribution — weighted to show realistic pipeline
STATUS_WEIGHTS = [0.12, 0.08, 0.10, 0.15, 0.12, 0.12, 0.10, 0.08, 0.05, 0.08]


def get_assignable_users():
    """Get users who can be assigned leads (Director, Team Leader, Sales Executive)."""
    users = User.objects.filter(
        is_active=True,
        is_superuser=False,
        groups__name__in=['Director', 'Team Leader', 'Sales Executive']
    ).distinct()
    if not users.exists():
        print("  WARNING: No assignable users found. Run seed_groups.py first!")
        return []
    return list(users)


def seed_leads():
    """Create 60 sample leads assigned to available users."""
    print(f"\n{'='*50}")
    print("  SEEDING LEADS (60 records)")
    print(f"{'='*50}\n")

    users = get_assignable_users()
    if not users:
        return

    print(f"  Assignable users: {', '.join(u.username for u in users)}")

    # Try to get projects for interested_project
    projects = []
    try:
        from Masters.models import Project
        projects = list(Project.objects.filter(is_deleted=False, is_active=True))
    except Exception:
        pass

    created_count = 0
    leads = []

    for i in range(60):
        name = CUSTOMER_NAMES[i]
        mobile = MOBILES[i]

        # Skip if lead already exists with this mobile
        existing = Lead.objects.filter(mobile=mobile).first()
        if existing:
            leads.append(existing)
            continue

        status = random.choices(STATUSES, weights=STATUS_WEIGHTS, k=1)[0]
        assigned_user = random.choice(users)
        project = random.choice(projects) if projects else None

        # Create date spread over last 90 days
        days_ago = random.randint(0, 90)

        lead = Lead.objects.create(
            name=name,
            mobile=mobile,
            alternate_number=f'91{random.randint(10000000, 99999999)}' if random.random() > 0.6 else None,
            email=f"{name.split()[0].lower()}{i}@gmail.com",
            budget=random.choice(BUDGETS),
            preferred_area=random.choice(AREAS),
            property_requirement=random.choice(PROPERTY_TYPES),
            lead_source=random.choice(SOURCES),
            assigned_employee=assigned_user,
            interested_project=project,
            status=status,
            remarks=f"Interested in {random.choice(PROPERTY_TYPES)} at {random.choice(AREAS)}.",
            created_by_type='User',
            created_by_identifier=str(assigned_user.id),
            modified_by_type='User',
            modified_by_identifier=str(assigned_user.id),
        )
        # Backdate created_on
        from django.utils import timezone
        Lead.objects.filter(pk=lead.pk).update(
            created_on=timezone.now() - timedelta(days=days_ago)
        )
        leads.append(lead)
        created_count += 1

    print(f"  Created {created_count} new leads (total: {len(leads)})")
    return leads


def seed_followups(leads):
    """Create follow-ups for leads that have progressed past NEW_LEAD."""
    print(f"\n{'='*50}")
    print("  SEEDING FOLLOW-UPS")
    print(f"{'='*50}\n")

    if not leads:
        print("  No leads to create follow-ups for.")
        return

    users = get_assignable_users()
    if not users:
        return

    created_count = 0
    today = date.today()

    for lead in leads:
        # Only create follow-ups for leads past NEW_LEAD
        if lead.status == 'NEW_LEAD':
            continue

        # Skip if follow-ups already exist
        if lead.follow_ups.exists():
            continue

        # Create 1-4 follow-ups per lead
        num_followups = random.randint(1, 4)
        for j in range(num_followups):
            days_ago = random.randint(1, 60)
            follow_up_date = today - timedelta(days=days_ago)
            next_date = follow_up_date + timedelta(days=random.randint(2, 7))

            LeadFollowUp.objects.create(
                lead=lead,
                follow_up_date=follow_up_date,
                follow_up_type=random.choice(FOLLOWUP_TYPES),
                discussion_notes=random.choice(FOLLOW_UP_NOTES),
                follow_up_time=None,
                next_follow_up_date=next_date if j < num_followups - 1 else None,
                created_by=random.choice(users),
                created_by_type='User',
                created_by_identifier=str(users[0].id),
                modified_by_type='User',
                modified_by_identifier=str(users[0].id),
            )
            created_count += 1

    print(f"  Created {created_count} follow-ups")


def run():
    leads = seed_leads()
    seed_followups(leads or [])

    print(f"\n{'='*50}")
    print("  SUMMARY")
    print(f"{'='*50}\n")
    print(f"  Total Leads:      {Lead.objects.filter(is_deleted=False).count()}")
    print(f"  Total Follow-ups: {LeadFollowUp.objects.count()}")
    print(f"  Lead statuses:")
    for status, label in LEAD_STATUS_CHOICES:
        count = Lead.objects.filter(status=status, is_deleted=False).count()
        if count > 0:
            print(f"    {label}: {count}")
    print()


if __name__ == '__main__' or True:
    run()
