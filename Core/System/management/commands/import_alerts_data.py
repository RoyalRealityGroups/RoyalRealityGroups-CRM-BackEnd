from django.core.management.base import BaseCommand

from Core.System.management.alertsdata import import_alerts_data




class Command(BaseCommand):
    help = 'Importing Alerts Data from Initial json Data'

    def handle(self, *args, **kwargs):
        self.stdout.write("Import Alerts json Data Started")
        import_alerts_data()      
        self.stdout.write("Importing Alerts json Data Ended")




# python manage.py import_alerts_data