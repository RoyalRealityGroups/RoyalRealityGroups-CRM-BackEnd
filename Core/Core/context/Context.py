import threading
import json
import logging


logger = logging.getLogger(__name__)

request_cfg = threading.local()
request_cfg.session_data = {}
request_cfg.session_id = ''
request_cfg.user = None
request_cfg.mydb = None



def get_user():
    return getattr(request_cfg, 'user', None)


def set_user(user):
    request_cfg.user = user


def get_session_data():
    return request_cfg.session_data


def set_session_data(json_dict):
    request_cfg.session_data = json_dict


def get_session(key=None, default=None):
    return request_cfg.session_data.get(key, default)


def set_context_session(key, value):
    request_cfg.session_data[key] = value
