from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
import json

class Command(BaseCommand):
    help = 'Check which permissions are missing from the database'

    def handle(self, *args, **options):
        # Load menuitem.json
        try:
            with open('Menu/menuitem.json', 'r') as f:
                menuitems = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('Menu/menuitem.json not found'))
            return
        
        # Load permissiondetail.json  
        try:
            with open('Menu/permissiondetail.json', 'r') as f:
                permissiondetails = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('Menu/permissiondetail.json not found'))
            return
        
        missing_permissions = []
        
        # Check menuitem permissions
        self.stdout.write("Checking menuitem permissions...")
        for item in menuitems:
            perm = item.get('Permission')
            if perm and '.' in perm:
                app_label, codename = perm.split('.', 1)
                try:
                    Permission.objects.get(content_type__app_label=app_label, codename=codename)
                    self.stdout.write(f"✓ Found: {perm}")
                except Permission.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"✗ Missing: {perm}"))
                    missing_permissions.append(perm)
        
        # Check permissiondetail permissions
        self.stdout.write("\nChecking permissiondetail permissions...")
        for item in permissiondetails:
            perm = item.get('Permission')
            if perm and '.' in perm:
                app_label, codename = perm.split('.', 1)
                try:
                    Permission.objects.get(content_type__app_label=app_label, codename=codename)
                    self.stdout.write(f"✓ Found: {perm}")
                except Permission.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"✗ Missing: {perm}"))
                    missing_permissions.append(perm)
        
        self.stdout.write(f"\n=== SUMMARY ===")
        self.stdout.write(f"Total missing permissions: {len(set(missing_permissions))}")
        for perm in sorted(set(missing_permissions)):
            self.stdout.write(self.style.ERROR(f"  - {perm}"))