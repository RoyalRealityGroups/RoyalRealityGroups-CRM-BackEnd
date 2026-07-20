import os
import datetime
from pathlib import Path

from django.core.management.utils import get_random_secret_key

from dotenv import load_dotenv

# Load .env file from the backend directory (parent of settings.py)
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=env_path)


SAFE_MODE = os.getenv("SAFE_MODE", "False") == "True"

DYNAMICS_SAFE_MODE = SAFE_MODE or os.getenv("DYNAMICS_SAFE_MODE", "False") == "True"

FLOW_SAFE_MODE = SAFE_MODE or os.getenv("FLOW_SAFE_MODE", "False") == "True"

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", get_random_secret_key())


# SECURITY WARNING: don't run with debug turned on in production!

DEBUG = os.getenv("DEBUG", "False") == "True"

# Enforce SECRET_KEY in production
if not DEBUG and not os.getenv("DJANGO_SECRET_KEY"):
    raise Exception("DJANGO_SECRET_KEY environment variable must be set in production")


URL_SCHEMA = os.getenv('URL_SCHEMA', "http")
ALLOWED_HOSTS = ['*']
CSRF_TRUSTED_ORIGINS = [ URL_SCHEMA +'://'+host for host in ALLOWED_HOSTS ] + [
    'http://localhost:5174',
    'http://127.0.0.1:5174',
]

GLOBAL_API_URL = os.getenv("GLOBAL_API_URL", URL_SCHEMA + '://' + ALLOWED_HOSTS[0])
# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'dynamic_preferences',

    'rest_framework_simplejwt.token_blacklist',
    'rest_framework',
    'drf_spectacular',
    'django_filters',
    'dbbackup',
    'import_export',
    'imagekit',
    'django_admin_listfilter_dropdown',
    'rangefilter',
    'django_crontab',
    # 'admin_auto_filters',  # Temporarily disabled - not available on PyPI
    'Core.Users',
    'Core.System',
    'Core.Reports',
    'Users',
    'Masters',
    'Sales',
    'Lead',
    'Dispatch',
    'Invoice',
    'Receipts',
    'Delivery',
    # 'advanced_filters',
    'thirdparty',
    'General',
    'dashboards',
    # Phase 1 - New apps
    'Inventory',
    'Booking',
    'Documents',
    'RealEstateReports',
    'SiteVisit',
]


USER_MODELS = [
                {
                    'name': 'User',
                    'type': 'User',
                    'model': 'Users.User',
                }
            ]


AUTH_USER_MODEL = 'Users.User'



REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'Core.Core.authentication.Authentication.JWTAuthentication',
    ),
    'NON_FIELD_ERRORS_KEY': 'error',
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
        'Core.Core.permissions.permissions.AllPermissions',
    ],
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PAGINATION_CLASS': 'Core.Core.pagination.Paginations.StandardResultsSetPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'EXCEPTION_HANDLER': 'Core.exceptions.custom_exception_handler',
    # 'DEFAULT_THROTTLE_CLASSES': [
    #     'rest_framework.throttling.AnonRateThrottle',
    #     'rest_framework.throttling.UserRateThrottle'
    # ],
    # 'DEFAULT_THROTTLE_RATES': {
    #     'anon': '100/hour',
    #     'user': '1000/hour'
    # }
}


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.gzip.GZipMiddleware',  # Response compression
    'Core.Core.middleware.cache_headers.CacheHeadersMiddleware',  # HTTP cache headers
    'Core.Core.middleware.request_validation.RequestValidationMiddleware',  # Request validation
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'Core.Core.middleware.csrf_exempt_api.DisableCSRFForAPIMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # 'Common.middleware.SqlPrintingMiddleware',
    'Core.Core.middleware.allpermissions.allPermissionsMiddleware',
    'Core.Core.middleware.error.ErrorMiddleware',
    # 'Common.middleware.TimezoneMiddleware',
    # 'Core.Core.middleware.query_monitor.QueryMonitorMiddleware',  # Query monitoring
]

# Security Settings
if not DEBUG and URL_SCHEMA.lower() == 'https':
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
else:
    # Allow local HTTP API usage (e.g. localhost:8011) without forced HTTPS redirects.
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# File Upload Limits
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB


AUTHENTICATION_BACKENDS = [
    # 'django.contrib.auth.backends.ModelBackend',
    'Core.Core.authentication.Authentication.CustomAuthenticationBackend',
    # 'django.contrib.auth.backends.ModelBackend',
    # 'Users.auth_backends.UserTypeBackend',
    # 'Users.auth_backends.OrganizerAuthenticationBackend',
]


# AUTHENTICATION_BACKENDS = ('Common.Authentication.CustomAuthenticationBackend',)

GENERAL_APP_LABEL = 'General'

INSTALLED_APPS += [ 'corsheaders',]

if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    try:
        gzip_index = MIDDLEWARE.index('django.middleware.gzip.GZipMiddleware')
        MIDDLEWARE.insert(gzip_index + 1, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    except ValueError:
        MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1', 'localhost']

# CORS Configuration
# NOTE: Explicitly allow all origins per deployment request.
CORS_ALLOW_ALL_ORIGINS = True
CORS_ORIGIN_ALLOW_ALL = True  # backward-compatible alias
CORS_ALLOW_CREDENTIALS = True
CORS_URLS_REGEX = r"^/(api|media)/.*$"

# CORS_ORIGIN_WHITELIST = (
#   'http://localhost:8000',
# )

ROOT_URLCONF = 'BaseProject.urls'

APPEND_SLASH = True

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'build'),os.path.join('templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'dynamic_preferences.processors.global_preferences',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'libraries': {
                'common_tags': 'Core.Core.filters.TemplateFilters',
            },
        },
    },
]

WSGI_APPLICATION = 'BaseProject.wsgi.application'

# Validate required database configuration for all environments
if os.getenv("DB_NAME", None) is None:
    raise Exception("DB_NAME environment variable must be set")
if os.getenv("DB_USER", None) is None:
    raise Exception("DB_USER environment variable must be set")
if os.getenv("DB_PASS", None) is None:
    raise Exception("DB_PASS environment variable must be set")

DATABASES = {
    

    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000 -c idle_in_transaction_session_timeout=60000',
        },
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASS'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,
        'TEST':{
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'test_db.sqlite3'),
        }
    },
}

# Redis Cache Configuration
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache" if os.getenv("USE_REDIS", "False") == "True" else "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://127.0.0.1:6379/1") if os.getenv("USE_REDIS", "False") == "True" else "unique-snowflake",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 50,
                "retry_on_timeout": True,
            },
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
        } if os.getenv("USE_REDIS", "False") == "True" else {},
        "KEY_PREFIX": "sales_app",
        "TIMEOUT": 300,  # 5 minutes default
    }
}

# Session cache configuration (optional but recommended)
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

CACHE_TIME_OUT_ONE_YEAR = 60 * 60 * 24 * 365
CACHE_TIME_OUT_ONE_MONTH = 60 * 60 * 24 * 30

# GZip Compression Settings
GZIP_COMPRESSION_LEVEL = 6  # 1-9, higher = more compression but slower

import sys
if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test_db.sqlite3'
    }


# Token lifetime: 24 hours for access, 30 days for refresh in production
ACCESS_TOKEN_LIFETIME = datetime.timedelta(hours=24) if not DEBUG else datetime.timedelta(days=365)
REFRESH_TOKEN_LIFETIME = datetime.timedelta(days=30) if not DEBUG else datetime.timedelta(days=365)


LOGIN_URL = '/admin/login/' 
LOGOUT_URL = '/admin/logout/'

SPECTACULAR_SETTINGS = {
    'TITLE': 'BaseProject API',
    'DESCRIPTION': 'BaseProject API',
    'VERSION': '1.0.0',
    'LICENSE': {'name': 'Closed License'},
    'CONTACT': {'email': 'admin@gmail.com'},
    'SERVE_INCLUDE_SCHEMA': False,    # /schema/ endpoint is not  included in the generated schema.
    'SECURITY': [{'Bearer': []}],

    'SWAGGER_UI_SETTINGS': {
        'docExpansion': 'none',
        'deepLinking': True,
        'defaultModelRendering': 'model',
        'displayRequestDuration': True,
        'filter': True,
        'persistAuthorization': False,
        "displayOperationId": True,
    },

    'SERVERS': [
        {'url': '/', 'description': '(HTTP or HTTPS)'},
    ],

    'SERVE_AUTHENTICATION': ['rest_framework.authentication.SessionAuthentication'],

    'SERVE_PERMISSIONS': ['rest_framework.permissions.IsAuthenticated'],

    "EXTENSIONS_INFO": {
        "x-login-url": "/api/login/",
        "x-logout-url": "/api/logout/",
    }, 

}


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# AUTHENTICATION_BACKENDS = ('Common.Authentication.CustomAuthenticationBackend',)

SINGLE_MOBILE_DEVICE_PER_USER = False

# IMPORT_EXPORT_USE_TRANSACTIONS = True 

# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

# TIME_ZONE = 'UTC'
TIME_ZONE = 'Asia/Kolkata'



USE_I18N = True

USE_TZ = True

USE_GLOBAL_URL = True


STATICFILES_DIRS = [
    path for path in [
        os.path.join(BASE_DIR, 'static_assets'),
        os.path.join(BASE_DIR, 'build/static'),
    ] if os.path.isdir(path)
]
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

DBBACKUP_FILENAME_TEMPLATE = 'backup-{datetime}.sql'
BACKUP_DIRECTORY = r'db/backup'
DBBACKUP_STORAGE_OPTIONS = {'location': BACKUP_DIRECTORY}

# DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
# DBBACKUP_STORAGE_OPTIONS = {'location': os.path.join(BASE_DIR, 'media\\backup')}


USE_S3 = os.getenv('USE_S3', 'False') == 'True'


if USE_S3:
    # AWS S3 Configrations
    INSTALLED_APPS += ['storages']
    
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
    
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY or not AWS_STORAGE_BUCKET_NAME:
        raise Exception("AWS credentials must be set when USE_S3=True")
    AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME

    # ap-south-1
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }

    AWS_S3_REGION_NAME = 'ap-south-1' #change to your region
    AWS_S3_SIGNATURE_VERSION = 's3v4'

    AWS_STATIC_LOCATION = 'static'
    # STATICFILES_STORAGE = 'Common.storage_backends.StaticStorage'
    # STATIC_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, AWS_STATIC_LOCATION)
    STATIC_URL = '/static/'

    AWS_PUBLIC_MEDIA_LOCATION = 'media/public'
    PUBLIC_FILE_STORAGE = 'Common.storage_backends.PublicMediaStorage'

    AWS_PRIVATE_MEDIA_LOCATION = 'media'
    PRIVATE_FILE_STORAGE = 'Common.storage_backends.PrivateMediaStorage'

    STORAGES = {
        "default": {
            "BACKEND": PRIVATE_FILE_STORAGE,
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }

    MEDIA_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, AWS_PRIVATE_MEDIA_LOCATION)

    # IMAGEKIT_DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

    # STATICFILES_DIRS = [
    #     os.path.join(BASE_DIR, 'static'),
    # ]
    
    AWS_DBBACKUP_MEDIA_LOCATION = r'db/backups/'
    DBBACKUP_STORAGE = 'Common.storage_backends.DBBackupStorage'
    # DBBACKUP_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    DBBACKUP_STORAGE_OPTIONS = {
        'access_key': AWS_ACCESS_KEY_ID,
        'secret_key': AWS_SECRET_ACCESS_KEY,
        'bucket_name': AWS_STORAGE_BUCKET_NAME,
        'location': AWS_DBBACKUP_MEDIA_LOCATION,
        'encrypt_key': True,  # Enable encryption
    }
else:
    # STATIC IN LOCALS
    STATIC_URL = '/static/'

    MEDIA_ROOT =  os.path.join(BASE_DIR, 'media')
    MEDIA_URL = '/media/'

    DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
    BACKUP_FILE_NAME = 'backup-{datetime}.sql'
    BACKUP_FILE_PATH = os.path.join(BACKUP_DIRECTORY, BACKUP_FILE_NAME)
    DBBACKUP_STORAGE_OPTIONS = {'location': BACKUP_DIRECTORY}

    def generate_backup_filename():
        timestamp = datetime.datetime.now().strftime('%d/%b/%Y %H:%M:%S')
        return DBBACKUP_FILENAME_TEMPLATE.format(datetime=timestamp)

    if __name__ == "__main__":
        backup_filename = generate_backup_filename()


# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CRONJOBS = [
    # ('*/5 * * * *', 'myapp.cron.other_scheduled_job', ['arg1', 'arg2'], {'verbose': 0}), # To call a function
]

LOG_DIR = os.path.join(BASE_DIR, '.log')
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
    },
    'handlers': {
        'logfile': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': ".log/DEBUG_LogFile.log",
        },
        'logfile_info':{
            'level':'INFO',
            'class':'logging.FileHandler',
            'formatter': 'standard',
            'filename': ".log/INFO_LogFile.log",
        },
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        # 'level':'DEBUG' if DEBUG else 'WARNING',
        'class':'logging.FileHandler',
        'filename': ".log/root_logfile.log",
        'maxBytes': 1024 * 1024 * 10, #Max 10MB
        'backupCount': 3,
        'formatter': 'standard',
    },
    'loggers': {
        'django': {
            'handlers':['console'],
            'propagate': True,
            'level':'WARN',
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'Common': {
            'level':'DEBUG' if DEBUG else 'WARNING',
            'handlers': ['logfile', 'console'],
        },
        'thirdparty': {
            'level':'INFO',
            'handlers': ['logfile_info', 'console'],
        },
    }
}


# IOServer (Socket.IO) optional configuration. Leave IO_SERVER_URL empty to disable.
IO_SERVER_URL = os.getenv('IO_SERVER_URL', '').strip()
IO_SECRET = os.getenv('IO_SECRET')

# Enforce IO_SECRET only when IOServer is enabled in production
if not DEBUG and IO_SERVER_URL and not IO_SECRET:
    raise Exception("IO_SECRET environment variable must be set when IO_SERVER_URL is configured in production")



FOCUS_SYNC_ON = os.getenv('FOCUS_SYNC_ON', False)
FOCUS_BASEURL = os.getenv('FOCUS_BASEURL', None)
FOCUS_COMPANY_CODE = os.getenv('FOCUS_COMPANY_CODE', None)
FOCUS_USERNAME = os.getenv('FOCUS_USERNAME', None)
FOCUS_PASSWORD = os.getenv('FOCUS_PASSWORD', None)

FOCUS_API2_BASEURL = os.getenv('FOCUS_API2_BASEURL', None)
FOCUS_API2_TOKEN = os.getenv('FOCUS_API2_TOKEN', None)
