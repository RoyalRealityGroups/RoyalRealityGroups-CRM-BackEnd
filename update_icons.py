import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BaseProject.settings')
django.setup()

from Core.System.models import Submenu, Menuitem

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
if masters:
    for name, icon in icon_mapping.items():
        item = Menuitem.objects.filter(submenu=masters, name=name).first()
        if item and icon:
            item.icon = icon
            item.save()
            print(f'Updated {name} icon to {icon}')

print('Icon update complete!')
