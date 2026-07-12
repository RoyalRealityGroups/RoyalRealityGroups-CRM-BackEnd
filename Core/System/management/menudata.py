import os.path
import tablib

from Core.Users.models import ContentTypeDetail, PermissionDetail
from Core.Users.resources import ContentTypeDetailResource, DjangoAppResource, PermissionDetailResource
from Core.System.resources import MenuResource,SubmenuResource,MenuitemResource
from Core.System.models import Menuitem 
from django.conf import settings
 
GENERAL_APP_LABEL = getattr(settings, 'GENERAL_APP_LABEL', 'General')

#Export data

def export_menu_data():
    mypath=f"{GENERAL_APP_LABEL}/Data/"
    
    if not os.path.exists(mypath):
        os.mkdir(mypath)

    try:
        menu = MenuResource()
        dataset = menu.export()
        with open(mypath+'menu.json', 'w') as f:
            f.write(dataset.json)
        print("Success to Export Menu Data")
    except:
        print(" Failed to Export Menu Data ")



    try:
        submenu = SubmenuResource()
        dataset = submenu.export()
        with open(mypath+'submenu.json', 'w') as f:
            f.write(dataset.json)
        print("Success to Export Submenu Data")
    except:
        print(" Failed to Export Submenu Data ")
    


    try:
        queryset = Menuitem.objects.filter(permission__permissiondetails__release = True, permission__content_type__contenttypedetails__release = True)
        menuitem = MenuitemResource()
        dataset = menuitem.export(queryset)
        with open(mypath+'menuitem.json', 'w') as f:
            f.write(dataset.json)
        print("Success to Export MenuItem Data")
    except:
        print(" Failed to Export MenuItem Data ")
    


    try:
        djangoapp = DjangoAppResource()
        dataset = djangoapp.export()
        with open(mypath+'djangoapp.json', 'w') as f:
            f.write(dataset.json)
        print("Success to Export DjangoApp Data")
    except:
        print(" Failed to Export DjangoApp Data ")



    try:
        queryset = ContentTypeDetail.objects.filter(release = True,)
        contenttypedetail = ContentTypeDetailResource()
        dataset = contenttypedetail.export()
        with open(mypath+'contenttypedetail.json', 'w') as f:
            f.write(dataset.json)
        print("Success to Export ContentTypeDetail Data")
    except:
        print(" Failed to Export ContentTypeDetail Data ")
    


    try:
        queryset = PermissionDetail.objects.filter(release = True, permission__content_type__contenttypedetails__release = True)
        permissiondetail = PermissionDetailResource()
        dataset = permissiondetail.export(queryset)
        with open(mypath+'permissiondetail.json', 'w') as f:
            f.write(dataset.json)
        print("Success to Export PermissionDetail Data")
    except:
        print(" Failed to Export PermissionDetail Data ")
    



#import data

def import_menu_data():

    mypath="Menu/"
    
    # Create missing permissions first
    from django.core.management import call_command
    print("Creating missing permissions...")
    call_command('migrate', verbosity=0)
    call_command('UpdateContentTypeDetail', verbosity=1)
    call_command('UpdatePermissionDetail', verbosity=1)
    
    # Helper function to print detailed errors
    def print_import_errors(result, data_type):
        print(f'Failed to Import {data_type} data has errors')
        print(f'Has errors: {result.has_errors()}')
        print(f'Has validation errors: {result.has_validation_errors()}')
        
        # Print row errors with details
        row_errors = result.row_errors()
        if row_errors:
            print(f'Row errors: {len(row_errors)} rows have errors')
            for row_num, errors in row_errors:
                print(f"  Row {row_num}:")
                for error in errors:
                    print(f"    - Error: {error.error}")
                    if hasattr(error, 'traceback'):
                        print(f"    - Traceback: {error.traceback}")
        
        # Print base errors
        if result.base_errors:
            print(f'Base errors: {result.base_errors}')
        
        # Print invalid rows
        if result.invalid_rows:
            print(f'Invalid rows: {result.invalid_rows}')

    menu = MenuResource()
    dataset = tablib.Dataset()
    dataset.json = open(mypath+'menu.json', "r").read()
    result = menu.import_data(dataset, dry_run=True)
    print("Processing a Import Menu Data")

    if not result.has_errors():
        result = menu.import_data(dataset, dry_run=False)
        print(' Success to Export Menu data ')
    else:
        print_import_errors(result, 'Menu')

    submenu = SubmenuResource()
    dataset = tablib.Dataset()
    dataset.json = open(mypath+'submenu.json', "r").read()
    result = submenu.import_data(dataset, dry_run=True)
    print("Processing a Import Submenu Data")

    if not result.has_errors():
        result = submenu.import_data(dataset, dry_run=False)
        print(' Success to Export Submenu data ')
    else:
        print_import_errors(result, 'Submenu')

    menuitem = MenuitemResource()
    dataset = tablib.Dataset()
    dataset.json = open(mypath+'menuitem.json', "r").read()
    result = menuitem.import_data(dataset, dry_run=True, skip_unchanged=True, report_skipped=False)
    print("Processing a Import Menuitem Data")

    if not result.has_errors():
        result = menuitem.import_data(dataset, dry_run=False, skip_unchanged=True, report_skipped=False)
        print(' Success to Export MenuItem data ')
    else:
        print_import_errors(result, 'Menuitem')

    djangoapp = DjangoAppResource()
    dataset = tablib.Dataset()
    dataset.json = open(mypath+'djangoapp.json', "r").read()
    result = djangoapp.import_data(dataset, dry_run=True)
    print("Processing a Import DjangoApp Data")

    if not result.has_errors():
        result = djangoapp.import_data(dataset, dry_run=False)
        print(' Success to Export DjangoApp data ')
    else:
        print_import_errors(result, 'DjangoApp')

    contenttypedetail = ContentTypeDetailResource()
    dataset = tablib.Dataset()
    dataset.json = open(mypath+'contenttypedetail.json', "r").read()
    result = contenttypedetail.import_data(dataset, dry_run=True)
    print("Processing a Import ContentTypeDetail Data")

    if not result.has_errors():
        result = contenttypedetail.import_data(dataset, dry_run=False)
        print(' Success to Export ContentTypeDetail data ')
    else:
        print_import_errors(result, 'ContentTypeDetail')

    permissiondetail = PermissionDetailResource()
    dataset = tablib.Dataset()
    dataset.json = open(mypath+'permissiondetail.json', "r").read()
    result = permissiondetail.import_data(dataset, dry_run=True, skip_unchanged=True, report_skipped=False)
    print("Processing a Import PermissionDetail Data")

    if not result.has_errors():
        result = permissiondetail.import_data(dataset, dry_run=False, skip_unchanged=True, report_skipped=False)
        print(' Success to Export Permissiondetail data ')
    else:
        print_import_errors(result, 'PermissionDetail')




