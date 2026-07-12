from django.db.models import Q, Count
# from Common.Authentication import User
# from Masters.models import State, Location
 
from rest_framework import serializers
from django.db.models import ForeignKey, ManyToManyField

from Core.Users.models import Assignee, AssigneeDefnition, DataPermissions
 
 
class ModelSerializerPermissionMixin(serializers.ModelSerializer):
    """
    Mixin to add permission validation to serializers.
    """
 
   
    def __init__(self,*args,**kwargs):
 
        self.init_validation_methods()
 
        super().__init__(*args, **kwargs)
   
    def validate_model_permission(self, user, app_label, model_name, instance_id, screen_type):
        """
        Validate if the user has permission for the given model instance.
 
        Args:
            user: User instance
            model_path: String path to model (e.g. 'Masters.city')
            instance_id: ID of the model instance
 
        Returns:
            bool: True if user has permission, False if exclusions apply.
 
        Raises:
            serializers.ValidationError: If permission is denied or the model path is invalid.
        """
        print(f'validate_model_permission: user={user}, model_path={app_label}.{model_name}, instance_id={instance_id}', ) #screen_type = {screen_type}
       
        model_path = f"{app_label}.{model_name}"
        # user_group_ids = list(user.groups.values_list('id', flat=True))
        instance_id = str(instance_id)
        filters = {}
        no_filters = {}
 
        if screen_type == 'entry':
            filters = {'entry': True}
            no_filters = {'entry': False}
        elif screen_type == 'view':
            filters = {'view': True}
            no_filters = {'entry': False}
        elif screen_type == 'report':
            filters = {'report': True}
            no_filters = {'entry': False}
        else:
            return False

        user_type = type(user)
        user_type = user_type.__name__
        user_identifier = user.id

        group_related_name = user.__class__._meta.get_field('groups').related_query_name()
        group_filter = {f'group__{group_related_name}' : user}

        assigndef_obj =  AssigneeDefnition.objects.filter(screen__app_label = app_label ,screen__model= model_name, is_deleted = False).first()
        assignee_bypass = user.has_perm(f'{app_label}.assignee_bypass_{model_name}')
        if assigndef_obj and not assignee_bypass:
            if Assignee.objects.filter(user_type= user_type, user_identifier= user_identifier, screen__app_label = app_label,screen__model= model_name, instance_id= instance_id, is_deleted = False).exists():
                return True
            else:
                if DataPermissions.objects.filter(Q(user_type= user_type, user_identifier= user_identifier,type = 1) & Q(is_deleted=False) | Q(type=2, **group_filter) & Q(is_deleted=False) ).count() > 0:
                    pass
                else:
                    return False
 
 
        result = DataPermissions.objects.filter(Q(Q(user_type= user_type, user_identifier= user_identifier, type = 1) | Q(type=2, **group_filter)) & Q(is_deleted=False) ).filter(
            model_path=model_path,
            # **filters
        ).aggregate(
            total_records=Count('id'),
            specific_exclusions=Count(
                'id',
                filter=Q(instance_id=instance_id, exclusions=True, **filters)
            ),
            specific_inclusions=Count(
                'id',
                filter=Q(instance_id=instance_id, exclusions=False, **filters)
            ),
            any_exclusions=Count(
                'id',
                filter=Q(exclusions=True)
            )
        )
        print('result', result)
       
        # If no records exist, access is granted
        if result['total_records'] == 0:
            return True
           
        # If the specific model_id is found
        if result['specific_exclusions'] > 0:
            return False  # Explicitly excluded
        if result['specific_inclusions'] > 0:
            return True  # Explicitly included
           
        # If the model_id is not found, check if we're in exclusion mode
        return result['any_exclusions'] > 0
   
 
    def validate_relation(self, field, value, screen_type):
        # print('validate_relation', self, field_name, value)
        print(f'validate_relation: field_name={field.name}, value={value}, type={type(value)}')
        """
        Validate both ForeignKey and ManyToMany field permissions dynamically.
 
        Args:
            field_name (str): Name of the field being validated.
            value: Primary key (ID) for ForeignKey or list of IDs for ManyToMany.
 
        Returns:
            Validated value if permission exists.
        """
        # field = self.Meta.model._meta.get_field(field_name)
        related_model = field.related_model
        model_path = f"{related_model._meta.app_label}.{related_model._meta.model_name}"
        # print('model_path',)
        # validator = PermissionValidator()
        user = self.context['request'].user
        if user.is_superuser:
            return True
        # Handle ManyToManyField (list of IDs)
        if field.many_to_many:
            print('field.many_to_many',field.many_to_many)
            if not value:
                return False  # Allow empty values
 
           
            instances = value if isinstance(value, (list, tuple)) else list(value)
            for instance in instances:
                res= self.validate_model_permission(
                    user = self.context['request'].user,
                    app_label=related_model._meta.app_label,
                    model_name=related_model._meta.model_name,
                    instance_id=instance.id,
                    # instance_id=instance,
                    screen_type = screen_type
                )
                if not res:
                    return False  # Permission denied
 
            return True
 
        # Handle ForeignKey (single ID)
        elif field.one_to_one or field.is_relation:
            print('field.ForeignKey',field.one_to_one or field.is_relation)
            print(f'ForeignKey field detected. Raw value: {value}')
           
            print('value',value)
            print('user',self.context['request'].user)
            print('model_path',model_path)
            
            if value is None:
                return True  # Allow None values for optional fields
 
            res = self.validate_model_permission(
                user=self.context['request'].user,
                app_label=related_model._meta.app_label,
                model_name=related_model._meta.model_name,
                instance_id=value.id,
                screen_type = screen_type
 
            )
            if not res:
                return False  # Permission denied
 
            return True
       
        # If the field is neither FK nor M2M, raise an error
        return False
   
 
    def init_validation_methods(self,):
        model_class = self.Meta.model
       
        data_validate_fields = getattr(self.Meta, "data_validate_fields", [])
        fields = getattr(self.Meta, "fields", [])
 
        # if len(data_validate_fields) == 0:
        #     raise ValueError(f"data_validate_fields has zero arguments")
 
        missing_fields = [field for field in data_validate_fields if field not in list(fields)]
 
        if missing_fields:
            raise ValueError(f"data_validate_fields - {missing_fields} are missing in fields")
 
        for field_name in data_validate_fields:
            field = model_class._meta.get_field(field_name)
            if isinstance(field, ForeignKey) or isinstance(field, ManyToManyField):
                related_model = field.related_model
 
                if type(related_model) == str:
                    # continue
                    model_path = related_model
                else:
                    model_path = f"{related_model._meta.app_label}.{related_model._meta.model_name}"
                    # like getting model_path f"{Account._meta.app_label}.{Account._meta.model_name}"
               
                if isinstance(field, ForeignKey):
                    field_name = field.name + '_id'
                else:
                    field_name = field.name[:-1] if field.name.endswith('s') else field.name
                    field_name = field_name + '_ids'
                   
 
                def validate_m_warper(field):
                    def validate_m(value):
                        # print('value-----',value)
                        if not self.validate_relation(field, value, 'entry'):
                            raise serializers.ValidationError(f"You do not have permission to use this value. Please contact your administrator if you believe this is incorrect.")
                       
                        return value
                    return validate_m
               
                setattr(self, f'validate_{field_name}', validate_m_warper(field))
 