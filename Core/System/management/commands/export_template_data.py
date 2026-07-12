from django.core.management.base import BaseCommand

from Core.System.management.templatedata import export_template_data




class Command(BaseCommand):
    help = 'Exporting Template Data from Initial json Data'

    def handle(self, *args, **kwargs):
        self.stdout.write("Export Template json Data Started")
        export_template_data()
        self.stdout.write("Exporting Template json Data Ended")



# python manage.py export_template_data