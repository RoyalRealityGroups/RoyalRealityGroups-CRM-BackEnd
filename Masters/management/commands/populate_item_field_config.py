from django.core.management.base import BaseCommand

from Masters.field_config_defaults import upsert_item_field_configurations


class Command(BaseCommand):
    help = 'Populate default Item Field Configuration'

    def handle(self, *args, **kwargs):
        created_count, updated_count = upsert_item_field_configurations()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully populated Item Field Configuration: {created_count} created, {updated_count} updated'
            )
        )
