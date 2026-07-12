from django.core.management.base import BaseCommand
from Core.System.management.menudata import import_menu_data



class Command(BaseCommand):
    help = 'Importing ContentTypeDetail, Menu, MenuItem, SubMenu, DjangoApp, PermissionDetail Data from Initial json Data'

    def handle(self, *args, **kwargs):
        self.stdout.write("Import Menu json Data Started")
        import_menu_data()      
        self.stdout.write("Importing Menu json Data Ended")




# python manage.py import_menu_data