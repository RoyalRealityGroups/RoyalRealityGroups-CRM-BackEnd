from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_users', '0006_force_dispatch_authorization_all_companies'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='authorizationdefinition',
            name='unique_active_global_authorization',
        ),
        migrations.AddConstraint(
            model_name='authorizationdefinition',
            constraint=models.UniqueConstraint(
                fields=('screen',),
                condition=models.Q(
                    status=True,
                    has_all_companies=True,
                    has_all_locations=True,
                    is_deleted=False,
                ),
                name='unique_active_global_authorization',
            ),
        ),
    ]
