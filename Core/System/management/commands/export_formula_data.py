from django.core.management.base import BaseCommand
from Core.System.management.formuladata import export_formula_data





class Command(BaseCommand):
    help = 'Exporting FormulaUpdate, FormulaVariables, Formula from Initial json Data'

    def handle(self, *args, **kwargs):
        self.stdout.write("Export Formula json Data Started")
        export_formula_data()      
        self.stdout.write("Exporting Formula json Data Ended")





# python manage.py export_formula_data