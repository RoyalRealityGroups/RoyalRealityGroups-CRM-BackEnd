from django.core.management.base import BaseCommand
from Core.System.management.menudata import export_menu_data



class Command(BaseCommand):
    help = 'Exporting ContentTypeDetail, Menu, MenuItem, SubMenu, DjangoApp, PermissionDetail Data from Initial json Data'

    def handle(self, *args, **kwargs):
        self.stdout.write("Export Menu json Data Started")
        export_menu_data()      
        self.stdout.write("Exporting Menu json Data Ended")



# python manage.py export_menu_data