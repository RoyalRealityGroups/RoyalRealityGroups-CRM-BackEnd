from django.core.management.base import BaseCommand

from Core.System.management.alertsdata import export_alerts_data




class Command(BaseCommand):
    help = 'Exporting Alerts Data from Initial json Data'

    def handle(self, *args, **kwargs):
        self.stdout.write("Export Alerts json Data Started")
        export_alerts_data()
        self.stdout.write("Exporting Alerts json Data Ended")



# python manage.py export_alerts_data