from django.core.management.base import BaseCommand
from django.db import transaction
from Masters.models import (
    Country, State, City, Area, Company, Location, WareHouse, UOM,
    Category, Brand, Tax, Item, OutletType, Superstockist, Distributor, 
    Retailer, PriceBook
)
from Masters.validators import add_deleted_prefix_to_field
from datetime import datetime


class Command(BaseCommand):
    help = 'Migrate existing duplicate records by adding prefixes to deleted ones'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making actual changes',
        )
        parser.add_argument(
            '--model',
            type=str,
            help='Specific model to process (e.g., Country, State, etc.)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        specific_model = options.get('model')
        
        # List of models to process
        models_to_process = [
            Country, State, City, Area, Company, Location, WareHouse, UOM,
            Category, Brand, Tax, Item, OutletType, Superstockist, Distributor, 
            Retailer, PriceBook
        ]
        
        if specific_model:
            # Filter to specific model
            models_to_process = [
                model for model in models_to_process 
                if model.__name__.lower() == specific_model.lower()
            ]
            if not models_to_process:
                self.stdout.write(
                    self.style.ERROR(f'Model "{specific_model}" not found')
                )
                return

        self.stdout.write(
            self.style.SUCCESS(
                f'Starting duplicate migration {"(DRY RUN)" if dry_run else ""}'
            )
        )

        total_processed = 0
        total_updated = 0

        for model_class in models_to_process:
            processed, updated = self.process_model(model_class, dry_run)
            total_processed += processed
            total_updated += updated

        self.stdout.write(
            self.style.SUCCESS(
                f'Migration complete. Processed: {total_processed}, Updated: {total_updated}'
            )
        )

    def process_model(self, model_class, dry_run=False):
        """Process a single model for duplicate handling"""
        model_name = model_class.__name__
        self.stdout.write(f'\nProcessing {model_name}...')
        
        processed = 0
        updated = 0
        
        try:
            with transaction.atomic():
                # Process name duplicates
                if hasattr(model_class, 'name'):
                    name_updated = self.handle_name_duplicates(model_class, dry_run)
                    updated += name_updated
                
                # Process code duplicates  
                if hasattr(model_class, 'code'):
                    code_updated = self.handle_code_duplicates(model_class, dry_run)
                    updated += code_updated
                
                processed = model_class.objects.count()
                
                if dry_run:
                    # Rollback transaction in dry run
                    transaction.set_rollback(True)
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error processing {model_name}: {str(e)}')
            )
            return 0, 0
        
        self.stdout.write(
            f'  {model_name}: {processed} records processed, {updated} updated'
        )
        
        return processed, updated

    def handle_name_duplicates(self, model_class, dry_run=False):
        """Handle name duplicates by adding prefixes to deleted records"""
        updated = 0
        
        # Find case-insensitive name duplicates
        from django.db.models import Count
        from django.db.models.functions import Lower
        
        # Get names that appear more than once (case-insensitive)
        duplicate_names = (
            model_class.objects
            .annotate(lower_name=Lower('name'))
            .values('lower_name')
            .annotate(count=Count('lower_name'))
            .filter(count__gt=1)
        )
        
        for dup in duplicate_names:
            lower_name = dup['lower_name']
            
            # Get all records with this name (case-insensitive)
            records = model_class.objects.filter(name__iexact=lower_name)
            
            # Separate active and deleted records
            active_records = records.filter(is_deleted=False)
            deleted_records = records.filter(is_deleted=True)
            
            # If multiple active records exist, mark older ones as deleted with prefix
            if active_records.count() > 1:
                # Keep the newest active record, mark others as deleted
                newest_active = active_records.order_by('-created_on').first()
                older_active = active_records.exclude(pk=newest_active.pk)
                
                for record in older_active:
                    if not dry_run:
                        record.name = add_deleted_prefix_to_field(record, 'name')
                        record.is_deleted = True
                        record.save(update_fields=['name', 'is_deleted'])
                    
                    self.stdout.write(
                        f'    Marked duplicate active {model_class.__name__} as deleted: {record.name}'
                    )
                    updated += 1
            
            # Add prefixes to deleted records that don't have them
            for record in deleted_records:
                if not record.name.startswith('DEL_'):
                    if not dry_run:
                        record.name = add_deleted_prefix_to_field(record, 'name')
                        record.save(update_fields=['name'])
                    
                    self.stdout.write(
                        f'    Added prefix to deleted {model_class.__name__}: {record.name}'
                    )
                    updated += 1
        
        return updated

    def handle_code_duplicates(self, model_class, dry_run=False):
        """Handle code duplicates by adding prefixes to deleted records"""
        updated = 0
        
        # Find case-insensitive code duplicates
        from django.db.models import Count
        from django.db.models.functions import Upper
        
        # Get codes that appear more than once (case-insensitive)
        duplicate_codes = (
            model_class.objects
            .annotate(upper_code=Upper('code'))
            .values('upper_code')
            .annotate(count=Count('upper_code'))
            .filter(count__gt=1)
        )
        
        for dup in duplicate_codes:
            upper_code = dup['upper_code']
            
            # Get all records with this code (case-insensitive)
            records = model_class.objects.filter(code__iexact=upper_code)
            
            # Separate active and deleted records
            active_records = records.filter(is_deleted=False)
            deleted_records = records.filter(is_deleted=True)
            
            # If multiple active records exist, mark older ones as deleted with prefix
            if active_records.count() > 1:
                # Keep the newest active record, mark others as deleted
                newest_active = active_records.order_by('-created_on').first()
                older_active = active_records.exclude(pk=newest_active.pk)
                
                for record in older_active:
                    if not dry_run:
                        record.code = add_deleted_prefix_to_field(record, 'code')
                        record.is_deleted = True
                        record.save(update_fields=['code', 'is_deleted'])
                    
                    self.stdout.write(
                        f'    Marked duplicate active {model_class.__name__} as deleted: {record.code}'
                    )
                    updated += 1
            
            # Add prefixes to deleted records that don't have them
            for record in deleted_records:
                if not record.code.startswith('DEL_'):
                    if not dry_run:
                        record.code = add_deleted_prefix_to_field(record, 'code')
                        record.save(update_fields=['code'])
                    
                    self.stdout.write(
                        f'    Added prefix to deleted {model_class.__name__}: {record.code}'
                    )
                    updated += 1
        
        return updated