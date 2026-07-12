from django.apps import AppConfig
from django.db.utils import ProgrammingError, OperationalError
from django.db import connection




class SystemConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Core.System'


    def ready(self):
        
        try:            
            from Core.Core.authentication import JWTAuthenticationScheme
            
            if self._is_running_migrations():
                return

            from .models import Setting
            from Core.Core.database.table_validator import check_if_table_exists

            if not check_if_table_exists(Setting):
                return

            # If we get here, the table exists and migrations aren't running
            from Core.System.services import register_signals,start_alert_scheduler_thread,start_task_scheduler_thread,initialize_templates
            from Core.System.database_event_listener import start_listener
            start_alert_scheduler_thread()
            # start_task_scheduler_thread()  # Disabled to prevent repeated SQL queries
            initialize_templates()
            register_signals()
            start_listener()

        except (ProgrammingError, OperationalError, ImportError):
            # Database isn't ready, table doesn't exist, or model import failed
            return
        
        # from Core.System.services import register_signals
        # register_signals()

    def _is_running_migrations(self):
        """Check if we're running migrations"""
        import sys
        return any(arg in sys.argv for arg in ['migrate', 'makemigrations'])
    
    
