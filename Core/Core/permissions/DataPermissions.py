from django.db.models import Q, Exists, OuterRef, CharField
from django.db.models.functions import Cast
from django.db import models
from django.forms import ValidationError
# from Common.Authentication import User
# from Masters.models import State, Location
 
# from Users.models import DataPermissions, AssigneeDefnition, Assignee
from django.db.models import ForeignKey, ManyToManyField
 
def get_data_permission_functions( DataPermissions, AssigneeDefnition, Assignee):
 
    def get_qs(app_label, model_name, base_queryset, user, screen_type = 'view',data_validate_fields=[]):
        queryset = base_queryset
        if not getattr(user, "is_authenticated", False):
            return queryset.none()
        assigndef_obj =  AssigneeDefnition.objects.filter(screen__app_label = app_label,screen__model= model_name, is_deleted = False).first()
        # assignee_bypass =  AssigneeByPass.objects.filter(Q(Q(user=user, type = 1) | Q(group__user=user, type=2)) & Q(is_deleted = False)).first()
 
        # assignee_bypass = user.has_perm(f'{app_label}s.assignee_bypass_{model_name}s')
        assignee_bypass = user.has_perm(f'{app_label}.assignee_bypass_{model_name}')
        # print('assignee_bypass', assignee_bypass)

        user_type = type(user)
        user_type = user_type.__name__
        user_identifier = user.id

        group_related_name = user.__class__._meta.get_field('groups').related_query_name()
        group_filter = {f'group__{group_related_name}' : user}
        
        if assigndef_obj and not assignee_bypass:
            approvals = Assignee.objects.filter(user_type= user_type, user_identifier= user_identifier,screen__app_label = app_label,screen__model= model_name, instance_id=Cast(OuterRef('id'), models.CharField(max_length=36)), is_deleted = False)
 
            queryset_assignee = queryset.annotate(
                is_assignee=Exists(approvals)
            ).filter(is_assignee=True )
           
            if DataPermissions.objects.filter(Q(user_type=user_type, user_identifier= user_identifier, type = 1) & Q(is_deleted=False) | Q( type=2, **group_filter) & Q(is_deleted=False) ).count() > 0:
                if assigndef_obj.apply_type == 1:
                    queryset = (queryset_assignee & get_dp_qs(queryset, user, user_type, user_identifier, group_filter, screen_type,data_validate_fields))
                else:
                    queryset = (queryset_assignee | get_dp_qs(queryset, user, user_type, user_identifier, group_filter, screen_type,data_validate_fields))
            else:
                queryset = queryset_assignee
        else:
            queryset = get_dp_qs(queryset, user, user_type, user_identifier, group_filter, screen_type,data_validate_fields)

        if user.has_perm(f"{app_label}.add_{model_name}"):
            queryset = queryset | base_queryset.filter(created_by_type = user_type, created_by_identifier = user_identifier)
 
        return queryset.distinct()
 
 
    def get_dp_qs(base_queryset, user, user_type, user_identifier, group_filter, screen_type = 'view', data_validate_fields=[]):
 
        if not user.is_superuser:
 
            queryset = base_queryset
            model_class = base_queryset.model
            
            if len(data_validate_fields) == 0:
                fields = model_class._meta.get_fields()
            else:
                fields = [model_class._meta.get_field(field_name) for field_name in data_validate_fields if model_class._meta.get_field(field_name) is not None]

            # Get all relevant permissions in bulk
            model_paths = set()
            field_mappings = {}
            
            for field in fields:
                if isinstance(field, ForeignKey) or isinstance(field, ManyToManyField):
                    related_model = field.related_model
 
                    if type(related_model) == str:
                        model_path = related_model
                    else:
                        model_path = f"{related_model._meta.app_label}.{related_model._meta.model_name}"
                    
                    field_name = field.name + '_id' if isinstance(field, ForeignKey) else field.name
                    model_paths.add(model_path)
                    field_mappings[field_name] = model_path
            
            # Add doc ID
            app_label = model_class._meta.app_label
            model_name = model_class._meta.model_name
            doc_model_path = f"{app_label}.{model_name}"
            model_paths.add(doc_model_path)
            field_mappings['id'] = doc_model_path
            
            # Bulk fetch permissions for all model paths
            filters = get_screen_filters(screen_type)
            
            permissions = DataPermissions.objects.filter(
                Q(user_type=user_type, user_identifier=user_identifier, type=1) | Q(type=2, **group_filter),
                model_path__in=model_paths,
                is_deleted=False,
                **filters
            ).values('model_path', 'instance_id', 'exclusions')
            
            # Group permissions by model_path
            perm_dict = {}
            for perm in permissions:
                model_path = perm['model_path']
                if model_path not in perm_dict:
                    perm_dict[model_path] = {'exclusions': set(), 'inclusions': set()}
                
                if perm['exclusions']:
                    perm_dict[model_path]['exclusions'].add(perm['instance_id'])
                else:
                    perm_dict[model_path]['inclusions'].add(perm['instance_id'])
            
            # Apply permissions using simple field lookups instead of Exists
            combined_q = Q()
            
            for field_name, model_path in field_mappings.items():
                if model_path in perm_dict:
                    perms = perm_dict[model_path]
                    field_q = Q()
                    
                    # Exclusions
                    if perms['exclusions']:
                        field_q &= ~Q(**{f'{field_name}__in': perms['exclusions']})
                    
                    # Inclusions (if any inclusions exist, only allow those)
                    if perms['inclusions']:
                        field_q &= Q(**{f'{field_name}__in': perms['inclusions']})
                    
                    combined_q &= field_q
            
            queryset = queryset.filter(combined_q)
 
        return queryset
 
 
    def get_screen_filters(screen_type):
        if screen_type == 'entry':
            return {'entry': True}
        elif screen_type == 'view':
            return {'view': True}
        elif screen_type == 'report':
            return {'report': True}
        else:
            raise ValidationError('Invalid screen type')
    
    def get_permitted_class(user, user_type, user_identifier, group_filter, model_path, field_name, screen_type):
        # This function is kept for backward compatibility but not used in optimized version
        filters = get_screen_filters(screen_type)
        
        return Q(
            # Two cases:
            # 1. If exclusions=True, return cities NOT in permission model
            # 2. If exclusions=False, return cities IN permission model
           
            ~Exists(
                DataPermissions.objects.filter(Q(user_type=user_type, user_identifier=user_identifier, type = 1) | Q( type=2, **group_filter) ).filter(
                    model_path=model_path, #'path.to.city.model',
                    instance_id = Cast(OuterRef(field_name), output_field=CharField()), #'city_id'
                    exclusions=True,
                    is_deleted = False,
                    **filters
                )
            ) &
            Q(
                Exists(
                    DataPermissions.objects.filter(Q(user_type=user_type, user_identifier=user_identifier, type = 1) | Q( type=2, **group_filter) ).filter(
                        model_path=model_path,
                        instance_id = Cast(OuterRef(field_name), output_field=CharField()),
                        exclusions=False,
                        is_deleted = False,
                        **filters
                    )
                ) |
                ~Exists(
                    DataPermissions.objects.filter(Q(user_type=user_type, user_identifier=user_identifier, type = 1) | Q( type=2, **group_filter) )
                    .filter(
                        model_path=model_path,
                        exclusions=False,
                        is_deleted = False,
                        # **filters
                    )
                )
            )
        )
   
    return get_qs, get_dp_qs
       
 
