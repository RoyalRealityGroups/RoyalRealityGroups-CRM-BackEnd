"""
Seed script: Create sample Projects.

Usage:
    python manage.py shell < scripts/seed_projects.py

Creates 8 sample real estate projects (mix of Plot, Flat, Villa, Mixed).
"""
import django
import os
import sys

if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BaseProject.settings')
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    django.setup()

from django.contrib.auth import get_user_model
from Masters.models import Project

User = get_user_model()

# ============================================================================
# SAMPLE PROJECTS
# ============================================================================

PROJECTS = [
    {
        'name': 'Green Valley Layout',
        'developer_name': 'RR Group',
        'project_type': 'PLOT',
        'location': 'Shamshabad, Hyderabad',
        'approval_type': 'HMDA',
        'status': 'ACTIVE',
    },
    {
        'name': 'Sunrise Heights',
        'developer_name': 'RR Group',
        'project_type': 'FLAT',
        'location': 'Gachibowli, Hyderabad',
        'approval_type': 'HMDA',
        'status': 'ACTIVE',
    },
    {
        'name': 'Royal Orchid Villas',
        'developer_name': 'RR Group',
        'project_type': 'VILLA',
        'location': 'Kompally, Hyderabad',
        'approval_type': 'HMDA',
        'status': 'ACTIVE',
    },
    {
        'name': 'Lake View Enclave',
        'developer_name': 'RR Group',
        'project_type': 'PLOT',
        'location': 'Bachupally, Hyderabad',
        'approval_type': 'DTCP',
        'status': 'ACTIVE',
    },
    {
        'name': 'Sky Tower Residency',
        'developer_name': 'RR Group',
        'project_type': 'FLAT',
        'location': 'Madhapur, Hyderabad',
        'approval_type': 'HMDA',
        'status': 'UPCOMING',
    },
    {
        'name': 'Palm Springs Township',
        'developer_name': 'RR Group',
        'project_type': 'MIXED',
        'location': 'Miyapur, Hyderabad',
        'approval_type': 'HMDA',
        'status': 'UPCOMING',
    },
    {
        'name': 'Golden Meadows Phase 1',
        'developer_name': 'RR Group',
        'project_type': 'PLOT',
        'location': 'Patancheru, Hyderabad',
        'approval_type': 'DTCP',
        'status': 'COMPLETED',
    },
    {
        'name': 'Heritage Towers',
        'developer_name': 'RR Group',
        'project_type': 'FLAT',
        'location': 'Kukatpally, Hyderabad',
        'approval_type': 'HMDA',
        'status': 'SOLD_OUT',
    },
]


def seed_projects():
    """Create sample projects."""
    print(f"\n{'='*50}")
    print("  SEEDING PROJECTS")
    print(f"{'='*50}\n")

    # Get a user for audit fields
    user = User.objects.filter(is_active=True).first()
    user_id = str(user.id) if user else ''

    created_count = 0

    for proj_data in PROJECTS:
        name = proj_data['name']

        # Skip if already exists
        if Project.objects.filter(name=name, is_deleted=False).exists():
            print(f"  Exists: {name}")
            continue

        Project.objects.create(
            name=proj_data['name'],
            developer_name=proj_data['developer_name'],
            project_type=proj_data['project_type'],
            location=proj_data['location'],
            approval_type=proj_data['approval_type'],
            status=proj_data['status'],
            is_active=True,
            created_by_type='User',
            created_by_identifier=user_id,
            modified_by_type='User',
            modified_by_identifier=user_id,
        )
        created_count += 1
        print(f"  Created: {name} ({proj_data['project_type']}, {proj_data['status']})")

    print(f"\n  Total created: {created_count}")
    print(f"  Total projects: {Project.objects.filter(is_deleted=False).count()}")
    print()


if __name__ == '__main__' or True:
    seed_projects()
