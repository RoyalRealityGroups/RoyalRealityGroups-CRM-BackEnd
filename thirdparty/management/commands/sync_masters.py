import time
from django.core.management.base import BaseCommand





class Command(BaseCommand):
    help = 'It Helps to get the masters from the Focus'

    def handle(self, *args, **kwargs):
        self.stdout.write("Started Syncing Data")
        time.sleep(70)
        self.stdout.write("Sync Completed")
        
        
        
        
# python manage.py sync_masters