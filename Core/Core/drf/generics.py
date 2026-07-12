from rest_framework.generics import GenericAPIView
from rest_framework import mixins, views
# from Common.DynamicPermissions import get_qs
from Core.Core.permissions.DataPermissions import get_data_permission_functions
from Core.Users.models import Assignee, AssigneeDefnition, DataPermissions


get_qs, get_dp_qs =  get_data_permission_functions( DataPermissions, AssigneeDefnition, Assignee)

class MyGenericAPIView(GenericAPIView):
    
    def get_queryset(self):
        user = self.request.user  
        screen_type =  getattr(self, 'screen_type', 'view')
        data_validate_fields =  getattr(self, 'data_validate_fields', [])

        # print('----users',user,screen_type,type(screen_type) )
        # print('----data_validate_fields',data_validate_fields )
        # if not user:
        #     raise Exception("'user' must submit in kwargs in queryset.filter() function")
       
        queryset = super().get_queryset()
        queryset = queryset.filter(is_deleted=False)
        if not getattr(user, "is_authenticated", False):
            return queryset.none()
 
        if not user.is_superuser: #and not user.has_perm('System.all_data')
            app_label = queryset.model._meta.app_label
            model_name = queryset.model._meta.model_name
            queryset = get_qs(app_label, model_name, queryset, user, screen_type = screen_type,data_validate_fields=data_validate_fields) 

        return queryset 


class CreateAPIView(mixins.CreateModelMixin,
                    MyGenericAPIView):
    """
    Concrete view for creating a model instance.
    """
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class ListAPIView(mixins.ListModelMixin,
                  MyGenericAPIView):
    """
    Concrete view for listing a queryset.
    """
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class RetrieveAPIView(mixins.RetrieveModelMixin,
                      MyGenericAPIView):
    """
    Concrete view for retrieving a model instance.
    """
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class DestroyAPIView(mixins.DestroyModelMixin,
                     MyGenericAPIView):
    """
    Concrete view for deleting a model instance.
    """
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class UpdateAPIView(mixins.UpdateModelMixin,
                    MyGenericAPIView):
    """
    Concrete view for updating a model instance.
    """
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class ListCreateAPIView(mixins.ListModelMixin,
                        mixins.CreateModelMixin,
                        MyGenericAPIView):
    """
    Concrete view for listing a queryset or creating a model instance.
    """
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class RetrieveUpdateAPIView(mixins.RetrieveModelMixin,
                            mixins.UpdateModelMixin,
                            MyGenericAPIView):
    """
    Concrete view for retrieving, updating a model instance.
    """
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class RetrieveDestroyAPIView(mixins.RetrieveModelMixin,
                             mixins.DestroyModelMixin,
                             MyGenericAPIView):
    """
    Concrete view for retrieving or deleting a model instance.
    """
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class RetrieveUpdateDestroyAPIView(mixins.RetrieveModelMixin,
                                   mixins.UpdateModelMixin,
                                   mixins.DestroyModelMixin,
                                   MyGenericAPIView):
    """
    Concrete view for retrieving, updating or deleting a model instance.
    """
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
