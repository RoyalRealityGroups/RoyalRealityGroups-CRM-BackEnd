"""
Script to add the Site Visit Calendar menu item to the database.
Run with: python manage.py shell < scripts/add_site_visit_calendar_menu.py

Or from Django shell:
  exec(open('scripts/add_site_visit_calendar_menu.py').read())
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BaseProject.settings')
try:
    django.setup()
except:
    pass

from Core.System.models import Submenu, Menuitem, Menu
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

# 1. Clear the direct click on Site Visit Management submenu so it expands
sv_submenu = Submenu.objects.filter(code='SBM-007').first()
if sv_submenu:
    if sv_submenu.click:
        sv_submenu.click = ''
        sv_submenu.save(update_fields=['click'])
        print(f"✓ Cleared click on '{sv_submenu.name}' (SBM-007) — it will now expand")
    else:
        print(f"✓ '{sv_submenu.name}' (SBM-007) already has no direct click")
else:
    print("✗ SBM-007 submenu not found")

# 2. Add the Site Visit Calendar menu item if it doesn't exist
if sv_submenu:
    existing = Menuitem.objects.filter(code='LM-002B').first()
    if existing:
        print(f"✓ Menu item LM-002B already exists: '{existing.name}'")
    else:
        # Find the permission for viewing site visits
        perm = Permission.objects.filter(codename='view_sitevisit').first()
        menu = sv_submenu.menu

        mi = Menuitem.objects.create(
            code='LM-002B',
            name='Site Visit Calendar',
            icon='calendar_month',
            link='/sitevisit/calendar',
            sequence=2,
            menu=menu,
            submenu=sv_submenu,
            permission=perm,
        )
        print(f"✓ Created menu item: '{mi.name}' (LM-002B) → /sitevisit/calendar")

    # Also ensure the existing Site Visits item (LM-002) has sequence=1
    sv_item = Menuitem.objects.filter(code='LM-002').first()
    if sv_item and sv_item.sequence != 1:
        sv_item.sequence = 1
        sv_item.save(update_fields=['sequence'])
        print(f"✓ Updated LM-002 sequence to 1")

print("\nDone! Refresh the frontend to see the updated sidebar.")
