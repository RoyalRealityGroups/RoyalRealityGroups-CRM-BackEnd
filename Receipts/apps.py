from django.apps import AppConfig


class ReceiptsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Receipts'
    verbose_name = 'Receipts Management'

    def ready(self):
        import Receipts.signals
