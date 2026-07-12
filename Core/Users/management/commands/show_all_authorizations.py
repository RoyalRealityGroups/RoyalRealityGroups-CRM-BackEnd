from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from Core.Users.models import Authorization, AuthorizationDefinition
from django.db.models import Q


class Command(BaseCommand):
    help = 'Show all Authorization records with details'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('\n=== All Authorization Records ===\n'))
        
        active_q = Q(is_deleted=False) | Q(is_deleted__isnull=True)
        authorizations = Authorization.objects.filter(active_q).order_by('level', 'id')
        
        self.stdout.write(f'Total Authorization records: {authorizations.count()}\n')
        
        for auth in authorizations:
            self.stdout.write(f'\n--- Authorization ID: {auth.id} ---')
            self.stdout.write(f'  Code: {auth.code if hasattr(auth, "code") else "N/A"}')
            self.stdout.write(f'  Level: {auth.level}')
            
            # Type
            if auth.type == Authorization.USER:
                self.stdout.write(f'  Type: USER')
                self.stdout.write(f'    User Type: {auth.user_type}')
                self.stdout.write(f'    User ID: {auth.user_identifier}')
            elif auth.type == Authorization.GROUP:
                group_name = auth.group.name if auth.group else 'None'
                self.stdout.write(f'  Type: GROUP')
                self.stdout.write(f'    Group: {group_name} (ID: {auth.group_id if auth.group else "None"})')
            else:
                self.stdout.write(f'  Type: {auth.type}')
            
            # Screen (ContentType)
            if auth.screen:
                ct = auth.screen
                self.stdout.write(f'  Screen: {ct.app_label}.{ct.model} (ContentType ID: {ct.id})')
            else:
                self.stdout.write(f'  Screen: None')
            
            # Authorization Definition
            if auth.authorization_definition:
                auth_def = auth.authorization_definition
                code = getattr(auth_def, 'code', 'N/A')
                self.stdout.write(f'  Auth Definition: {code} (ID: {auth_def.id})')
                if auth_def.screen:
                    ct = auth_def.screen
                    self.stdout.write(f'    Linked to screen: {ct.app_label}.{ct.model}')
            else:
                self.stdout.write(f'  Auth Definition: None')
            
            # Notifications
            flags = []
            if auth.send_email:
                flags.append('Email')
            if auth.send_sms:
                flags.append('SMS')
            if auth.send_notification:
                flags.append('Notification')
            self.stdout.write(f'  Notifications: {", ".join(flags) if flags else "None"}')
        
        self.stdout.write(self.style.SUCCESS('\n=== End of List ===\n'))
        
        # Show ContentTypes for reference
        self.stdout.write(self.style.WARNING('\n=== Available ContentTypes ===\n'))
        content_types = ContentType.objects.filter(
            Q(app_label='Sales', model='salesorder') |
            Q(app_label='Invoice', model='invoice') |
            Q(app_label='Dispatch', model='dispatchplan') |
            Q(app_label='Delivery', model='proofofdelivery') |
            Q(app_label='Masters', model='scheme') |
            Q(app_label='Masters', model='pricebookdocument')
        )
        for ct in content_types:
            self.stdout.write(f'  {ct.app_label}.{ct.model} = ContentType ID {ct.id}')
        
        self.stdout.write('')
