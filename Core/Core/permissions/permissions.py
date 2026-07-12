import os
from django.conf import settings
# from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated,DjangoModelPermissions, DjangoObjectPermissions, BasePermission
from rest_framework import exceptions
import copy

class AllPermissions(DjangoModelPermissions):

    def __init__(self):
        self.perms_map = copy.deepcopy(self.perms_map) 
        self.perms_map['GET'] = ['%(app_label)s.view_%(model_name)s']

    
    def has_permission(self, request, view):
        if not request.user or (
           not request.user.is_authenticated and self.authenticated_users_only):
            return False

        # Workaround to ensure DjangoModelPermissions are not applied
        # to the root view when using DefaultRouter.
        if getattr(view, '_ignore_model_permissions', False):
            return True

        queryset = self._queryset(view)
        perms = self.get_required_permissions(request.method, queryset.model)

        return request.user.has_perms(perms)
    

def GetPermission(perms=''):
    class CheckPermission(BasePermission):

        def has_permission(self, request, view):
            method = request.method
            if not bool(request.user and request.user.is_authenticated):
                return False
            if request.user.is_superuser:
                return True
            elif method in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'] and perms in list(request.user.get_all_permissions()):
                return True
            else:
                return False

    return CheckPermission


def GetFocusPermission():
    class FocusPermission(BasePermission):

        def has_permission(self, request, view):
            if request.headers.get('token','') == 'LBKUJP3WG36CDIGNIAE8J5IIFI5E8919GAE2JEF359CHI79Q03':
                return True
            else:
                return False

    return FocusPermission

def GetIOPermission():
    IO_SECRET = os.getenv("IO_SECRET", default=settings.IO_SECRET)
    class IOPermission(BasePermission):
        def has_permission(self, request, view):
            if request.headers.get('ioAuthorization','') == IO_SECRET and IO_SECRET != None:
                return True
            else:
                return False

    return IOPermission


class IsCustomer(BasePermission):

    def has_permission(self, request, view):
        user = request.user
        user_type = type(user)
        user_type = user_type.__name__
        if not bool(request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        elif user_type == 'Customer':
            return True
        else:
            return False


class IsOnlyCustomer(BasePermission):
    #   Only Customers except Guests
    def has_permission(self, request, view):
        user = request.user
        user_type = type(user)
        user_type = user_type.__name__
        if not bool(request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        elif user_type == 'Customer':
            return True
        else:
            return False
        

class IsDeliveryPerson(BasePermission):

    def has_permission(self, request, view):
        user = request.user
        user_type = type(user)
        user_type = user_type.__name__
        if not bool(request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        elif user_type == 'DeliveryPerson':
            return True
        else:
            return False
        
    

class IsDriver(BasePermission):

    def has_permission(self, request, view):
        user = request.user
        user_type = type(user)
        user_type = user_type.__name__
        if not bool(request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        elif user_type == 'Driver':
            return True
        else:
            return False