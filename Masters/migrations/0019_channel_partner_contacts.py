# Generated migration for channel partner contacts

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('Masters', '0018_remove_location_contact_fields'),
    ]

    operations = [
        # Create SuperstockistContact model
        migrations.CreateModel(
            name='SuperstockistContact',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_deleted', models.BooleanField(default=False)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('created_by_type', models.CharField(blank=True, max_length=50, null=True)),
                ('created_by_identifier', models.CharField(blank=True, max_length=255, null=True)),
                ('updated_by_type', models.CharField(blank=True, max_length=50, null=True)),
                ('updated_by_identifier', models.CharField(blank=True, max_length=255, null=True)),
                ('contact_person', models.CharField(max_length=100)),
                ('phone', models.CharField(blank=True, max_length=15, null=True)),
                ('email', models.EmailField(blank=True, max_length=100, null=True)),
                ('designation', models.CharField(blank=True, max_length=100, null=True)),
                ('is_primary', models.BooleanField(default=False)),
                ('superstockist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contacts', to='Masters.superstockist')),
            ],
            options={
                'verbose_name': 'Superstockist Contact',
                'verbose_name_plural': 'Superstockist Contacts',
                'db_table': 'superstockist_contacts',
                'ordering': ['-is_primary', 'contact_person'],
            },
        ),
        # Create DistributorContact model
        migrations.CreateModel(
            name='DistributorContact',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_deleted', models.BooleanField(default=False)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('created_by_type', models.CharField(blank=True, max_length=50, null=True)),
                ('created_by_identifier', models.CharField(blank=True, max_length=255, null=True)),
                ('updated_by_type', models.CharField(blank=True, max_length=50, null=True)),
                ('updated_by_identifier', models.CharField(blank=True, max_length=255, null=True)),
                ('contact_person', models.CharField(max_length=100)),
                ('phone', models.CharField(blank=True, max_length=15, null=True)),
                ('email', models.EmailField(blank=True, max_length=100, null=True)),
                ('designation', models.CharField(blank=True, max_length=100, null=True)),
                ('is_primary', models.BooleanField(default=False)),
                ('distributor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contacts', to='Masters.distributor')),
            ],
            options={
                'verbose_name': 'Distributor Contact',
                'verbose_name_plural': 'Distributor Contacts',
                'db_table': 'distributor_contacts',
                'ordering': ['-is_primary', 'contact_person'],
            },
        ),
        # Create RetailerContact model
        migrations.CreateModel(
            name='RetailerContact',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_deleted', models.BooleanField(default=False)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('created_by_type', models.CharField(blank=True, max_length=50, null=True)),
                ('created_by_identifier', models.CharField(blank=True, max_length=255, null=True)),
                ('updated_by_type', models.CharField(blank=True, max_length=50, null=True)),
                ('updated_by_identifier', models.CharField(blank=True, max_length=255, null=True)),
                ('contact_person', models.CharField(max_length=100)),
                ('phone', models.CharField(blank=True, max_length=15, null=True)),
                ('email', models.EmailField(blank=True, max_length=100, null=True)),
                ('designation', models.CharField(blank=True, max_length=100, null=True)),
                ('is_primary', models.BooleanField(default=False)),
                ('retailer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contacts', to='Masters.retailer')),
            ],
            options={
                'verbose_name': 'Retailer Contact',
                'verbose_name_plural': 'Retailer Contacts',
                'db_table': 'retailer_contacts',
                'ordering': ['-is_primary', 'contact_person'],
            },
        ),
    ]
