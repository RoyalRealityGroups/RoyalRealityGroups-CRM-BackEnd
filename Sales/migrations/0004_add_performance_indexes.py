# Generated migration for adding performance indexes to Sales models

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Sales', '0003_alter_salesorder_authorized_status_and_more'),
    ]

    operations = [
        # SalesOrder indexes
        migrations.AddIndex(
            model_name='salesorder',
            index=models.Index(
                fields=['order_date', 'company'],
                name='salesorder_date_company_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='salesorder',
            index=models.Index(
                fields=['customer_type', 'retailer', 'distributor', 'superstockist'],
                name='salesorder_customer_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='salesorder',
            index=models.Index(
                fields=['status', 'order_date'],
                name='salesorder_status_date_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='salesorder',
            index=models.Index(
                fields=['company', 'status', 'order_date'],
                name='salesorder_company_status_idx'
            ),
        ),
    ]
