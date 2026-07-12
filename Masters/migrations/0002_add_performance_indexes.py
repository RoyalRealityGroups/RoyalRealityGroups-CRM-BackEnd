# Generated migration for adding performance indexes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Masters', '0001_initial'),
    ]

    operations = [
        # Item indexes
        migrations.AddIndex(
            model_name='item',
            index=models.Index(fields=['name'], name='item_name_idx'),
        ),
        migrations.AddIndex(
            model_name='item',
            index=models.Index(fields=['is_active', 'is_saleable'], name='item_active_saleable_idx'),
        ),
        
        # PriceBook compound indexes
        migrations.AddIndex(
            model_name='pricebook',
            index=models.Index(
                fields=['company', 'item', 'is_active', 'effective_from', 'effective_to'],
                name='pricebook_lookup_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='pricebook',
            index=models.Index(
                fields=['state', 'city', 'area'],
                name='pricebook_location_idx',
                condition=models.Q(price_type='GEOGRAPHIC')
            ),
        ),
        migrations.AddIndex(
            model_name='pricebook',
            index=models.Index(
                fields=['superstockist', 'distributor', 'retailer'],
                name='pricebook_partner_idx',
                condition=models.Q(price_type='CHANNEL_PARTNER')
            ),
        ),
        
        # Channel Partner state indexes
        migrations.AddIndex(
            model_name='superstockist',
            index=models.Index(fields=['state', 'is_active'], name='superstockist_state_active_idx'),
        ),
        migrations.AddIndex(
            model_name='distributor',
            index=models.Index(fields=['state', 'is_active'], name='distributor_state_active_idx'),
        ),
        migrations.AddIndex(
            model_name='distributor',
            index=models.Index(fields=['superstockist', 'is_active'], name='distributor_parent_active_idx'),
        ),
        migrations.AddIndex(
            model_name='retailer',
            index=models.Index(fields=['state', 'is_active'], name='retailer_state_active_idx'),
        ),
        migrations.AddIndex(
            model_name='retailer',
            index=models.Index(fields=['distributor', 'is_active'], name='retailer_parent_active_idx'),
        ),
    ]
