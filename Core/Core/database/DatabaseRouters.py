from email.policy import default
import threading
from django.http import Http404
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

 

# class SchemaRouter(object):

#     def db_for_read(self, model, **hints):
#         if model._meta.app_label == 'Attendance' and 'attendance' in settings.DATABASES:
#             return 'attendance'
#         else:
#             return 'default'

#     def db_for_write(self, model, **hints):
#         if model._meta.app_label == 'Attendance' and 'attendance' in settings.DATABASES:
#             return 'attendance'
#         else:
#             return 'default'

    
#     def allow_migrate(self, db, app_label, model_name=None, **hints):
        
#         if db == 'attendance' and app_label != 'Attendance':
#             return False

#         elif app_label == 'Attendance' and db == 'default':
#             return False

#         return True

## SETTINGS

# DATABASE_ROUTERS = [
#     'Common.DatabaseRouters.SchemaRouter',
# ]

# 'attendance': {
#     'ENGINE': 'django.db.backends.postgresql',
#     'OPTIONS': {
#         'options': '-c search_path=django,attendance'
#     },
#     'NAME': 'Wheelsmart',
#     'USER': 'postgres',
#     'PASSWORD': 'absolin123',
#     'HOST': '127.0.0.1',
#     'PORT': '5432',
# },