"""
Seed script: Create default groups (roles) and sample users.

Usage:
    python manage.py shell < scripts/seed_groups.py

Or from Django shell:
    exec(open('scripts/seed_groups.py').read())

Creates:
    Groups: Director, Team Leader, Sales Executive, Viewer
    Users:  One user per group with default password 'Pass@123'
"""
import django
import os
import sys

# Setup Django if running standalone
if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BaseProject.settings')
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    django.setup()

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

User = get_user_model()

DEFAULT_PASSWORD = 'Pass@123'


# ============================================================================
# GROUP DEFINITIONS
# ============================================================================

GROUPS = {
    'Director': {
        'description': 'Full access to all modules — highest level',
        'apps': [
            'Lead', 'SiteVisit', 'Inventory', 'Booking', 'Masters',
            'Users', 'RealEstateReports', 'Documents', 'dashboards',
            'General', 'Core_Users', 'Core_System', 'Core_Reports',
        ],
        'full_access': True,
    },
    'Team Leader': {
        'description': 'Full access except User & Permission Management',
        'apps': [
            'Lead', 'SiteVisit', 'Inventory', 'Booking', 'Masters',
            'RealEstateReports', 'Documents', 'dashboards', 'General',
        ],
        'full_access': True,
    },
    'Sales Executive': {
        'description': 'Lead, Site Visit, Booking — operational role',
        'apps': [
            'Lead', 'SiteVisit', 'Booking',
        ],
        'extra_view': ['Inventory', 'Masters', 'dashboards'],
    },
    'Viewer': {
        'description': 'Read-only access to all screens',
        'apps': [
            'Lead', 'SiteVisit', 'Inventory', 'Booking', 'Masters',
            'RealEstateReports', 'Documents', 'dashboards',
        ],
        'view_only': True,
    },
}


# ============================================================================
# USER DEFINITIONS
# ============================================================================

USERS = [
    {
        'username': 'director',
        'first_name': 'Rajesh',
        'last_name': 'Kumar',
        'email': 'director@rrgms.com',
        'phone': '9876543210',
        'designation': 'Director',
        'group': 'Director',
        'is_staff': True,
    },
    {
        'username': 'teamlead',
        'first_name': 'Priya',
        'last_name': 'Sharma',
        'email': 'teamlead@rrgms.com',
        'phone': '9876543211',
        'designation': 'Team Leader',
        'group': 'Team Leader',
        'reporting_manager': 'director',
    },
    {
        'username': 'executive1',
        'first_name': 'Arun',
        'last_name': 'Patel',
        'email': 'arun@rrgms.com',
        'phone': '9876543212',
        'designation': 'Sales Executive',
        'group': 'Sales Executive',
        'reporting_manager': 'teamlead',
    },
    {
        'username': 'executive2',
        'first_name': 'Sneha',
        'last_name': 'Reddy',
        'email': 'sneha@rrgms.com',
        'phone': '9876543213',
        'designation': 'Sales Executive',
        'group': 'Sales Executive',
        'reporting_manager': 'teamlead',
    },
    {
        'username': 'viewer',
        'first_name': 'Kiran',
        'last_name': 'Rao',
        'email': 'viewer@rrgms.com',
        'phone': '9876543214',
        'designation': 'Analyst',
        'group': 'Viewer',
        'reporting_manager': 'director',
    },
]


# ============================================================================
# SEED FUNCTIONS
# ============================================================================

def get_permissions_for_apps(app_labels):
    """Get visible permissions for given app labels (only those shown in UI)."""
    cts = ContentType.objects.filter(app_label__in=app_labels)
    # Only include permissions that have PermissionDetail with hide=False
    # These are the ones visible in the Group Edit UI toggles
    from Core.Users.models import PermissionDetail
    visible_perm_ids = PermissionDetail.objects.filter(hide=False).values_list('permission_id', flat=True)
    return Permission.objects.filter(content_type__in=cts, id__in=visible_perm_ids)


def seed_groups():
    """Create groups and assign permissions."""
    print("\n{'='*50}")
    print("  SEEDING GROUPS")
    print(f"{'='*50}\n")

    for group_name, config in GROUPS.items():
        group, created = Group.objects.get_or_create(name=group_name)
        action = 'Created' if created else 'Updated'

        # Clear existing permissions
        group.permissions.clear()

        app_labels = [app.lower() for app in config['apps']]
        extra_view_apps = [app.lower() for app in config.get('extra_view', [])]

        if config.get('full_access'):
            perms = get_permissions_for_apps(app_labels)
            group.permissions.add(*perms)
            print(f"  {action}: {group_name} ({perms.count()} permissions, full access)")

        elif config.get('view_only'):
            perms = get_permissions_for_apps(app_labels).filter(codename__startswith='view_')
            group.permissions.add(*perms)
            print(f"  {action}: {group_name} ({perms.count()} permissions, view only)")

        else:
            perms = get_permissions_for_apps(app_labels)
            group.permissions.add(*perms)
            count = perms.count()
            if extra_view_apps:
                view_perms = get_permissions_for_apps(extra_view_apps).filter(codename__startswith='view_')
                group.permissions.add(*view_perms)
                count += view_perms.count()
            print(f"  {action}: {group_name} ({count} permissions)")

    print()


def seed_users():
    """Create sample users and assign to groups."""
    print(f"{'='*50}")
    print("  SEEDING USERS")
    print(f"{'='*50}\n")
    print(f"  Default password: {DEFAULT_PASSWORD}\n")

    created_users = {}

    for user_data in USERS:
        username = user_data['username']
        group_name = user_data.pop('group')
        reporting_manager_username = user_data.pop('reporting_manager', None)

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': user_data.get('first_name', ''),
                'last_name': user_data.get('last_name', ''),
                'email': user_data.get('email', ''),
                'phone': user_data.get('phone', ''),
                'designation': user_data.get('designation', ''),
                'is_staff': user_data.get('is_staff', False),
                'is_active': True,
                'must_reset_password': False,
                'user_status': 'ACTIVE',
                'lead_data_scope': 'ALL' if group_name == 'Director' else 'TEAM' if group_name == 'Team Leader' else 'OWN',
                'followup_data_scope': 'ALL' if group_name == 'Director' else 'TEAM' if group_name == 'Team Leader' else 'OWN',
                'sitevisit_data_scope': 'ALL' if group_name == 'Director' else 'TEAM' if group_name == 'Team Leader' else 'OWN',
                'booking_data_scope': 'ALL' if group_name == 'Director' else 'TEAM' if group_name == 'Team Leader' else 'OWN',
            }
        )

        if created:
            user.set_password(DEFAULT_PASSWORD)
            user.save()

        # Assign group
        group = Group.objects.get(name=group_name)
        user.groups.clear()
        user.groups.add(group)

        created_users[username] = user
        action = 'Created' if created else 'Exists'
        print(f"  {action}: {username} ({user.first_name} {user.last_name}) -> Group: {group_name}")

    # Set reporting managers (second pass)
    print("\n  Setting reporting hierarchy...")
    for user_data_orig in USERS:
        username = user_data_orig['username']
        rm_username = user_data_orig.get('reporting_manager')
        if rm_username and rm_username in created_users:
            user = created_users[username]
            user.reporting_manager = created_users[rm_username]
            user.save(update_fields=['reporting_manager'])
            print(f"    {username} reports to {rm_username}")

    print()


def run():
    """Run all seed functions."""
    seed_groups()
    seed_users()

    print(f"{'='*50}")
    print("  SUMMARY")
    print(f"{'='*50}\n")
    print(f"  Groups: {Group.objects.count()}")
    print(f"  Users:  {User.objects.filter(is_superuser=False).count()}")
    print(f"\n  Login with any user using password: {DEFAULT_PASSWORD}")
    print(f"  Usernames: {', '.join(u['username'] for u in USERS)}")
    print()


if __name__ == '__main__' or True:
    run()
