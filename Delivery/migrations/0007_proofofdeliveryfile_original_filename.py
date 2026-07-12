from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Delivery", "0006_update_pod_optional_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="proofofdeliveryfile",
            name="original_filename",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]

