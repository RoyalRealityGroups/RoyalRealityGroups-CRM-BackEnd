import os
import psycopg2
import psycopg2.extensions
import select
import json
import threading
from django.core.cache import cache
from datetime import datetime

listener_thread = None
stop_event = threading.Event()

class DataBaseEventListener:
    def __init__(self, db_config, channel="settings_changes", default_schema="public"):
        """
        Initialize a PostgreSQL event listener.
        
        Args:
            db_config (dict): Database connection parameters
            channel (str): The notification channel to listen on
            default_schema (str): Default schema to use when none is specified
        """
        self.db_config = db_config
        self.channel = channel
        self.default_schema = default_schema
        self.conn = None
        self.cur = None
        
    def connect(self):
        """Establish connection to PostgreSQL database."""
        self.conn = psycopg2.connect(**self.db_config)
        self.conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        self.cur = self.conn.cursor()
        # print(f"Connected to PostgreSQL database: {self.db_config['database']}")
        
    def setup_trigger(self, table_name, trigger_name=None):
        """
        Create a trigger function and trigger on a table to notify on changes.
        
        Args:
            table_name (str): The name of the table to monitor (with or without schema)
            trigger_name (str, optional): Custom trigger name. Defaults to "{table_name}_notify_trigger".
        """
        # Handle schema-qualified table names
        if '.' in table_name:
            schema_name, base_table_name = table_name.split('.', 1)
        else:
            schema_name = self.default_schema
            base_table_name = table_name
        
        # Always quote the table name to handle uppercase letters, underscores, etc.
        quoted_table_name = f'{schema_name}."{base_table_name}"'
        
        # Use the base table name for the trigger name and function name
        base_table_name = base_table_name.strip('"')  # Remove quotes if present
        if trigger_name is None:
            trigger_name = f"{base_table_name}_notify_trigger"
            
        function_name = f"{schema_name}.{base_table_name}_notify_event"
        
        # Create or replace the trigger function
        self.cur.execute(f"""
        CREATE OR REPLACE FUNCTION {function_name}() RETURNS TRIGGER AS $$
        DECLARE 
            notification json;
        BEGIN
            -- Construct the notification with ONLY essential fields
            -- Instead of full row data, just include ID and preferences_code
            notification = json_build_object(
                'table', TG_TABLE_NAME,
                'action', TG_OP,
                'data', json_build_object(
                    'id', CASE WHEN TG_OP = 'DELETE' THEN OLD.id ELSE NEW.id END,
                    'preferences_code', CASE WHEN TG_OP = 'DELETE' THEN OLD.preferences_code ELSE NEW.preferences_code END
                ),
                'timestamp', CURRENT_TIMESTAMP
            );
            
            -- Send notification
            PERFORM pg_notify('{self.channel}', notification::text);
            
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
        """)
        
        # Create the trigger on the table
        trigger_sql = f"""
        DROP TRIGGER IF EXISTS {trigger_name} ON {quoted_table_name};
        CREATE TRIGGER {trigger_name}
        AFTER INSERT OR UPDATE OR DELETE ON {quoted_table_name}
        FOR EACH ROW EXECUTE FUNCTION {function_name}();
        """
        
        self.cur.execute(trigger_sql)
        
        # print(f"Created trigger '{trigger_name}' on table '{quoted_table_name}'")
    
    def start_listening(self, callback=None):
        """
        Start listening for notifications on the specified channel.
        
        Args:
            callback (callable, optional): Function to call when an event is received.
                                          If None, events are just printed.
        """
        try:
            # Start listening on the channel
            self.cur.execute(f"LISTEN {self.channel}")
            
            while True:
                # Check if there's a notification to be processed
                if select.select([self.conn], [], [], 5) == ([], [], []):
                    # Timeout, no event received
                    continue
                
                # Process any pending notifications
                self.conn.poll()
                while self.conn.notifies:
                    notify = self.conn.notifies.pop(0)
                    # Parse the notification payload as JSON
                    payload = json.loads(notify.payload)
                    
                    
                    if callback:
                        callback(payload)
                    else:
                        # Default behavior: print the event details
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        action = payload['action']
                        table = payload['table']
                        
        except KeyboardInterrupt:
            pass
        finally:
            self.close()
    
    def close(self):
        """Close database connection."""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

# Example usage
def handle_db_event(event_data):
    """Custom event handler function."""
    action = event_data['action']
    table = event_data['table']
    data = event_data['data']
        
    preferences_code= data.get('preferences_code')
    preferences= data.get('preferences')
    

    if table == 'System_setting':
        # Perform specific action for System_setting table
        # set_py_preferences(preferences_code,preferences)
        # cache.clear()
        cache.delete(preferences_code)


def listener_worker():
    global listener_thread, stop_event
    stop_event.clear()
    
    # Database connection parameters
    db_config = {
        'host': os.getenv('DB_HOST'),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASS'),
        'port': os.getenv('DB_PORT')
    }
    
    listener = DataBaseEventListener(db_config)
    listener.connect()
    listener.setup_trigger('System_setting')
    
    try:
        listener.start_listening(callback=handle_db_event)
    except Exception as e:
        pass
    finally:
        pass
        

def start_listener():
    global listener_thread, stop_event
    
    if listener_thread and listener_thread.is_alive():
        stop_event.set()
        listener_thread.join()
    
    listener_thread = threading.Thread(target=listener_worker, daemon=True)
    listener_thread.start()
    # print("Listener started in a new thread.")