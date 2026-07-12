from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage
from django.core.files.storage import FileSystemStorage



# class StaticStorage(S3Boto3Storage):
#     location = settings.AWS_STATIC_LOCATION

class PublicMediaStorage(S3Boto3Storage):
    
    if settings.USE_S3:
        location = settings.AWS_PUBLIC_MEDIA_LOCATION
        file_overwrite = False
        default_acl = 'public-read'
    else:
        pass

    # custom_domain = settings.WHEELSMART_DOMAIN

class PrivateMediaStorage(S3Boto3Storage):
    if settings.USE_S3:
        location = settings.AWS_PRIVATE_MEDIA_LOCATION
        default_acl = 'private'
        file_overwrite = False
        custom_domain = False
    else:
        pass

class DBBackupMediaStorage(S3Boto3Storage):
    if settings.USE_S3:
        location = settings.AWS_DBBACKUP_MEDIA_LOCATION
        default_acl = 'private'
        file_overwrite = False
        custom_domain = False
    else:
        pass