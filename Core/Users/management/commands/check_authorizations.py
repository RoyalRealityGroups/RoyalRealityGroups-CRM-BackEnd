from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from Core.Users.models import Authorization, AuthorizationDefinition
from django.db.models import Q


class Command(BaseCommand):
    help = 'Check Authorization configuration for pending approvals'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('\n=== Authorization Configuration Check ===\n'))
        
        # Models to check
        models_to_check = [
            ('Sales', 'salesorder'),
            ('Invoice', 'invoice'),
            ('Dispatch', 'dispatchplan'),
            ('Delivery', 'proofofdelivery'),
            ('Masters', 'scheme'),
            ('Masters', 'pricebookdocument'),
        ]
        
        for app_label, model_name in models_to_check:
            self.stdout.write(f'\n--- {app_label}.{model_name} ---')
            
            try:
                # Get ContentType
                content_type = ContentType.objects.get(app_label=app_label, model=model_name)
                self.stdout.write(f'✓ ContentType ID: {content_type.id}')
                
                # Check AuthorizationDefinitions
                active_q = Q(is_deleted=False) | Q(is_deleted__isnull=True)
                auth_defs = AuthorizationDefinition.objects.filter(
                    screen=content_type,
                    status=True
                ).filter(active_q)
                
                self.stdout.write(f'  Authorization Definitions: {auth_defs.count()}')
                for auth_def in auth_defs:
                    code = getattr(auth_def, 'code', 'N/A')
                    self.stdout.write(f'    - Code: {code} (ID: {auth_def.id})')
                
                # Check Authorizations
                authorizations = Authorization.objects.filter(
                    screen=content_type
                ).filter(active_q).order_by('level')
                
                self.stdout.write(f'  Direct Screen Authorizations: {authorizations.count()}')
                for auth in authorizations:
                    auth_type = 'User' if auth.type == Authorization.USER else 'Group'
                    name = auth.group.name if auth.group else auth.user_identifier
                    self.stdout.write(f'    Level {auth.level}: {auth_type} - {name}')
                
                # Check via authorization_definition
                auth_via_def = Authorization.objects.filter(
                    authorization_definition__screen=content_type
                ).filter(active_q).order_by('level')
                
                self.stdout.write(f'  Via Auth Definition: {auth_via_def.count()}')
                for auth in auth_via_def:
                    auth_type = 'User' if auth.type == Authorization.USER else 'Group'
                    name = auth.group.name if auth.group else auth.user_identifier
                    auth_def_name = auth.authorization_definition.name if auth.authorization_definition else 'None'
                    self.stdout.write(f'    Level {auth.level}: {auth_type} - {name} (Def: {auth_def_name})')
                
                # Check all authorizations by level (broader)
                all_auths = Authorization.objects.filter(active_q).order_by('level')
                self.stdout.write(f'  All Authorizations (any screen): {all_auths.count()}')
                level_counts = {}
                for auth in all_auths:
                    level_counts[auth.level] = level_counts.get(auth.level, 0) + 1
                for level, count in sorted(level_counts.items()):
                    self.stdout.write(f'    Level {level}: {count} authorizations')
                
            except ContentType.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'✗ ContentType not found for {app_label}.{model_name}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Error: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS('\n=== Check Complete ===\n'))
