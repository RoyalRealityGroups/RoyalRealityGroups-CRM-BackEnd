from django.db import connection


def check_if_table_exists(model):
    """
    Check if the database table for the given model exists.

    Args:
        model (Django Model): The model class to check the table for.

    Returns:
        bool: True if the table exists, False otherwise.
    """
    table_name = model._meta.db_table
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = %s)", 
            [table_name]
        )
        return cursor.fetchone()[0]
