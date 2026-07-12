from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core_users", "0004_remove_authorizationdefinition_unique_active_authorization_definition_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="authorizationdefinition",
            name="auto_approve_creator_level",
            field=models.BooleanField(default=False),
        ),
    ]

