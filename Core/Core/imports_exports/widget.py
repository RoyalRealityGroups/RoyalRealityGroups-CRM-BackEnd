
from import_export.widgets import Widget
from django.apps import apps

from Core.Core.utils.utils import get_model_path


class ChoicesWidget(Widget):
    """
    Widget that uses choice display values in place of database values
    """
    def __init__(self, choices, *args, **kwargs):
        """
        Creates a self.choices dict with a key, display value, and value,
        db value, e.g. {'Chocolate': 'CHOC'}
        """
        self.choices = dict(choices)
        self.revert_choices = dict((v, k) for k, v in self.choices.items())

    def clean(self, value, row=None, *args, **kwargs):
        """Returns the db value given the display value"""
        return self.revert_choices.get(value, value) if value else None

    def render(self, value, obj=None, **kwargs):
        """Returns the display value given the db value"""
        return self.choices.get(value, '')




class PermissionCodeWidget(Widget):
   
    def __init__(self, model, field='pk', *args, **kwargs):
        self.model = model
        self.field = field
        super().__init__(*args, **kwargs)

    def get_queryset(self, value, row, *args, **kwargs):
        return self.model.objects.all()

    def clean(self, value, row=None, *args, **kwargs):
        val = super().clean(value)
        if val:
            args = val.split('.')
            if len(args) > 0:
                try:
                    return self.get_queryset(value, row, *args, **kwargs).get(content_type__app_label = args[0], codename = args[1])
                except self.model.DoesNotExist:
                    print(f"Warning: Permission {val} not found, skipping...")
                    return None
            else:
                return None
        else:
            return None

    def render(self, value, obj=None, **kwargs):
        if value is None:
            return ""

        if value:
            return '%s.%s' % (value.content_type.app_label, value.codename)
        else:
            return ""

 
class UserRelatedWidget(Widget):
    def __init__(self, user_field):
        super().__init__()
        self.user_field = user_field
 
    def render(self, value, obj=None, **kwargs):
       
        type_field = f"{self.user_field}_type"
        identifier_field = f"{self.user_field}_identifier"
 
        # Check if the required fields exist on the object
        if not hasattr(obj, type_field) or not hasattr(obj, identifier_field):
            return ""
 
        type_value = getattr(obj, type_field)
        identifier_value = getattr(obj, identifier_field)
 
        # Validate that we have both values
        if not type_value or not identifier_value:
            return ""
 
        try:
            # Get the model class from the type value
            model_path = get_model_path(type_value)
           
            if model_path is None:
                return ""
           
            model_class = apps.get_model(model_path)
           
            # Find the user object
            user_obj = model_class.objects.filter(id=identifier_value).first()
           
            if user_obj:
                # Try to get username first, fall back to string representation
                result = getattr(user_obj, "username", None)
                if result is None:
                    result = getattr(user_obj, "name", str(user_obj))
                print(f"Found user: {result}")
                return result
            else:
                return ""
               
        except (LookupError, ValueError, AttributeError) as e:
            print(f"Error getting user object: {e}")
            return ""
 
    def clean(self, value, row=None, **kwargs):
        """
        Handle import cleaning - convert username back to user reference
        """
        if not value:
            return None
           
        # This method would need to be implemented based on your import requirements
        # For now, returning the value as-is
        return value