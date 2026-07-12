import mimetypes
import sys
import os
import re
import json
import uuid
import threading
import logging
import boto3
from django.apps import apps
import requests
import urllib.request
import urllib.parse
import magic  # Install with `pip install python-magic-bin` for Windows
 
from io import BytesIO
from datetime import datetime
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.mail import EmailMessage
from django.conf import settings
from django.core.mail.backends.smtp import EmailBackend
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from importlib import import_module
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont
from django.core.files.storage import default_storage
from django.db import models


from admin_auto_filters.filters import AutocompleteFilter
from rest_framework.exceptions import ValidationError





log = logging.getLogger(__name__)



def get_model_path(user_type):
    if user_type is None: ## applied only for the admin login
        return settings.AUTH_USER_MODEL
    
    for model in settings.USER_MODELS:
        if model.get('type') == user_type:
            return model.get('model')
    
    return None


# class EmailThread(threading.Thread):

#     def __init__(self, email):
#         self.email = email
#         threading.Thread.__init__(self)

#     def run(self):
#         print('entered run')
#         # send_mail(self.data.subject, '', '', self.data.to, html_message=self.data.body)
#         self.email.send()


# class SMSThread(threading.Thread):

#     def __init__(self, data):
#         self.data = data
#         threading.Thread.__init__(self)

#     def run(self):
#         GLOBAL_VARS = global_preferences_registry.manager().all()
#         if GLOBAL_VARS['SMS__ENABLE_SMS'] == 'T':
#             data =  urllib.parse.urlencode({GLOBAL_VARS['SMS__MSG_VAR']: self.data['message'], GLOBAL_VARS['SMS__NUMBER_VAR']:self.data['to_phone']})
#             # data = data.encode('utf-8')
#             # request = urllib.request.Request("http://text.justsms.co.in/vendorsms/pushsms.aspx?")
#             # request = urllib.request.Request("http://164.52.195.161/API/SendMsg.aspx?uname=20160715&pass=srilalitha&send=SLEIPL&dest=7382766529&msg=Hi%20Gopi%0AREGARDS%2C%0ASRI%20LALITHA%20ENTERPRISES%20INDUSTRIES%20PVT%20LTD.%2C&priority=1")
#             # request = urllib.request.Request("http://164.52.195.161/API/SendMsg.aspx?uname=20160715&pass=srilalitha&send=SLEIPL&"+msg+"&dest="+number)
#             request = urllib.request.Request(GLOBAL_VARS['SMS__URL'] + data )
#             f = urllib.request.urlopen(request)
#             fr = f.read()
#             return(fr)

class IOThread(threading.Thread):

    def __init__(self, url, data):
        self.url = url
        self.data = data
        threading.Thread.__init__(self)

    def run(self):
        
        IO_SERVER_URL = os.getenv("IO_SERVER_URL", default="http://localhost:3000/")
        IO_ENABLE = os.getenv("IO_ENABLE", default="True")
        IO_SECRET = os.getenv("IO_SECRET", default="")
        if IO_SERVER_URL != None and IO_ENABLE == "True":
            data = json.dumps(self.data).encode('utf-8')
            response = requests.request("POST",IO_SERVER_URL + self.url, data=data, headers={ 'Content-Type': 'application/json', 'authorization': IO_SECRET })
            # f = urllib.request.urlopen(request)
            fr = response.text
            return fr
        else:
            return None


# class Util:
#     @staticmethod
#     def send_email(data, attachments=None):
#         log.info("======================================EMAIL======================================")
#         log.info("subject: {subject}, body: {body}, to: {to}".format(subject=data['email_subject'], body=data['email_body'], to=data['to_email']))
#         log.info("=================================================================================")

#         GLOBAL_VARS = global_preferences_registry.manager().all()
#         backend = EmailBackend(host=GLOBAL_VARS['SMTP__HOST'], port=GLOBAL_VARS['SMTP__PORT'], username=GLOBAL_VARS['SMTP__USER'], 
#                        password=GLOBAL_VARS['SMTP__PASSWORD'], use_tls=GLOBAL_VARS['SMTP__USE_TLS'])

#         email = EmailMessage(subject=data['email_subject'], body=data['email_body'], to=[data['to_email']], connection=backend  )

#         if attachments:
#             for attachment in attachments:
#                 if isinstance(attachment, tuple):

#                     file_name, file_data, content_type = attachment

#                     log.info(f"Attaching file: {file_name}")
#                     log.info(f"Content type: {content_type}")
#                     log.info(f"File data length: {len(file_data)} bytes")
#                     try:

#                         email.attach(file_name, file_data, content_type)
                        
#                         log.info(f"File {file_name} attached successfully")
#                     except Exception as e:
#                         log.error(f"Error attaching file {file_name}: {e}")
#                 else:
#                     log.warning(f"Invalid attachment format: {attachment}")

#         EmailThread(email).start()

#     @staticmethod
#     def send_sms(data):
#         log.info("======================================SMS======================================")
#         log.info(""+data['to_phone']+" "+data['message'])
#         log.info("=================================================================================")
#         SMSThread(data).start()
        
    # @staticmethod
    # def send_live_notification(url, data):
    #     IOThread(url, data).start()
        

def doccode(model, prefix):
    lastRec = model.objects.last()
    if lastRec:
        nxtId = lastRec.id + 1
    else:
        nxtId = 1
    now = datetime.now() 

    date_time = now.strftime("%y%m%d%H%M%S%f")[:-3]
    
        
    return str(prefix) + str(date_time )


def get_request_url(request):

    if settings.USE_GLOBAL_URL:
        return settings.GLOBAL_URL
    else:
        # current_site = get_current_site(self.context['request']).domain
        baseurl = "https://" if request.is_secure() else "http://"
        baseurl += request.get_host()
        return baseurl

        
def removeDuplicates(arr):
    temp = []
    for i in range(len(arr)):
        if arr[i] not in temp:
            temp.append(arr[i])
    return temp


    
def CompressImage(selectedfile):
    name_arr = selectedfile.name.split('.')
    valid_extensions = ['jpg', 'jpeg', 'png',]
    if len(name_arr) > 1 and name_arr[-1].lower() in valid_extensions:
        if selectedfile and not isinstance(selectedfile, str):

            im = Image.open(selectedfile)

            output = BytesIO()

            # Resize/modify the image
            # im = im.resize((100, 100))

            im = im.convert('RGB')
            im.save(output, format='JPEG',
                    optimize = True,  
                    quality = 30)
            output.seek(0)
            
            # print("im",im)
            
            print("output",output)
            
            a = InMemoryUploadedFile(output, 'ImageField', "%s.jpg" % name_arr[0], 'image/jpeg',sys.getsizeof(output), None)
            # print("InMemoryUploadedFile",a)
            

            return a
        
        else:
            return selectedfile
    else:
        return selectedfile


def ac_filter(Xfield_name):
    class XFilter(AutocompleteFilter):
        title = Xfield_name.upper()
        field_name = Xfield_name
        # if hasattr(field, "verbose_name"):
        #     self.lookup_title = field.verbose_name
        # else:
        #     self.lookup_title = other_model._meta.verbose_name
    return XFilter



class Util:
    @staticmethod
    def get_preferences(preferences_code):
        try:
            from Core.System.models import Setting  
            setting = Setting.objects.filter(preferences_code=preferences_code).first()
            if setting and setting.preferences:
                return json.loads(setting.preferences)
            return {}
        except json.JSONDecodeError:
            log.error(f"Invalid JSON format for preferences_code: {preferences_code}")
            return {}
        except Exception as e:
            log.error(f"Error fetching preferences for {preferences_code}: {e}")
            return {}
        

    @staticmethod
    def send_email(data, attachments=None):
        log.info("======================================EMAIL======================================")
        log.info("subject: {subject}, body: {body}, to: {to}".format(subject=data['email_subject'], body=data['email_body'], to=data['to_email']))
        log.info("=================================================================================")

        email_config = Util.get_preferences("EMAIL_CONFIG")
        
        gateway_key = data.get('gateway')

        gateway = email_config.get(gateway_key)

        backend = EmailBackend(host=gateway.get('smtp_host'),
                               port=gateway.get('smtp_port'),
                               username=gateway.get('smtp_user'),
                               password=gateway.get('smtp_password'),
                               use_tls=gateway.get('use_tls', True))
 
        from_email = gateway.get('from_email') or gateway.get('smtp_user')
       
        email = EmailMessage(subject=data['email_subject'], body=data['email_body'], from_email=from_email, to=[data['to_email']],
            connection=backend
        )
 
        if attachments:
            for attachment in attachments:
                if isinstance(attachment, tuple):
                    file_name, file_data, content_type = attachment
                    log.info(f"Attaching file: {file_name}")
                    try:
                        email.attach(file_name, file_data, content_type)
                        log.info(f"File {file_name} attached successfully")
                    except Exception as e:
                        log.error(f"Error attaching file {file_name}: {e}")
                else:
                    log.warning(f"Invalid attachment format: {attachment}")

        EmailThread(email).start()


  

    @staticmethod
    def send_sms(data):
        log.info("==================== SMS SENDING ====================")
        log.info(f"Sending SMS to {data.get('to_phone')} with message: {data.get('message')}")
        log.info("======================================================")

        sms_config = Util.get_preferences("SMS_CONFIG")
        gateway_key = data.get('gateway')

        gateway = sms_config.get(gateway_key)
        if not gateway:
            log.error(f"Gateway '{gateway_key}' not found in SMS configuration")
            return
        
        method = gateway.get('method')
        if not method:
            log.error("HTTP method is missing or None in SMS configuration")
            raise ValueError("HTTP method must be specified in SMS configuration")

        url = gateway.get('url')
        if not url:
            log.error("Invalid SMS configuration: missing 'url'")
            return

        # api_key = gateway.get('api_key')
        headers = gateway.get('headers', {})
        url_params = gateway.get('url_params', {})
        body_params = gateway.get('body_params', {})
        phone_location = gateway.get('phone_location', 'url')
        message_location = gateway.get('message_location', 'body')
        phn_variable = gateway.get('phn_variable', 'number')
        msg_variable = gateway.get('msg_variable', 'message')
        body_format = gateway.get('body_format', 'json')

        # Add phone number and message based on their location

        if phone_location == 'url':
            url_params[phn_variable] = data.get('to_phone')
        elif phone_location == 'header':
            headers[phn_variable] = data.get('to_phone')
        elif phone_location == 'body':
            body_params[phn_variable] = data.get('to_phone')

        if message_location == 'url':
            url_params[msg_variable] = data.get('message')
        elif message_location == 'header':
            headers[msg_variable] = data.get('message')
        elif message_location == 'body':
            body_params[msg_variable] = data.get('message')

        # Prepare body data based on format
        if body_format == 'json':
            body_data = json.dumps(body_params).encode('utf-8')
        elif body_format == 'form-data':
            boundary = uuid.uuid4().hex
            body_data = ''
            for key, value in body_params.items():
                body_data += f"--{boundary}\r\n"
                body_data += f'Content-Disposition: form-data; name="{key}"\r\n\r\n'
                body_data += f"{value}\r\n"
            body_data += f"--{boundary}--\r\n"
            body_data = body_data.encode('utf-8')
            headers['Content-Type'] = f'multipart/form-data; boundary={boundary}'
        elif body_format == 'www-form-urlencoded':
            body_data = urllib.parse.urlencode(body_params).encode('utf-8')
        elif body_format == 'xml':
            xml_elements = ''.join(f"<{k}>{v}</{k}>" for k, v in body_params.items())
            body_data = f"<?xml version='1.0' encoding='UTF-8'?><root>{xml_elements}</root>".encode('utf-8')
            headers['Content-Type'] = 'application/xml'
        else:
            log.error("Unsupported body format")
            return

        # Construct full URL
        # full_url = f"{url}?{urllib.parse.urlencode(url_params)}"
        # request = urllib.request.Request(full_url, data=body_data, headers=headers, method=gateway.get('method', 'POST'))

        full_url = f"{url}?{urllib.parse.urlencode(url_params)}"
        log.info(f"Full URL: {full_url}")
        log.info(f"Headers: {headers}")
        log.info(f"Body: {body_data.decode('utf-8')}")
        log.info(f"HTTP Method: {method}")

        try:
            request = urllib.request.Request(full_url, data=body_data, headers=headers, method=method)
            with urllib.request.urlopen(request) as response:
                response_data = response.read().decode('utf-8')
                log.info(f"SMS Response: {response_data}")
        except urllib.error.HTTPError as e:
            log.error(f"HTTP Error: {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            log.error(f"URL Error: {e.reason}")
        except Exception as e:
            log.error(f"Unexpected error: {e}")

        log.info("======================================================")

        SMSThread(data).start()


class EmailThread(threading.Thread):
    def __init__(self, email):
        super().__init__()
        self.email = email

    def run(self):
        self.email.send()

class SMSThread(threading.Thread):
    def __init__(self, data):
        super().__init__()
        self.data = data

    def run(self):
        Util.send_sms(self.data)




def create_thumbnail(file_instance):
    try:
        # Check MIME type to confirm it's an image
        mime_type, _ = mimetypes.guess_type(file_instance.name)
        if mime_type and mime_type.startswith('image'):
            try:
                image = Image.open(file_instance)
                image.thumbnail((150, 150))  # Resize to thumbnail size

                thumb_io = BytesIO()
                image.save(thumb_io, format=image.format)
                thumb_file = ContentFile(thumb_io.getvalue(), name=f"t_{file_instance.name}")
                return thumb_file
            except Exception as e:
                # Log the exception for debugging
                print(f"Error processing image file: {e}")
                pass
        
        # Fallback to placeholder for non-image files or errors
        # return create_placeholder_thumbnail(file_instance)
        return None
    except Exception as e:
        print(f"Exception in create_thumbnail: {e}")
        return None
    

def create_placeholder_thumbnail(file_instance):
    try:
        # Determine the file extension (for file type, e.g., PDF, CSV)
        file_extension = os.path.splitext(file_instance.name)[1].lower().strip('.')

        # Create a white image (150x150 px)
        placeholder_image = Image.new('RGB', (150, 150), color='white')
        draw = ImageDraw.Draw(placeholder_image)

        # Set up font for writing text
        try:
            font = ImageFont.truetype("arial.ttf", 18)  # Try to use Arial font
        except IOError:
            font = ImageFont.load_default()  # Fallback to default font

        # Write the file extension in uppercase on the placeholder image
        text = f"{file_extension.upper()}"

        # Get the bounding box of the text
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]

        # Position the text in the center of the image
        position = ((150 - text_width) // 2, (150 - text_height) // 2)
        draw.text(position, text, fill="black", font=font)

        # Save the placeholder image to a BytesIO object
        thumb_io = BytesIO()
        placeholder_image.save(thumb_io, format='PNG')
        thumb_io.seek(0)

        # Create a ContentFile for the thumbnail with a .png extension
        thumb_file = ContentFile(thumb_io.getvalue(), name=f"thumb_{file_instance.name}.png")
        return thumb_file
    except Exception as e:
        print(f"Error generating placeholder thumbnail: {e}")
        return None
    
       
        
def copy_file(s3, source_key, destination_key):
    print('------source_key', source_key)
    print('------destination_key', destination_key)

    if s3:
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )

        # Validate if source key exists
        try:
            s3.head_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=source_key)
        except Exception as e:
            print('------Exception', e)
            return {"success": False, "message": f"Source key '{source_key}' does not exist in the bucket.{e}"}

        try:
            s3.copy_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                CopySource={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': source_key},
                Key=destination_key,
            )
            print('source_key:', source_key)
            print('destination_key:', destination_key)
            return {"success": True, "message": f"File copied from {source_key} to {destination_key}"}
        except Exception as e:
            print('------Exception', e)
            return {"success": False, "message": f"Error copying file in S3: {str(e)}"}
    else:
        try:
            with default_storage.open(source_key, 'rb') as source_file:
                default_storage.save(destination_key, source_file)
            return {"success": True, "message": f"File copied from {source_key} to {destination_key}"}
        except Exception as e:
            print('------Exception', e)
            return {"success": False, "message": f"Error copying file locally: {str(e)}"}



def move_file(s3, source_key, destination_key):
    print('------source_key:', source_key)
    print('------destination_key:', destination_key)

    if s3:
        try:
            copy_response = copy_file(s3, source_key, destination_key)
            if not copy_response.get("success"):
                return copy_response  # Exit if copy failed

            s3 = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME,
            )

            try:
                s3.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=source_key)
                print(f"File moved from {source_key} to {destination_key}")
                return {"success": True, "message": f"File moved from {source_key} to {destination_key}"}
            except Exception as e:
                print('------Exception while deleting source key:', e)
                return {"success": False, "message": f"Error deleting source file '{source_key}' from S3: {str(e)}"}

        except Exception as e:
            print('------Exception in move_file (S3):', e)
            return {"success": False, "message": f"Error moving file in S3: {str(e)}"}

    else:
        try:
            if default_storage.exists(source_key):
                with default_storage.open(source_key, 'rb') as source_file:
                    default_storage.save(destination_key, source_file)
                try:
                    default_storage.delete(source_key)
                    print(f"File moved from {source_key} to {destination_key}")
                    return {"success": True, "message": f"File moved from {source_key} to {destination_key}"}
                except Exception as e:
                    print('------Exception while deleting source file locally:', e)
                    return {"success": False, "message": f"Error deleting source file '{source_key}' locally: {str(e)}"}
            else:
                print(f"Source file does not exist: {source_key}")
                return {"success": False, "message": f"Source file '{source_key}' does not exist locally."}
        except Exception as e:
            print('------Exception in move_file (local):', e)
            return {"success": False, "message": f"Error moving file locally: {str(e)}"}



def extract_file_metadata(file_instance):
    metadata = {}

    try:
        if not hasattr(file_instance, "name"):
            raise ValueError("Invalid file instance")

        metadata.update({
            "originalname": file_instance.name,
            "fileextension": os.path.splitext(file_instance.name)[1].lower().lstrip('.'),
            "file_size": file_instance.size,
            "filename": os.path.basename(file_instance.name),
        })

        # Get MIME type
        mime = magic.Magic(mime=True)
        metadata["mimetype"] = mime.from_buffer(file_instance.read(2048))  # Read first 2KB

        # Fallback to mimetypes
        if not metadata["mimetype"]:
            metadata["mimetype"] = mimetypes.guess_type(file_instance.name)[0] or "application/octet-stream"

        # File timestamps (only for temp files)
        if hasattr(file_instance, "temporary_file_path"):
            stats = os.stat(file_instance.temporary_file_path())
            metadata.update({
                "creation_time": timezone.make_aware(datetime.fromtimestamp(stats.st_ctime)).isoformat(),
                "last_modified": timezone.make_aware(datetime.fromtimestamp(stats.st_mtime)).isoformat(),
                "last_accessed": timezone.make_aware(datetime.fromtimestamp(stats.st_atime)).isoformat(),
            })
        else:
            metadata["creation_time"] = None

    except Exception as e:
        metadata["error"] = str(e)

    return metadata


#----------------------------------------------------------- example json for sms-------------------------------------------------------- #     

# {
#     "SMS_CONFIG": {
#         "default_gateway": {
#             "url": "https://example.com/send-sms",
#             "api_key": "your_api_key",
#             "method": "POST",
#             "headers": {
#                 "Content-Type": "application/json"
#             },
#             "url_params": {},
#             "body_params": {},
#             "phone_location": "url",       # Options: url, header, body
#             "message_location": "body",    # Options: url, header, body
#             "body_format": "json"          # Options: json, form-data, www-form-urlencoded, xml
#         },
#         "gateway_with_headers": {
#             "url": "https://example.com/sms",
#             "api_key": "your_api_key",
#             "method": "POST",
#             "headers": {
#                 "Content-Type": "application/x-www-form-urlencoded",
#                 "Authorization": "Bearer your_api_key"
#             },
#             "phone_location": "header",
#             "message_location": "header",
#             "body_format": "www-form-urlencoded"
#         },
#         "gateway_with_xml": {
#             "url": "https://example.com/send-xml-sms",
#             "api_key": "your_api_key",
#             "method": "POST",
#             "headers": {
#                 "Content-Type": "application/xml"
#             },
#             "phone_location": "body",
#             "message_location": "body",
#             "body_format": "xml"
#         }
#     }
# }


def append_to_json_file(obj):
        data_to_append = {
            "App Label": obj.get("app_label"),
            "Model Name": obj.get("model_name"),
            "Verbose Name": "",
            "Verbose Name Plural": "",
            "Fields": obj.get("fields"),  # Assumed to be already in the correct format
            "Rules": obj.get("rules", "[]"),
            "Other Attributes": obj.get("other_attributes" ,"{}")
        }

        try:
            try:
                with open('DynamicDjango/models_data/models_data.json', 'r') as f:
                    existing_data = json.load(f)
                    if not isinstance(existing_data, list):
                        existing_data = []
            except (FileNotFoundError, json.JSONDecodeError):
                existing_data = []

            existing_data.append(data_to_append)

            with open('DynamicDjango/models_data/models_data.json', 'w') as f:
                json.dump(existing_data, f, indent=4)

        except Exception as e:
            raise ValidationError(f"Error saving data to file: {str(e)}")
        

def is_valid_email(email):
    # Regular expression pattern for email validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # Check if the email matches the pattern
    if re.match(pattern, email):
        return True
    return False
        


def get_function_from_path(path: str):
    try:
        module_path, function_name = path.rsplit('.', 1)
        module = import_module(module_path)
        return getattr(module, function_name)
    except Exception as e:
        print(f"[ERROR] Unable to import function: {e}")
        return None
    
def calculate_next_run(obj):
    """
    Calculate the next run datetime for a scheduler object based on
    frequency and repeat_interval, skipping missed runs and returning
    the next future datetime.

    Supports frequencies:
      1 - Minutes
      2 - Hours
      3 - Daily
      4 - Weekly
      5 - Monthly
      6 - Yearly
      7 - Custom (uses obj.custom_interval timedelta, must be set)
      8 - One-time (runs once at start_time or last_run)
    
    Returns:
        datetime of next run or None if no next run exists.
    """

    # Validate required attributes
    if not hasattr(obj, 'frequency') or obj.frequency is None:
        return None

    now = timezone.now()
    last_run = getattr(obj, 'last_run', None) or getattr(obj, 'start_time', now)
    
    # Make sure last_run is timezone-aware
    if timezone.is_naive(last_run):
        last_run = timezone.make_aware(last_run, timezone.get_current_timezone())

    freq = obj.frequency
    interval = getattr(obj, 'repeat_interval', None)
    
    # For custom interval: we expect a timedelta object on obj.custom_interval
    custom_interval = getattr(obj, 'custom_interval', None)

    # If one-time and already run in the past (last_run <= now), no next run
    if freq == 8:
        if last_run > now:
            return last_run
        return None
    
    # For custom frequency (7), use custom_interval timedelta directly
    if freq == 7:
        if not custom_interval:
            return None
        next_run = last_run
        while next_run <= now:
            next_run += custom_interval
        return next_run

    # For other enumerated frequencies, ensure interval is a positive integer
    if not interval or interval <= 0:
        return None

    next_run = last_run

    # Loop to skip any missed executions and find the next future run
    while next_run <= now:
        if freq == 1:  # Minutes
            next_run += timezone.timedelta(minutes=interval)
        elif freq == 2:  # Hours
            next_run += timezone.timedelta(hours=interval)
        elif freq == 3:  # Daily
            next_run += timezone.timedelta(days=interval)
        elif freq == 4:  # Weekly
            next_run += timezone.timedelta(weeks=interval)
        elif freq == 5:  # Monthly
            next_run += relativedelta(months=interval)
        elif freq == 6:  # Yearly
            next_run += relativedelta(years=interval)
        else:
            # Unknown frequency
            return None

    return next_run


def user_by_type_id(type, identifier):
    # Validate input parameters
    if not type or not identifier:
        log.warning("Invalid 'type' or 'identifier' provided.")
        return None

    try:
        # Get model path and retrieve model class
        model_path = get_model_path(type)
        model_class = apps.get_model(model_path)
        # Query and return the user instance
        return model_class.objects.filter(id=identifier).first()
        
    except Exception as e:
        log.error(f"Error fetching user by type '{type}' and identifier '{identifier}': {e}")
        return None
    
def get_model_fields(model_class,prefix='',current_depth=1,max_depth=4,visited_models=None,flatten=False):

    if visited_models is None:
        visited_models = set()

    if model_class in visited_models or current_depth > max_depth:
        return []

    visited_models.add(model_class)

    fields = []

    for field in model_class._meta.get_fields():
        if isinstance(field, models.ManyToOneRel):
            continue  # Skip reverse relations

        is_fk = isinstance(field, (models.ForeignKey, models.OneToOneField, models.ManyToManyField))

        field_name = f"{prefix}{field.name}" if flatten else field.name

        field_info = {
            'name': field_name,
            'verbose_name': getattr(field, 'verbose_name', '').title(),
            'data_type': field.get_internal_type(),
            'concrete': field.concrete,
            'editable': field.editable,
            'null': field.null,
        }

        if not flatten and is_fk:
            related_model = field.related_model
            field_info['related_model'] = {
                'app_name': related_model._meta.app_label,
                'model_name': related_model._meta.model_name,
                'verbose_name': related_model._meta.verbose_name.title(),
                'fields': get_model_fields(
                    related_model,
                    prefix='',
                    current_depth=current_depth + 1,
                    max_depth=max_depth,
                    visited_models=visited_models.copy(),
                    flatten=False
                )
            }

        fields.append(field_info)

        if flatten and is_fk:
            related_model = field.related_model
            nested_fields = get_model_fields(
                related_model,
                prefix=field_name + '.',
                current_depth=current_depth + 1,
                max_depth=max_depth,
                visited_models=visited_models.copy(),
                flatten=True
            )
            fields.extend(nested_fields)

    return fields


