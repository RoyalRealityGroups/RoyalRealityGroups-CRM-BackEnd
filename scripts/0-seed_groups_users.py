"""
Seed script: Create default groups (roles) and sample users.

Usage:
    python manage.py shell < scripts/seed_groups.py

Or from Django shell:
    exec(open('scripts/seed_groups.py').read())

Creates:
    Groups: Director, Team Leader, Sales Executive, Viewer
    Users:  One user per group with default password 'Pass@123'
    UserPermissions: Menu-based permissions for each user
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
# GROUP DEFINITIONS (Legacy Django permissions)
# ============================================================================

GROUPS = {
    'Director': {
        'description': 'Full access to all modules — highest level',
        'apps': [
            'Lead', 'SiteVisit', 'Inventory', 'Booking', 'ProjectManagement',
            'Users', 'RealEstateReports', 'Documents', 'dashboards',
            'General', 'Core_Users', 'Core_System', 'Core_Reports', 'Availability',
        ],
        'full_access': True,
    },
    'Team Leader': {
        'description': 'Full access except User & Permission Management',
        'apps': [
            'Lead', 'SiteVisit', 'Inventory', 'Booking', 'ProjectManagement',
            'RealEstateReports', 'Documents', 'dashboards', 'General', 'Availability',
        ],
        'full_access': True,
    },
    'Sales Executive': {
        'description': 'Lead, Site Visit, Booking — operational role',
        'apps': [
            'Lead', 'SiteVisit', 'Booking',
        ],
        'extra_view': ['Inventory', 'ProjectManagement', 'dashboards', 'Availability'],
    },
    'Viewer': {
        'description': 'Read-only access to all screens',
        'apps': [
            'Lead', 'SiteVisit', 'Inventory', 'Booking', 'ProjectManagement',
            'RealEstateReports', 'Documents', 'dashboards', 'Availability',
        ],
        'view_only': True,
    },
}


# ============================================================================
# MENUITEM-BASED PERMISSIONS (New system)
# Maps group name to list of menuitem codes with their permissions
# ============================================================================

MENUITEM_PERMISSIONS = {
    'Director': {
        # Full access to all menuitems
        '_all_': {'can_view': True, 'can_add': True, 'can_edit': True, 'can_delete': True, 'can_export': True},
    },
    'Team Leader': {
        # Full access except user management
        '_all_except_': ['USER_PERMISSION'],
        '_default_': {'can_view': True, 'can_add': True, 'can_edit': True, 'can_delete': True, 'can_export': True},
    },
    'Sales Executive': {
        # Specific screens with full access
        'LEAD': {'can_view': True, 'can_add': True, 'can_edit': True, 'can_delete': False, 'can_export': False},
        'FOLLOWUP': {'can_view': True, 'can_add': True, 'can_edit': True, 'can_delete': False, 'can_export': False},
        'SITE_VISIT': {'can_view': True, 'can_add': True, 'can_edit': True, 'can_delete': False, 'can_export': False},
        'BOOKING': {'can_view': True, 'can_add': True, 'can_edit': True, 'can_delete': False, 'can_export': False},
        # View only
        'INVENTORY': {'can_view': True, 'can_add': False, 'can_edit': False, 'can_delete': False, 'can_export': False},
        'PROJECT': {'can_view': True, 'can_add': False, 'can_edit': False, 'can_delete': False, 'can_export': False},
        'DASHBOARD': {'can_view': True, 'can_add': False, 'can_edit': False, 'can_delete': False, 'can_export': False},
    },
    'Viewer': {
        # View-only access to all
        '_all_': {'can_view': True, 'can_add': False, 'can_edit': False, 'can_delete': False, 'can_export': False, 'is_view_only': True},
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


def seed_user_menu_permissions(user, group_name):
    """Create UserPermission records based on menuitem-based permission config."""
    from Users.models import UserPermission
    from Core.System.models import Menuitem
    
    config = MENUITEM_PERMISSIONS.get(group_name, {})
    if not config:
        return 0
    
    all_menuitems = Menuitem.objects.filter(is_deleted=False)
    count = 0
    
    # Handle '_all_' - full access to all menuitems
    if '_all_' in config:
        perms = config['_all_']
        for menuitem in all_menuitems:
            UserPermission.objects.update_or_create(
                user=user,
                menuitem=menuitem,
                defaults={
                    'can_view': perms.get('can_view', False),
                    'can_add': perms.get('can_add', False),
                    'can_edit': perms.get('can_edit', False),
                    'can_delete': perms.get('can_delete', False),
                    'can_export': perms.get('can_export', False),
                    'is_view_only': perms.get('is_view_only', False),
                }
            )
            count += 1
    
    # Handle '_all_except_' - full access except certain codes
    elif '_all_except_' in config:
        exclude_codes = config['_all_except_']
        default_perms = config.get('_default_', {})
        for menuitem in all_menuitems:
            if menuitem.code not in exclude_codes:
                UserPermission.objects.update_or_create(
                    user=user,
                    menuitem=menuitem,
                    defaults={
                        'can_view': default_perms.get('can_view', False),
                        'can_add': default_perms.get('can_add', False),
                        'can_edit': default_perms.get('can_edit', False),
                        'can_delete': default_perms.get('can_delete', False),
                        'can_export': default_perms.get('can_export', False),
                        'is_view_only': default_perms.get('is_view_only', False),
                    }
                )
                count += 1
    
    # Handle specific menuitem codes
    else:
        for code, perms in config.items():
            if code.startswith('_'):
                continue
            menuitem = all_menuitems.filter(code=code).first()
            if menuitem:
                UserPermission.objects.update_or_create(
                    user=user,
                    menuitem=menuitem,
                    defaults={
                        'can_view': perms.get('can_view', False),
                        'can_add': perms.get('can_add', False),
                        'can_edit': perms.get('can_edit', False),
                        'can_delete': perms.get('can_delete', False),
                        'can_export': perms.get('can_export', False),
                        'is_view_only': perms.get('is_view_only', False),
                    }
                )
                count += 1
            else:
                print(f"    Warning: Menuitem code '{code}' not found")
    
    return count


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
                'lead_data_scope': 'ALL' if group_name in ('Director', 'Team Leader', 'Sales Executive') else 'ALL',
                'followup_data_scope': 'ALL' if group_name in ('Director', 'Team Leader', 'Sales Executive') else 'ALL',
                'sitevisit_data_scope': 'ALL' if group_name in ('Director', 'Team Leader', 'Sales Executive') else 'ALL',
                'booking_data_scope': 'ALL' if group_name in ('Director', 'Team Leader', 'Sales Executive') else 'ALL',
            }
        )

        if created:
            user.set_password(DEFAULT_PASSWORD)
            user.save()

        # Assign group (legacy)
        group = Group.objects.get(name=group_name)
        user.groups.clear()
        user.groups.add(group)
        
        # Assign menuitem-based permissions (new system)
        perm_count = seed_user_menu_permissions(user, group_name)

        created_users[username] = user
        action = 'Created' if created else 'Exists'
        print(f"  {action}: {username} ({user.first_name} {user.last_name}) -> Group: {group_name}, MenuPerms: {perm_count}")

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
    
    # Count menu permissions
    from Users.models import UserPermission
    print(f"  UserPermissions: {UserPermission.objects.count()}")
    
    print(f"\n  Login with any user using password: {DEFAULT_PASSWORD}")
    print(f"  Usernames: {', '.join(u['username'] for u in USERS)}")
    print()


if __name__ == '__main__' or True:
    run()
