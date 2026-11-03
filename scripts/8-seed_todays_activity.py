"""
Seed script: Today's activity — calls made by employees + new leads today.

Generates realistic "today" data so dashboards / reports / Today's Insights
have live numbers to show:
  - New leads created TODAY (spread across today's working hours)
  - Follow-ups logged TODAY
  - Call logs made TODAY by employees (outgoing / incoming / missed / rejected)
  - A few calls auto-matched to existing leads by phone number

Usage:
    python manage.py shell < scripts/8-seed_todays_activity.py
  OR:
    python manage.py shell -c "exec(open('scripts/8-seed_todays_activity.py').read())"

Safe to re-run — it ADDS fresh activity for the current day each time.
Pass counts via env vars to tune volume:
    SEED_NEW_LEADS=15 SEED_CALLS=40 python manage.py shell -c "exec(open('scripts/8-seed_todays_activity.py').read())"
"""
import django, os, sys, random
from datetime import datetime, timedelta, time

if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BaseProject.settings')
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model
from Lead.models import (
    Lead, LeadFollowUp, CallLog,
    LEAD_SOURCE_CHOICES, LEAD_STATUS_CHOICES, LEAD_BUCKET_CHOICES,
)

User = get_user_model()

# ── tunables (env overrides) ───────────────────────────────────────────────────
NEW_LEADS_TODAY = int(os.getenv('SEED_NEW_LEADS', '15'))
CALLS_TODAY     = int(os.getenv('SEED_CALLS', '45'))
FOLLOWUPS_TODAY = int(os.getenv('SEED_FOLLOWUPS', '20'))

# ── sample data ─────────────────────────────────────────────────────────────────
FIRST_NAMES = [
    'Aditya', 'Bhavya', 'Charan', 'Deepa', 'Eswar', 'Farida', 'Gopi', 'Hema',
    'Indra', 'Jaya', 'Kiran', 'Latha', 'Murali', 'Neela', 'Omkar', 'Pooja',
    'Qadir', 'Ramya', 'Sanjay', 'Tanvi', 'Uday', 'Varsha', 'Yash', 'Zoya',
    'Naveen', 'Sravya', 'Teja', 'Keerthi', 'Rohan', 'Nisha',
]
LAST_NAMES = [
    'Reddy', 'Rao', 'Sharma', 'Naidu', 'Kumar', 'Varma', 'Gupta', 'Shetty',
    'Nair', 'Patel', 'Choudhary', 'Das', 'Pillai', 'Menon', 'Verma', 'Hegde',
]

BUDGETS = ['30-40 Lakhs', '40-50 Lakhs', '50-60 Lakhs', '60-80 Lakhs',
           '80 Lakhs - 1 Cr', '1-1.5 Cr', '1.5-2 Cr']
AREAS = ['Madhapur', 'Gachibowli', 'Kondapur', 'Kukatpally', 'Miyapur',
         'Bachupally', 'Kompally', 'Narsingi', 'Tellapur', 'Mokila']
PROPERTY_TYPES = ['2BHK Flat', '3BHK Flat', 'Plot 150 sq.yd', 'Plot 200 sq.yd',
                  'Villa', '4BHK Flat', 'Duplex', '3BHK Villa']
FOLLOW_UP_NOTES = [
    'Spoke today, customer wants a site visit this weekend.',
    'Shared brochure on WhatsApp, awaiting response.',
    'Discussed pricing, customer negotiating.',
    'Customer asked about home loan assistance.',
    'Confirmed budget, looking for east-facing unit.',
    'Not reachable, will retry tomorrow.',
    'Interested, comparing with another project.',
    'Wants to bring family before deciding.',
    'Asked about possession timeline and amenities.',
    'Ready to book, finalising the unit.',
]

CALL_TYPES = ['outgoing', 'incoming', 'missed', 'rejected']
CALL_TYPE_WEIGHTS = [0.55, 0.25, 0.12, 0.08]  # mostly outgoing
SOURCES = [s[0] for s in LEAD_SOURCE_CHOICES]
STATUSES = [s[0] for s in LEAD_STATUS_CHOICES]
BUCKETS = [s[0] for s in LEAD_BUCKET_CHOICES]
FOLLOWUP_TYPES = ['CALL', 'WHATSAPP', 'MEETING', 'SITE_VISIT']


# ── helpers ───────────────────────────────────────────────────────────────────
def _today_datetime(hour_min=9, hour_max=19):
    """Return a timezone-aware datetime set to a random time earlier TODAY."""
    now = timezone.localtime()
    hour = random.randint(hour_min, min(hour_max, max(hour_min, now.hour)))
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    naive = datetime.combine(now.date(), time(hour, minute, second))
    aware = timezone.make_aware(naive, timezone.get_current_timezone())
    # never return a future time
    return min(aware, now)


def _unique_mobile():
    for _ in range(50):
        m = f'9{random.randint(100000000, 999999999)}'
        if not Lead.objects.filter(mobile=m).exists():
            return m
    return f'9{random.randint(100000000, 999999999)}'


def get_sales_users():
    users = list(User.objects.filter(
        is_active=True, is_superuser=False,
        groups__name__in=['Director', 'Team Leader', 'Sales Executive'],
    ).distinct())
    if not users:
        # fall back to any active user
        users = list(User.objects.filter(is_active=True)[:5])
    return users


# ── 1. New leads created today ──────────────────────────────────────────────────
def seed_new_leads_today(users):
    print(f"\n{'='*52}")
    print(f"  NEW LEADS TODAY  ({NEW_LEADS_TODAY})")
    print(f"{'='*52}")

    projects = []
    try:
        from ProjectManagement.models import Project
        projects = list(Project.objects.filter(is_deleted=False, is_active=True))
    except Exception:
        pass

    created = []
    for i in range(NEW_LEADS_TODAY):
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        mobile = _unique_mobile()
        user = random.choice(users)
        created_dt = _today_datetime()

        lead = Lead.objects.create(
            name=name,
            mobile=mobile,
            alternate_number=(f'8{random.randint(100000000, 999999999)}'
                              if random.random() > 0.6 else None),
            email=f"{name.split()[0].lower()}{random.randint(1,9999)}@gmail.com",
            budget=random.choice(BUDGETS),
            preferred_area=random.choice(AREAS),
            property_requirement=random.choice(PROPERTY_TYPES),
            lead_source=random.choice(SOURCES),
            assigned_employee=user,
            interested_project=random.choice(projects) if projects else None,
            status='ONGOING',
            bucket=random.choice(['NEW_LEAD', 'NEW_LEAD', 'HOT_LEAD']),  # mostly new
            remarks=f"Fresh enquiry today for {random.choice(PROPERTY_TYPES)} at {random.choice(AREAS)}.",
            created_by_type='User', created_by_identifier=str(user.id),
            modified_by_type='User', modified_by_identifier=str(user.id),
        )
        # Force created_on to TODAY (auto_now_add would already be today, but we set a specific time)
        Lead.objects.filter(pk=lead.pk).update(created_on=created_dt, modified_on=created_dt)
        created.append(lead)

    print(f"  → Created {len(created)} leads dated today")
    return created


# ── 2. Follow-ups logged today ───────────────────────────────────────────────────
def seed_followups_today(users, todays_leads):
    print(f"\n{'='*52}")
    print(f"  FOLLOW-UPS TODAY  ({FOLLOWUPS_TODAY})")
    print(f"{'='*52}")

    # mix today's new leads + some existing active leads
    pool = list(todays_leads)
    existing = list(Lead.objects.filter(status__in=['ONGOING', 'LIVE'], is_deleted=False)
                    .exclude(pk__in=[l.pk for l in todays_leads])[:50])
    pool += existing
    if not pool:
        print("  No leads available for follow-ups.")
        return

    today = timezone.localdate()
    created = 0
    for _ in range(FOLLOWUPS_TODAY):
        lead = random.choice(pool)
        user = lead.assigned_employee or random.choice(users)
        fu = LeadFollowUp.objects.create(
            lead=lead,
            follow_up_date=today,
            follow_up_type=random.choice(FOLLOWUP_TYPES),
            discussion_notes=random.choice(FOLLOW_UP_NOTES),
            follow_up_time=_today_datetime().time(),
            next_follow_up_date=today + timedelta(days=random.randint(1, 7)),
            created_by=user,
            created_by_type='User', created_by_identifier=str(user.id),
            modified_by_type='User', modified_by_identifier=str(user.id),
        )
        LeadFollowUp.objects.filter(pk=fu.pk).update(
            created_on=_today_datetime(), modified_on=_today_datetime()
        )
        created += 1
    print(f"  → Created {created} follow-ups dated today")


# ── 3. Call logs made today ───────────────────────────────────────────────────
def seed_calls_today(users):
    print(f"\n{'='*52}")
    print(f"  CALL LOGS TODAY  ({CALLS_TODAY})")
    print(f"{'='*52}")

    # Pull some real lead phone numbers so a portion of calls auto-match
    lead_phones = list(
        Lead.objects.filter(is_deleted=False)
        .exclude(mobile__isnull=True)
        .values_list('mobile', 'id')[:80]
    )

    created = 0
    matched = 0
    for _ in range(CALLS_TODAY):
        user = random.choice(users)
        call_type = random.choices(CALL_TYPES, weights=CALL_TYPE_WEIGHTS, k=1)[0]
        called_at = _today_datetime()

        # ~60% of calls are to existing leads (auto-match), rest are new numbers
        lead_obj = None
        if lead_phones and random.random() < 0.6:
            phone, lead_id = random.choice(lead_phones)
            lead_obj = Lead.objects.filter(pk=lead_id).first()
            phone_number = phone
            matched += 1
        else:
            phone_number = f'7{random.randint(100000000, 999999999)}'

        # duration: 0 for missed/rejected, else realistic
        if call_type in ('missed', 'rejected'):
            duration = 0
        else:
            duration = random.randint(15, 600)  # 15s to 10 min

        CallLog.objects.create(
            phone_number=phone_number,
            call_type=call_type,
            duration_secs=duration,
            called_at=called_at,
            device_platform='android',
            called_by=user,
            lead=lead_obj,
            call_count=1,
            call_times=[called_at.isoformat()],
        )
        created += 1

    print(f"  → Created {created} call logs today ({matched} matched to existing leads)")


# ── summary ───────────────────────────────────────────────────────────────────
def print_summary():
    today = timezone.localdate()
    start = timezone.make_aware(datetime.combine(today, time.min), timezone.get_current_timezone())
    end = timezone.make_aware(datetime.combine(today, time.max), timezone.get_current_timezone())

    leads_today = Lead.objects.filter(created_on__range=(start, end), is_deleted=False).count()
    calls_today = CallLog.objects.filter(called_at__range=(start, end)).count()
    fu_today = LeadFollowUp.objects.filter(follow_up_date=today).count()

    print(f"\n{'='*52}")
    print(f"  TODAY'S ACTIVITY SUMMARY  ({today})")
    print(f"{'='*52}")
    print(f"  New leads today      : {leads_today}")
    print(f"  Follow-ups today     : {fu_today}")
    print(f"  Calls made today     : {calls_today}")

    print(f"\n  Calls by type (today):")
    for ct in CALL_TYPES:
        cnt = CallLog.objects.filter(called_at__range=(start, end), call_type=ct).count()
        print(f"    {ct:<10} {cnt}")

    print(f"\n  Calls by employee (today):")
    from django.db.models import Count
    rows = (CallLog.objects.filter(called_at__range=(start, end))
            .values('called_by__username')
            .annotate(c=Count('id')).order_by('-c'))
    for r in rows:
        print(f"    {str(r['called_by__username']):<20} {r['c']}")
    print()


def run():
    random.seed()  # fresh randomness each run (today's data varies)
    print(f"\n{'#'*52}")
    print(f"#  SEEDING TODAY'S ACTIVITY")
    print(f"{'#'*52}")

    users = get_sales_users()
    if not users:
        print("\n  ERROR: No users found. Run 0-seed_groups_users.py first.")
        return
    print(f"  Employees: {', '.join(u.username for u in users)}")

    todays_leads = seed_new_leads_today(users)
    seed_followups_today(users, todays_leads)
    seed_calls_today(users)
    print_summary()


if __name__ == '__main__' or True:
    run()
