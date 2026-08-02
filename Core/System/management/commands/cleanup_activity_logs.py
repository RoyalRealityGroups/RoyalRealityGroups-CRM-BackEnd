"""
Management command to delete ActivityLog records older than 6 months.

Usage:
    python manage.py cleanup_activity_logs

Run via cron every Sunday at 2am:
    0 2 * * 0 python manage.py cleanup_activity_logs
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Delete ActivityLog records older than 6 months. Keeps the last 180 days.'

    def handle(self, *args, **options):
        from Core.System.models import ActivityLog

        cutoff = timezone.now() - timedelta(days=180)

        self.stdout.write(f'Deleting ActivityLog records created before {cutoff.strftime("%Y-%m-%d")}...')

        deleted_count, _ = ActivityLog.objects.filter(created_on__lt=cutoff).delete()

        self.stdout.write(
            self.style.SUCCESS(f'Done. Deleted {deleted_count} ActivityLog record(s).')
        )
        self.stdout.write(
            f'Remaining: {ActivityLog.objects.count()} record(s).'
        )
