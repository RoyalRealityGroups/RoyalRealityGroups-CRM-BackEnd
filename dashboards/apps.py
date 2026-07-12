from django.apps import AppConfig


class DashboardsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboards'
    verbose_name = 'Dashboards'

    def ready(self):
        """Import signals when app is ready."""
        pass
