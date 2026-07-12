from django.core.management.base import BaseCommand
from datetime import date, datetime, timedelta
from django.db import models

from django.db.models.fields import BooleanField
from Core.Reports.models import ScheduledEmail
from Core.Reports.views import create_scheduledemail
from django.db.models import Q, Sum, Count, Max, F
from django.db.models import F, ExpressionWrapper
from django.db.models.functions import ExtractDay
from django.db.models import F, ExpressionWrapper, DurationField
from django.db.models.functions import ExtractDay
from django.db.models import Func, F
from django.db.models.functions import Floor

class ExtractEpoch(Func):
    function = 'EXTRACT'
    template = "%(function)s(EPOCH from %(expressions)s)"
    output_field = models.FloatField()


class Command(BaseCommand):
    help = 'Performs some action on TemplateItems based on their repeat interval and start date'

    def handle(self, *args, **options, ):
        today = date.today()
        current_time = datetime.now().time()
        current_datetime = datetime.combine(date.today(), current_time)  
        current_datetime_str = current_datetime - timedelta(hours=5, minutes=30)
        current = current_datetime_str.strftime("%Y-%m-%d %H:%M:00+00:00")

        matching_items = ScheduledEmail.objects \
        .annotate(
            days_diff_mode=ExpressionWrapper(
                F('startdate') - today, output_field=models.DurationField()
            )
        ).annotate(
        days_diff_mode=ExpressionWrapper(
            F('days_diff_mode') - (F('days_diff_mode') / F('repeatdays')) * F('repeatdays'),
            output_field=models.DurationField()
        ))\
        .filter(
            Q(startdate__lte=today) &
            Q(is_deleted=False) &
            Q(time=current) &
            (~Q(last_run__lt=today) | Q(last_run__isnull=True)) &
            (
                (Q(frequency=1) & Q(startdate__lte=today)) |
                (Q(frequency=2) & Q(startdate__lte=today, startdate__week_day=today.weekday())) |
                (Q(frequency=3, startdate__day=today.day)) |
                (Q(frequency=4, startdate__day=today.day, startdate__month=today.month)) |
                (Q(frequency=5) & Q(repeatdays__isnull=False) & Q(startdate__lte=today) 
                 )
            )
        )

        print('matching_items111111111111', matching_items.count())

        for item in matching_items:

            create_scheduledemail(item)

# python manage.py scheduledemail

