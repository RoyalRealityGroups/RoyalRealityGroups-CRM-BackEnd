from django.core.management.base import BaseCommand
from thirdparty.AMCU import getCollectionData


class Command(BaseCommand):
    help = 'It Helps to get the data from Focus'

    def handle(self, *args, **kwargs):
        self.stdout.write("Started Syncing Data")
        getCollectionData()      
        self.stdout.write("Sync Completed")
        
        
# python manage.py sync_amcu_collection_data