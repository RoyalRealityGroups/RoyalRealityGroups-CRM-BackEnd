from django.apps import AppConfig
from django.conf import settings


class ReportsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Core.Reports'

    if not settings.DYNAMICS_SAFE_MODE:
        def ready(self):
            import Core.System.activity_log