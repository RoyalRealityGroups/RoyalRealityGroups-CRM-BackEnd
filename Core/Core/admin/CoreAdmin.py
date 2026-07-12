from django.apps import apps
from functools import partial

from Core.Core.utils.utils import get_model_path



class CoreAdmin:

    def __init__(self, model, admin_site):
        if not hasattr(self, 'user_related_fields'):
            self.user_related_fields = []
        self.user_related_fields = list(self.user_related_fields)
        for field in self.user_related_fields:
            field_name = field
            if not hasattr(self, field_name):
                display_method = partial(self.get_user_display, user_field=field)
                display_method.__name__ = field_name
                display_method.short_description = f"{field.replace('_', ' ').title()}"
                setattr(self, field_name, display_method)
        super().__init__(model, admin_site)


    def get_user_display(self, obj, user_field):
        type_field = f"{user_field}_type"
        identifier_field = f"{user_field}_identifier"

        type_value = getattr(obj, type_field, None)
        identifier_value = getattr(obj, identifier_field, None)

        if not type_value or identifier_value is None:
            return "-"
        
        model_path = get_model_path(type_value)

        model_class = apps.get_model(model_path)
        user_obj = model_class.objects.filter(id=identifier_value).first()
        return str(user_obj.username) if user_obj else "(User not found)"
        