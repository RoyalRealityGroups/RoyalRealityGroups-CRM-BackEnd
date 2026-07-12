from django.apps import apps

from rest_framework import serializers

from Core.Core.utils.utils import get_model_path
from Core.Users.serializers import CoreUserMiniSerializer



class FileRelatedField(serializers.RelatedField):
    """
    A read only field that represents its targets using their
    plain string representation.
    """

    def __init__(self, **kwargs):
        kwargs['read_only'] = True
        super().__init__(**kwargs)

    def to_representation(self, value):
        # return self.context['request'].build_absolute_uri(value.url)
        # # return str(value)
        try:
            url = value.url
            res =self.context['request'].build_absolute_uri(url)

        except Exception as e:
            url = "static/images/thumbnail/default_no_file.png"
            res =self.context['request'].build_absolute_uri(url)


        # res =self.context['request'].build_absolute_uri(url)
        
        return res


class FileThumbnailRelatedField(serializers.RelatedField):
    """
    A read only field that represents its targets using their
    plain string representation.
    """

    def __init__(self, **kwargs):
        kwargs['read_only'] = True
        super().__init__(**kwargs)

    def to_representation(self, value):

        try:
            url = value.url
            res =self.context['request'].build_absolute_uri(url)

        except Exception as e:
            url = "static/images/thumbnail/default_no_file.png"
            res =self.context['request'].build_absolute_uri(url)


        # res =self.context['request'].build_absolute_uri(url)
        
        return res
    

class UserRelatedField(serializers.Field):
    """
    A read-only field that represents user information from either created_by or modified_by
    """
    def __init__(self, user_field=None, **kwargs):
        self.user_field = user_field
        kwargs['read_only'] = True
        kwargs['source'] = '*' 
        super().__init__(**kwargs)


    def bind(self, field_name, parent):
        super().bind(field_name, parent)


    def to_representation(self, obj):
        type_field = f"{self.user_field}_type"
        identifier_field = f"{self.user_field}_identifier"
        
        if not hasattr(obj, type_field) or not hasattr(obj, identifier_field):
            return None
        
        type_value = getattr(obj, type_field)
        identifier_value = getattr(obj, identifier_field)

        model_path = get_model_path(type_value)

        if not model_path:
            return {}
        
        model_class = apps.get_model(model_path)

        user_obj = model_class.objects.filter(id= identifier_value).first()

        if not user_obj:
            return None
        
        user_data = CoreUserMiniSerializer(user_obj).data

        return user_data
    