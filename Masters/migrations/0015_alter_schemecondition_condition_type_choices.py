from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('Masters', '0014_scheme_schemeapplicability_schemebenefit_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='schemecondition',
            name='condition_type',
            field=models.CharField(
                choices=[
                    ('MIN_QUANTITY', 'Minimum Quantity'),
                    ('MIN_VALUE', 'Minimum Value'),
                    ('MAX_QUANTITY', 'Maximum Quantity'),
                    ('MAX_VALUE', 'Maximum Value'),
                    ('EXACT_QUANTITY', 'Exact Quantity'),
                    ('QUANTITY_RANGE', 'Quantity Range'),
                    ('VALUE_RANGE', 'Value Range'),
                    ('ITEM_COMBO', 'Item Combination'),
                ],
                help_text='Type of condition',
                max_length=30,
            ),
        ),
    ]
