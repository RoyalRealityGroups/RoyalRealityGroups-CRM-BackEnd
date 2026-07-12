import os.path
import tablib

from Core.System.resources import TemplateResource
from django.conf import settings
 
GENERAL_APP_LABEL = getattr(settings, 'GENERAL_APP_LABEL', 'General')

#Export data

def export_template_data():
    mypath=f"{GENERAL_APP_LABEL}/Data/"
    
    if not os.path.exists(mypath):
        os.mkdir(mypath)

    try:
        template = TemplateResource()
        dataset = template.export()
        with open(mypath+'template.json', 'w') as f:
            f.write(dataset.json)
        print("Success to Export Template Data")
    except:
        print(" Failed to Export Template Data ")



#import data

def import_template_data():

    mypath=f"{GENERAL_APP_LABEL}/Data/"


    template = TemplateResource()
    dataset = tablib.Dataset()
    dataset.json = open(mypath+'template.json', "r").read()
    result = template.import_data(dataset, dry_run=True)
    print("Processing a Import Template Data")

    if not result.has_errors():
        result = template.import_data(dataset, dry_run=False)
        print(' Success to Export Template data ')

    else:
        print('Failed to Import Template data has errors ')
        print(result.has_errors())
        print(result.has_validation_errors())
        print( result.row_errors())
        print(result.base_errors)
        print(result.invalid_rows)



