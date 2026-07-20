"""
Seed script: Create sample Site Visits.

Usage:
    python manage.py shell < scripts/seed_sitevisits.py

Creates site visits linked to existing leads and projects.
Requires: seed_leads.py and seed_projects.py to be run first.
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
]


def seed_sitevisits():
    """Create sample site visits."""
    print(f"\n{'='*50}")
    print("  SEEDING SITE VISITS")
    print(f"{'='*50}\n")

    # Get assignable users
    users = list(User.objects.filter(
        is_active=True, is_superuser=False,
        groups__name__in=['Director', 'Team Leader', 'Sales Executive']
    ).distinct())

    if not users:
        print("  No assignable users found. Run seed_groups_users.py first.")
        return

    # Get leads
    leads = list(Lead.objects.filter(is_deleted=False).order_by('?')[:20])
    if not leads:
        print("  No leads found. Run seed_leads.py first.")
        return

    # Get projects
    projects = list(Project.objects.filter(is_deleted=False, is_active=True))
    if not projects:
        print("  No projects found. Run seed_projects.py first.")
        return

    # Check existing
    existing_count = SiteVisit.objects.filter(is_deleted=False).count()
    if existing_count >= 15:
        print(f"  Already have {existing_count} site visits. Skipping.")
        return

    today = date.today()
    created_count = 0

    for lead in leads:
        # 60% chance of having a site visit
        if random.random() > 0.6:
            continue

        project = random.choice(projects)
        assigned = random.choice(users)
        days_ago = random.randint(0, 45)
        visit_date = today - timedelta(days=days_ago)

        # Weight status based on how old the visit is
        if days_ago > 20:
            status = random.choices(
                ['COMPLETED', 'CANCELLED'], weights=[0.8, 0.2], k=1
            )[0]
        elif days_ago > 7:
            status = random.choices(
                ['COMPLETED', 'CONFIRMED', 'CANCELLED'], weights=[0.5, 0.3, 0.2], k=1
            )[0]
        else:
            status = random.choices(
                ['SCHEDULED', 'CONFIRMED', 'COMPLETED'], weights=[0.4, 0.4, 0.2], k=1
            )[0]

        # Completion details only for completed visits
        feedback = random.choice(FEEDBACK_SAMPLES) if status == 'COMPLETED' else ''
        remarks = random.choice(REMARKS_SAMPLES) if status == 'COMPLETED' else ''

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
        print(f"  Created: {lead.name} → {project.name} ({visit_date}, {status})")

    print(f"\n  Total created: {created_count}")


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
