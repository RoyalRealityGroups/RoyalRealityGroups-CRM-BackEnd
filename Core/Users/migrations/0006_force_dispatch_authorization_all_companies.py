from django.db import migrations


def force_dispatch_all_companies(apps, schema_editor):
    AuthorizationDefinition = apps.get_model('core_users', 'AuthorizationDefinition')

    dispatch_defs = AuthorizationDefinition.objects.filter(
        screen__model='dispatchplan',
        screen__app_label__in=['Dispatch', 'dispatch', 'Delivery', 'delivery'],
        is_deleted=False,
    )

    for definition in dispatch_defs:
        definition.has_all_companies = True
        definition.save(update_fields=['has_all_companies'])
        definition.companies.clear()


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core_users', '0005_authorizationdefinition_auto_approve_creator_level'),
    ]

    operations = [
        migrations.RunPython(force_dispatch_all_companies, noop_reverse),
    ]
