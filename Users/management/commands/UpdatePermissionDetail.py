import re

from django.core.management.base import BaseCommand
from django.utils import timezone


from django.db.models import Q, Sum, Count

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group, Permission

from Core.Users.models import PermissionDetail



class Command(BaseCommand):
    help = 'Updating PermissionDetail Data from Permission Data'

    def handle(self, *args, **kwargs):
        self.stdout.write("Update PermissionDetail Started")
        permissionlist =Permission.objects.all().select_related('permissiondetails').annotate(n_details=Count('permissiondetails')).filter(n_details=0)
        for permission in permissionlist:
            chunks = permission.codename.split("_")
            name = chunks[0] if len(chunks) > 1 else permission.name

            PermissionDetail.objects.create(permission=permission, name= name.capitalize(), )
        
        self.stdout.write("Update PermissionDetail Ended")

# python manage.py UpdatePermissionDetail