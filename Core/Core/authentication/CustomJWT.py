import jwt
import json
from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone

from django.apps import apps as django_apps

import logging
from Core.Core.utils.utils import get_model_path
from Core.Users.models import JwtToken
logger = logging.getLogger(__name__)


def generate_access_token(user_identifier, user_type=None,):
    expiration_time = settings.ACCESS_TOKEN_LIFETIME
    access_expiring_on = (timezone.now() + expiration_time)
    user_identifier = str(user_identifier)
    payload = {
        'u_i': user_identifier,
        'u_t': user_type,
        'exp': int(access_expiring_on.timestamp()),
        'iat': timezone.now().timestamp(),
    }
    access_token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

    return access_token, access_expiring_on


def generate_refresh_token(user_identifier, user_type=None):
    expiration_time = settings.REFRESH_TOKEN_LIFETIME
    refresh_expiring_on = (timezone.now() + expiration_time)
    user_identifier = str(user_identifier)
    refresh_token_payload = {
        'user_identifier': user_identifier,  # Ensure this matches the actual field
        'user_type':user_type,
        'exp': int(refresh_expiring_on.timestamp()),
        'iat': timezone.now().timestamp(),
    }
    refresh_token = jwt.encode(refresh_token_payload, settings.SECRET_KEY, algorithm='HS256')
  
    return refresh_token, refresh_expiring_on


def create_tokens(user, user_type=None, session_data=None):
    
    access_token, access_expiring_on = generate_access_token(user.id, user_type )
    refresh_token, refresh_expiring_on = generate_refresh_token(user.id, user_type )
    session_data_json = json.dumps(session_data)

    try:
        JwtToken.objects.create(user_identifier= user.id, user_type= user_type, access_token=access_token, refresh_token= refresh_token,  session_data=session_data_json,access_expiring_on = access_expiring_on, refresh_expiring_on = refresh_expiring_on )
        logger.info("Tokens saved to the database")
    except Exception as e:
        logger.error(f"Error saving Tokens to the database: {e}")
        # raise Exception("")

    return {
        'refresh': refresh_token,
        'access': access_token
    }


def update_access_token(refresh_token):
    
    try:
        jwt_obj = JwtToken.objects.get(refresh_token= refresh_token)
    except:
        raise Exception('Invalid Refresh Token')


    access_token, access_expiring_on = generate_access_token(jwt_obj.user_identifier, jwt_obj.user_type)
    # refresh_token = generate_refresh_token(user.username, user_type )

    try:
        JwtToken.objects.filter(refresh_token= refresh_token).update(access_token= access_token,access_expiring_on = access_expiring_on)
        logger.info("Tokens saved to the database")
    except Exception as e:
        logger.error(f"Error saving Tokens to the database: {e}")

    model_path = get_model_path(jwt_obj.user_type)

    if model_path is None:
        raise Exception('User not found')
                
    user_model = django_apps.get_model(model_path, require_ready=False)

    user = user_model.objects.filter(id=jwt_obj.user_identifier).first()

    if user is None:
        logger.error('User not found.')
        raise Exception('User not found')
    

    return {
        'access': access_token,
        'user_identifier': jwt_obj.user_identifier, 
        'user_type': jwt_obj.user_type
    }

