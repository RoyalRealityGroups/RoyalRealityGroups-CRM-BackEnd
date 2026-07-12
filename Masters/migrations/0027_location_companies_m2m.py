from django.db import migrations, models


def copy_location_company_to_m2m(apps, schema_editor):
    Location = apps.get_model('Masters', 'Location')
    through_model = Location.companies.through

    rows_to_create = []
    for location in Location.objects.exclude(company_id__isnull=True).values('id', 'company_id'):
        rows_to_create.append(
            through_model(location_id=location['id'], company_id=location['company_id'])
        )

    if rows_to_create:
        through_model.objects.bulk_create(rows_to_create, ignore_conflicts=True)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('Masters', '0026_item_code_not_required_in_field_config'),
    ]

    operations = [
        migrations.AddField(
            model_name='location',
            name='companies',
            field=models.ManyToManyField(blank=True, related_name='locations', to='Masters.company'),
        ),
        migrations.RunPython(copy_location_company_to_m2m, noop_reverse),
        migrations.RemoveField(
            model_name='location',
            name='company',
        ),
    ]
