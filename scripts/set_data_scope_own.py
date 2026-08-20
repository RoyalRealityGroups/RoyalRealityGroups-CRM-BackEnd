"""
One-time script: Set all non-superuser users to OWN data scope.

Usage:
    python manage.py shell < scripts/set_data_scope_own.py
"""
import django
import os
import sys

if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BaseProject.settings')
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    django.setup()

from Users.models import User

updated = User.objects.filter(is_superuser=False).update(
    lead_data_scope='OWN',
    followup_data_scope='OWN',
    sitevisit_data_scope='OWN',
    booking_data_scope='OWN',
)

print(f'Updated {updated} user(s) to OWN data scope.')
print('Superusers are unchanged and still see all data.')
