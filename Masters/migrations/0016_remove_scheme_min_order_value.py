from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('Masters', '0015_alter_schemecondition_condition_type_choices'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scheme',
            name='min_order_value',
        ),
    ]
