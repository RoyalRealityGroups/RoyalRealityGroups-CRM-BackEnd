#!/usr/bin/env python
import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SalesApp.settings')
django.setup()

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

def check_permissions():
    # Load menuitem.json
    with open('Menu/menuitem.json', 'r') as f:
        menuitems = json.load(f)
    
    # Load permissiondetail.json  
    with open('Menu/permissiondetail.json', 'r') as f:
        permissiondetails = json.load(f)
    
    missing_permissions = []
    
    # Check menuitem permissions
    print("Checking menuitem permissions...")
    for item in menuitems:
        perm = item.get('Permission')
        if perm and '.' in perm:
            app_label, codename = perm.split('.', 1)
            try:
                Permission.objects.get(content_type__app_label=app_label, codename=codename)
                print(f"✓ Found: {perm}")
            except Permission.DoesNotExist:
                print(f"✗ Missing: {perm}")
                missing_permissions.append(perm)
    
    # Check permissiondetail permissions
    print("\nChecking permissiondetail permissions...")
    for item in permissiondetails:
        perm = item.get('Permission')
        if perm and '.' in perm:
            app_label, codename = perm.split('.', 1)
            try:
                Permission.objects.get(content_type__app_label=app_label, codename=codename)
                print(f"✓ Found: {perm}")
            except Permission.DoesNotExist:
                print(f"✗ Missing: {perm}")
                missing_permissions.append(perm)
    
    print(f"\n=== SUMMARY ===")
    print(f"Total missing permissions: {len(set(missing_permissions))}")
    for perm in sorted(set(missing_permissions)):
        print(f"  - {perm}")

if __name__ == '__main__':
    check_permissions()