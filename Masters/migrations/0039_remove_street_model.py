# Generated migration to remove Street model

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Masters', '0038_district_alter_area_options_area_country_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Street',
        ),
    ]
