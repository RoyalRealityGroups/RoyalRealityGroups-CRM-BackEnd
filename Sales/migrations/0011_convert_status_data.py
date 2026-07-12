from django.db import migrations


def convert_status_values(apps, schema_editor):
    """Convert old status values to new business workflow statuses"""
    SalesOrder = apps.get_model('Sales', 'SalesOrder')
    
    # Mapping: old_status -> new_status
    status_mapping = {
        'PENDING': 'DRAFT',
        'APPROVED': 'CONFIRMED',
        'REJECTED': 'CANCELLED',
        'PROCESSING': 'CONFIRMED',
        'PARTIALLY_INVOICED': 'PARTIALLY_INVOICED',
        'INVOICED': 'INVOICED',
        'DELIVERED': 'DELIVERED',
    }
    
    for old_status, new_status in status_mapping.items():
        SalesOrder.objects.filter(status=old_status).update(status=new_status)


def reverse_convert_status_values(apps, schema_editor):
    """Reverse conversion for rollback"""
    SalesOrder = apps.get_model('Sales', 'SalesOrder')
    
    # Reverse mapping
    reverse_mapping = {
        'DRAFT': 'PENDING',
        'CONFIRMED': 'APPROVED',
        'CANCELLED': 'REJECTED',
        'PARTIALLY_DISPATCHED': 'PROCESSING',
        'DISPATCHED': 'PROCESSING',
        'PARTIALLY_INVOICED': 'PARTIALLY_INVOICED',
        'INVOICED': 'INVOICED',
        'DELIVERED': 'DELIVERED',
    }
    
    for new_status, old_status in reverse_mapping.items():
        SalesOrder.objects.filter(status=new_status).update(status=old_status)


class Migration(migrations.Migration):

    dependencies = [
        ('Sales', '0010_update_sales_order_status_choices'),
    ]

    operations = [
        migrations.RunPython(convert_status_values, reverse_convert_status_values),
    ]
