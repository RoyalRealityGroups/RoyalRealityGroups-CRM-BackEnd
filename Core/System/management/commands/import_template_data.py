from django.core.management.base import BaseCommand

from Core.System.management.templatedata import import_template_data




class Command(BaseCommand):
    help = 'Importing Template Data from Initial json Data'

    def handle(self, *args, **kwargs):
        self.stdout.write("Import Template json Data Started")
        import_template_data()      
        self.stdout.write("Importing Template json Data Ended")




# python manage.py import_template_data