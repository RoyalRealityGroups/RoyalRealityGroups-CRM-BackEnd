from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.apps import apps

class Command(BaseCommand):
    help = 'Create missing permissions for menu import'

    def handle(self, *args, **options):
        # Define missing permissions
        missing_perms = [
            ('General', 'view_import_data', 'Can view import data'),
            ('General', 'view_import_history', 'Can view import history'),
            ('Masters', 'import_country', 'Can import country data'),
            ('Masters', 'import_state', 'Can import state data'),
            ('Masters', 'import_city', 'Can import city data'),
            ('Masters', 'import_area', 'Can import area data'),
            ('Masters', 'import_route', 'Can import route data'),
            ('Masters', 'import_location', 'Can import location data'),
            ('Masters', 'import_warehouse', 'Can import warehouse data'),
            ('Masters', 'import_category', 'Can import category data'),
            ('Masters', 'import_brand', 'Can import brand data'),
            ('Masters', 'import_tax', 'Can import tax data'),
            ('Masters', 'import_uom', 'Can import UOM data'),
            ('Masters', 'import_item', 'Can import item data'),
            ('Masters', 'import_itemtaxcomposition', 'Can import item tax composition data'),
            ('Masters', 'view_pricebookhistory', 'Can view price book history'),
        ]
        
        created_count = 0
        
        for app_label, codename, name in missing_perms:
            try:
                # Get or create content type for the app
                content_type, _ = ContentType.objects.get_or_create(
                    app_label=app_label,
                    model='permission'  # Generic model name
                )
                
                # Create permission if it doesn't exist
                permission, created = Permission.objects.get_or_create(
                    codename=codename,
                    content_type=content_type,
                    defaults={'name': name}
                )
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Created permission: {app_label}.{codename}')
                    )
                    created_count += 1
                else:
                    self.stdout.write(f'Permission already exists: {app_label}.{codename}')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating {app_label}.{codename}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nCreated {created_count} new permissions')
        )
