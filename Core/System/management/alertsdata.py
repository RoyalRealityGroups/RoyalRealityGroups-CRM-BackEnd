import os.path
import tablib

from Core.System.resources import AlertConfigResource, TemplateResource
from django.conf import settings
 
GENERAL_APP_LABEL = getattr(settings, 'GENERAL_APP_LABEL', 'General')

#Export data

def export_alerts_data():
    mypath=f"{GENERAL_APP_LABEL}/Data/"
    
    if not os.path.exists(mypath):
        os.mkdir(mypath)

    try:
        alert = AlertConfigResource()
        dataset = alert.export()
        with open(mypath+'alerts.json', 'w') as f:
            f.write(dataset.json)
        print("Success to Export Alert Data")
    except:
        print(" Failed to Export Alert Data ")



#import data

def import_alerts_data():

    mypath=f"{GENERAL_APP_LABEL}/Data/"


    alert = AlertConfigResource()
    dataset = tablib.Dataset()
    dataset.json = open(mypath+'alerts.json', "r").read()
    result = alert.import_data(dataset, dry_run=True)
    print("Processing a Import Alert Data")

    if not result.has_errors():
        result = alert.import_data(dataset, dry_run=False)
        print(' Success to Export Alert data ')

    else:
        print('Failed to Import Alert data has errors ')
        print(result.has_errors())
        print(result.has_validation_errors())
        print( result.row_errors())
        print(result.base_errors)
        print(result.invalid_rows)



