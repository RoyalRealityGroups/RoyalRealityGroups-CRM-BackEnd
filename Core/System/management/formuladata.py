import os.path
import tablib


from Core.System.resources import FormulaResource
from django.conf import settings
 
GENERAL_APP_LABEL = getattr(settings, 'GENERAL_APP_LABEL', 'General')

#Export Data
def export_formula_data():
    mypath=f"{GENERAL_APP_LABEL}/Data/"

    try:
    
        if not os.path.exists(mypath):
            os.mkdir(mypath)
        
        formula = FormulaResource()
        dataset = formula.export()

        with open(mypath+'formula.json', 'w') as f:
            f.write(dataset.json)
        print("Success to Export Formula Data")

    except:
        print(" Failed to Export Formula Data ")







#Import Data
def import_formula_data():

    mypath="Users/Data/"

    formula = FormulaResource()
    dataset = tablib.Dataset()
    dataset.json = open(mypath+'formula.json', "r").read()
    result = formula.import_data(dataset, dry_run=True)
    print("Processing a Import Formula Data")

    if not result.has_errors():
        result = formula.import_data(dataset, dry_run=False)
        print("Success to Import Formula Data")

    else:
        print('Failed to import Formula data has errors ')
        print(result.has_errors())
        print(result.has_validation_errors())
        print( result.row_errors())
        print(result.base_errors)
        print(result.invalid_rows)




