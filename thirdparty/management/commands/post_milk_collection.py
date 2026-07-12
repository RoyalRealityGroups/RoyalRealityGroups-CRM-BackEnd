from django.core.management.base import BaseCommand
from thirdparty.AMCU import post_milk_collection


class Command(BaseCommand):
    help = 'It Helps to post the milk collection to Focus'

    def handle(self, *args, **kwargs):
        self.stdout.write("Started Posting Milk Collection Data")
        post_milk_collection()      
        self.stdout.write("Posting Completed")
        
        
# python manage.py post_milk_collection