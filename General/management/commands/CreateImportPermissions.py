from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Create custom permissions for Import module'

    def handle(self, *args, **kwargs):
        self.stdout.write("Creating Import Permissions Started")
        
        # Get or create ContentType for General app
        # We'll use a generic content type for these permissions
        content_type, created = ContentType.objects.get_or_create(
            app_label='General',
            model='importpermission',
            defaults={'model': 'importpermission'}
        )
        
        if created:
            self.stdout.write(f"Created ContentType: General.importpermission")
        
        # Create permissions for Import Data and Import History
        permissions_to_create = [
            ('view_import_data', 'Can view import data'),
            ('view_import_history', 'Can view import history'),
        ]
        
        for codename, name in permissions_to_create:
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                content_type=content_type,
                defaults={'name': name}
            )
            if created:
                self.stdout.write(f"Created Permission: General.{codename}")
            else:
                self.stdout.write(f"Permission already exists: General.{codename}")
        
        self.stdout.write("Creating Import Permissions Completed")

# python manage.py CreateImportPermissions
