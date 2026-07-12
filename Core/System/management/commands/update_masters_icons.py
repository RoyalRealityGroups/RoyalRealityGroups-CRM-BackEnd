from django.core.management.base import BaseCommand
from Core.System.models import Submenu, Menuitem


class Command(BaseCommand):
    help = 'Update Masters submenu item icons with SVG filenames'

    def handle(self, *args, **options):
        # Mapping of Menuitem names to SVG filenames
        icon_mapping = {
            'Country': 'Country.svg',
            'State': 'state.svg',
            'City': 'City.svg',
            'Area': 'Area.svg',
            'Company': 'company.svg',
            'Location': 'location.svg',
            'Warehouse': 'warehouse.svg',
            'UOM': 'UOM.svg',
            'Category': 'category.svg',
            'Brand': 'brand.svg',
            'Tax': 'tax.svg',
            'Item': 'Item.svg',
            'Item Tax Composition': 'Item Tax Composition.svg',
            'Outlet Type': 'Outlet Type.svg',
            'Distributor': 'Distributor.svg',
            'Retailer': 'Retailer.svg',
        }

        masters = Submenu.objects.filter(name='Masters').first()
        if not masters:
            self.stdout.write(self.style.ERROR('Masters submenu not found'))
            return

        updated_count = 0
        for name, icon in icon_mapping.items():
            item = Menuitem.objects.filter(submenu=masters, name=name).first()
            if item:
                item.icon = icon
                item.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Updated {name} icon to {icon}')
                )
                updated_count += 1
            else:
                self.stdout.write(self.style.WARNING(f'✗ Menuitem not found: {name}'))

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Successfully updated {updated_count} menu items')
        )
