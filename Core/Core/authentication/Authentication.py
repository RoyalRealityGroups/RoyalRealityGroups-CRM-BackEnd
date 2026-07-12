
from django.db.models import Q
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

from Core.Core.utils.utils import get_model_path
from Core.Core.context.Context import get_session_data, set_session_data, set_user, set_context_session
from Core.Users.models import JwtToken
User = get_user_model()

import string
from django.utils.crypto import get_random_string
import jwt
from django.conf import settings
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
import json
from django.apps import apps as django_apps

import logging

logger = logging.getLogger(__name__)

def set_session(key, value):
    # request_cfg.session_data[key] = value
    set_context_session(key, value)
    json_data = json.dumps(get_session_data())
    try:
        JwtToken.objects.filter(session_data=json_data).update(session_data=json_data)
        return True
    except Exception as e:
        logger.error(f"Error updating session data: {e}")
        return False
    

class CustomAuthenticationBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, user_type=None, **kwargs):
        try:
            model_path = get_model_path(user_type)
            if model_path is None:
                return None
                        
            user_model = django_apps.get_model(model_path, require_ready=False)

            user = user_model.objects.get(
                Q(
                    Q(email=username, is_email_verified=True) |
                    Q(phone=username) |
                    Q(username=username)
                )
            )

            # if password != None and user.password != None :
            #     if user.check_password(password):
            #         return user

            if password != None :
                if user.password != None and user.check_password(password):
                    return user


                if user.otp == password:
                    user.otp = get_random_string(4, allowed_chars=string.digits)
                    if not user.is_phone_verified:
                        user.is_phone_verified = True
                    user.save()
                    return user

            return None
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    


    def check_user_type(user_type):
        for model in settings.USER_MODELS:
            if model.get('type') == user_type:
                return True
        return False

    def _get_group_permissions(self, user_obj):
        user_type = type(user_obj)
        print("_get_group_permissions--------------", user_type.__name__)
        model_name = user_type.__name__
        model_path  = get_model_path(model_name)
        
        if model_path is None:
            return set()
        
        user_model = django_apps.get_model(model_path, require_ready=False)
 
        user_groups_field = user_model._meta.get_field("groups")
        user_groups_query = "group__%s" % user_groups_field.related_query_name()
 
        return Permission.objects.filter(**{user_groups_query: user_obj})
    
    def authenticate_header(self, request):
        return 'Bearer '



class JWTAuthentication(authentication.BaseAuthentication):
    
    def authenticate(self, request):
        access_token = request.META.get('HTTP_AUTHORIZATION')

        if access_token is None:
            logger.warning('Token not provided in the request headers.')
            return None

        access_token = self.get_the_token_from_header(access_token)

        try:
            payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=['HS256'])

        except jwt.ExpiredSignatureError:
            logger.error('Token has expired.')
            raise AuthenticationFailed('Token has expired')
        except jwt.InvalidSignatureError:
            logger.error('Invalid Signature.')
            raise AuthenticationFailed('Invalid Signature')
        except jwt.DecodeError:
            logger.error('Error decoding the token.')
            raise AuthenticationFailed('Error decoding the token')
        except Exception as e:
            logger.error(f'Unexpected error decoding token: {e}')
            raise AuthenticationFailed('Error decoding the token')
        
        try:
            jwt_obj = JwtToken.objects.get(access_token=access_token)
            json_dict = json.loads(jwt_obj.session_data)
            # request_cfg.session_data = json_dict
            set_session_data(json_dict)
        except Exception as e:
            logger.error('Token has expired.')
            raise AuthenticationFailed('Token has expired')
        
        user_identifier = payload.get('u_i')
        user_type = payload.get('u_t')

        if user_identifier is None:
            logger.error('User identifier not found in JWT.')
            raise AuthenticationFailed('User identifier not found in JWT')

        model_path = get_model_path(user_type)

        if model_path is None:
            return None
                    
        user_model = django_apps.get_model(model_path, require_ready=False)

        user = user_model.objects.filter(id=user_identifier).first()

        if user is None:
            logger.error('User not found.')
            raise AuthenticationFailed('User not found')
        else:
            # request_cfg.user = user
            set_user(user)

        # request_cfg.mydb = request_cfg.session_data.get('selected_db', None)   

        return user, payload

     
    def authenticate_header(self, request):
        return 'Bearer '
  
    def get_the_token_from_header(self, token):
        if not token.startswith('Bearer '):
            logger.error('Authorization header must start with "Bearer".')
            raise AuthenticationFailed('Authorization header must start with "Bearer".')
        token = token.replace('Bearer ', '').strip()
        return token
    
    
   
