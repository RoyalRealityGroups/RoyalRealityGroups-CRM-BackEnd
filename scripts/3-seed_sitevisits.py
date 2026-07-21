"""
Seed script: Create 55+ sample Site Visits.

Usage:
    python manage.py shell < scripts/3-seed_sitevisits.py

Creates site visits linked to existing leads and projects.
Requires: 1-seed_leads.py and 2-seed_projects.py to be run first.
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
from Lead.models import Lead
from Masters.models import Project
from SiteVisit.models import SiteVisit, SITE_VISIT_STATUS_CHOICES

User = get_user_model()

STATUSES = [s[0] for s in SITE_VISIT_STATUS_CHOICES]

FEEDBACK_SAMPLES = [
    'Customer liked the location and amenities.',
    'Impressed with the road connectivity.',
    'Wanted more options in east-facing plots.',
    'Happy with the pricing, will discuss with family.',
    'Requested another visit with spouse next week.',
    'Very positive response, likely to book soon.',
    'Customer compared with competitor project nearby.',
    'Liked the gated community concept.',
    'Concerned about water supply, team clarified.',
    'Loved the greenery and park area.',
    'Wants to check Vastu compliance for the plot.',
    'Impressed with the clubhouse amenities.',
    'Asking about school and hospital proximity.',
    'Liked the wide roads and open spaces.',
    'Interested in corner unit specifically.',
    'Discussed payment plan options in detail.',
    'Customer wants to bring builder friend for inspection.',
    'Very satisfied with construction quality.',
    'Wants higher floor, checking availability.',
    'Comparing rates with neighboring projects.',
]

REMARKS_SAMPLES = [
    'Follow up in 2 days.',
    'High potential buyer.',
    'Needs loan assistance.',
    'Budget constraint, offered payment plan.',
    'Referred by existing customer.',
    'Second visit completed.',
    'Wants to finalize this weekend.',
    'Competitor offering lower rate, negotiate.',
    'Ready to book if corner plot available.',
    'Will bring family for final decision.',
    'Hot lead — close within this week.',
    'Needs time to arrange finances.',
    'Interested in 2 plots for investment.',
    'NRI customer, limited time window.',
    'Wants possession within 6 months.',
]


def seed_sitevisits():
    """Create 55+ sample site visits."""
    print(f"\n{'='*50}")
    print("  SEEDING SITE VISITS (55+ records)")
    print(f"{'='*50}\n")

    # Get assignable users
    users = list(User.objects.filter(
        is_active=True, is_superuser=False,
        groups__name__in=['Director', 'Team Leader', 'Sales Executive']
    ).distinct())

    if not users:
        print("  No assignable users found. Run 0-seed_groups_users.py first.")
        return

    # Get leads
    leads = list(Lead.objects.filter(is_deleted=False))
    if not leads:
        print("  No leads found. Run 1-seed_leads.py first.")
        return

    # Get projects
    projects = list(Project.objects.filter(is_deleted=False, is_active=True))
    if not projects:
        print("  No projects found. Run 2-seed_projects.py first.")
        return

    today = date.today()
    created_count = 0
    target_count = 55

    # Use all leads, some get multiple visits
    visit_leads = leads.copy()
    # Add some repeat visits
    repeat_leads = random.sample(leads, min(15, len(leads)))
    visit_leads.extend(repeat_leads)
    random.shuffle(visit_leads)

    for lead in visit_leads[:target_count]:
        project = random.choice(projects)
        assigned = random.choice(users)
        days_ago = random.randint(0, 75)
        visit_date = today - timedelta(days=days_ago)

        # Weight status based on how old the visit is
        if days_ago > 30:
            status = random.choices(
                ['COMPLETED', 'CANCELLED'], weights=[0.85, 0.15], k=1
            )[0]
        elif days_ago > 14:
            status = random.choices(
                ['COMPLETED', 'CONFIRMED', 'CANCELLED'], weights=[0.5, 0.3, 0.2], k=1
            )[0]
        elif days_ago > 3:
            status = random.choices(
                ['SCHEDULED', 'CONFIRMED', 'COMPLETED'], weights=[0.3, 0.4, 0.3], k=1
            )[0]
        else:
            status = random.choices(
                ['SCHEDULED', 'CONFIRMED'], weights=[0.6, 0.4], k=1
            )[0]

        # Completion details only for completed visits
        feedback = random.choice(FEEDBACK_SAMPLES) if status == 'COMPLETED' else ''
        remarks = random.choice(REMARKS_SAMPLES) if status in ['COMPLETED', 'CONFIRMED'] else ''

        sv = SiteVisit.objects.create(
            lead=lead,
            customer_name=lead.name,
            project=project,
            project_name=project.name,
            visit_date=visit_date,
            assigned_employee=assigned,
            status=status,
            customer_feedback=feedback,
            remarks=remarks,
            created_by_type='User',
            created_by_identifier=str(assigned.id),
            modified_by_type='User',
            modified_by_identifier=str(assigned.id),
        )
        created_count += 1

    print(f"  Created {created_count} site visits")


def run():
    seed_sitevisits()

    print(f"\n{'='*50}")
    print("  SUMMARY")
    print(f"{'='*50}\n")
    total = SiteVisit.objects.filter(is_deleted=False).count()
    print(f"  Total Site Visits: {total}")
    for status, label in SITE_VISIT_STATUS_CHOICES:
        count = SiteVisit.objects.filter(status=status, is_deleted=False).count()
        if count > 0:
            print(f"    {label}: {count}")
    print()


if __name__ == '__main__' or True:
    run()
