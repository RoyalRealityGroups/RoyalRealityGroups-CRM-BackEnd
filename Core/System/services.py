import html
import os
import re
import threading
import time
import datetime
from django.conf import settings
import firebase_admin
import logging
import json
from django.utils import timezone
from django.db.models import Q,F
from django.db.models.signals import post_save, post_delete
from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.cache import cache
from firebase_admin import credentials, messaging
from Core.Core.utils.formaters import format_variables, get_attribute_value
from Core.Core.utils.generator import get_doc_path
from Core.Users.models import Authorization, AuthorizationDefinition, Device
from .models import Notification as NotificationModel, NotificationUsers, TaskScheduler, Template
from Core.Core.utils.utils import Util, calculate_next_run, is_valid_email, user_by_type_id

from Core.System.models import Setting,AlertConfig
from Core.System.signals import approval_event,assignee_added_event,multi_approved_event
from dynamic_preferences.registries import global_preferences_registry 
from .task_thread_manager import TaskThreadManager,active_threads

from datetime import timedelta, date
from django.db.models.functions import Now
User = get_user_model()

log = logging.getLogger(__name__)
login = True


def firebase_init():
    global login
    if login:
        try:
            GLOBAL_VARS = global_preferences_registry.manager().all()
            project_json = credentials.Certificate(json.loads(GLOBAL_VARS['JSON_DATA__JSONFILE'],strict=False))
            firebase_admin.initialize_app(project_json)
            login=False
        except Exception as E:
            pass
    else:
        pass


class Notification:
    
    def Send(user=None,subject="",body="",type=1,ref=0,message_priority=1,notification_type=1):
        if user != None and subject != "":
            NotificationModel(user=user,subject=subject,body=body,type=type,ref=ref,message_priority=message_priority,notification_type=notification_type).save()
            # if user.phone:          
                # sdata = {'to_phone': user.phone, 'message':  body + SMS.postfix }
                # Util.send_sms(sdata)

    def SendToUsers(users=[],subject="",body="",type=1,ref=0,message_priority=1,notification_type=1):
        if len(users) > 0 and subject != "":
            for user in users:
                NotificationModel(user=user,subject=subject,body=body,type=type,ref=ref,message_priority=message_priority,notification_type=notification_type).save()
                # if user.phone:          
                #     sdata = {'to_phone': user.phone, 'message':  body + SMS.postfix }
                    # Util.send_sms(sdata)



def get_dependent_models(model_class, in_models = []):
    if model_class != None:
        in_models.append(model_class)
        for related_object in model_class._meta.get_fields(include_hidden=True):
            if related_object.related_model != None and type(related_object).__name__ == "ManyToOneRel":
                if related_object.related_model not in in_models:
                    in_models += get_dependent_models(related_object.related_model, in_models)
                    # in_models.append(related_object.related_model)
                    
    return in_models


def send_push_notification(user_identifier, title, user_type, message, type, ref_id, modified_on, web_navigation_url=None, mobile_navigation_url=None, message_priority=1, notification_type=1):
    message = html.unescape(message)
    notification = NotificationModel.objects.create(
                    subject=title,
                    body=message,
                    type=type,
                    ref=ref_id,
                    message_priority=message_priority,
                    notification_type=notification_type,
                    web_navigation_url=web_navigation_url,
                    mobile_navigation_url=mobile_navigation_url
                )
                
    # Create notification user record
    NotificationUsers.objects.create(
                    user_identifier=user_identifier,  # Assuming username is used for notifications
                    user_type=user_type,  # Assuming default user type
                    notification=notification
                )
    
    firebase_init()
    alltokens = Device.objects.filter(Q(is_active=True) & (Q(socket=None) | Q(socket='')) & ~Q(fcmtoken='') & ~Q(fcmtoken=None) & Q(user_identifier=user_identifier) & Q(user_type=user_type)).values_list('fcmtoken', flat=True)
    
    alltokens_split = [alltokens[i:i + 500] for i in range(0, len(alltokens), 500)]
    
    response = None  # Initialize response variable
    
    for i, tokens in enumerate(alltokens_split):
        dataObject = {
            'id': str(notification.id),
            'message': message,
            'type': str(type),
            'ref_id': str(ref_id),
            'modified_on': str(modified_on),
            'web_navigation_url': str(web_navigation_url),
            'mobile_navigation_url': str(mobile_navigation_url),
        }

        multicast_message = messaging.MulticastMessage(notification=messaging.Notification(title=str(user_identifier), body=message), data=dataObject, tokens=tokens)
        response = messaging.send_multicast(multicast_message)

    if response is not None:
        pass
    else:
        pass


def send_push_notification_with_image(id, user,title, message, type, ref_id, modified_on, image_url=None):
    firebase_init()
    
    alltokens = Device.objects.filter(Q(is_active=True) & (Q(socket=None) | Q(socket='')) & ~Q(fcmtoken='') & ~Q(fcmtoken=None) & Q(user__is_active=True) & Q(Q(user__is_superuser=False) & Q(user=user))).values_list('fcmtoken', flat=True)
    
    alltokens_split = [alltokens[i:i + 500] for i in range(0, len(alltokens), 500)]
    
    response = None  # Initialize response variable

    for i, tokens in enumerate(alltokens_split):
        dataObject = {
            'id': str(id),
            'message': str(message),
            'type': str(type),
            'ref_id': str(ref_id),
            'modified_on': str(modified_on),
        }
        
        if image_url:
            dataObject['image_url'] = image_url

        dataObject = {key: str(value) for key, value in dataObject.items()}
        
        multicast_message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=str(title),
                body=str(message),
                image=str(image_url)
            ),
            data=dataObject,
            tokens=tokens
        )

        response = messaging.send_multicast(multicast_message)

    if response is not None:
        pass
    else:
        pass




def get_preferences(code, default=None):
    
    cache_data = cache.get(code)
    preferences = {}
    if cache_data:
        return cache_data
    else:
        try:
            settings_obj =  Setting.objects.get(preferences_code = code)
            preferences = json.loads(settings_obj.preferences)
        except json.JSONDecodeError:
            log.error(f"Invalid JSON format for preferences_code: {code}")
        except Exception as e:
            log.error(f"Error processing preferences for {code}: {e}")
            
        cache.set(code,preferences,timeout= settings.CACHE_TIME_OUT_ONE_YEAR)
        # return request_cfgs.preferences.get(code, default)
        return preferences

# def get_preferences(preferences_code, default=None):
#     setting = Setting.objects.filter(preferences_code=preferences_code).first()
#     if setting and setting.preferences:
#         try:
#             return json.loads(setting.preferences)  # Convert JSON string back to a Python dictionary
#         except json.JSONDecodeError:
#             return default  # Handle invalid JSON cases
#     return default


#------example of set preferences------------------#

# sms_setting = Setting.objects.get(preferences_code="SMS_CONFIG")

# email_setting = Setting.objects.get(preferences_code="EMAIL_CONFIG")

# set_preferences("EMAIL_CONFIG", {
#     "email_enabled": True,
#     "smtp_server": "smtp.example.com",
#     "port": 587
# })

# set_preferences("SMS_CONFIG", {
#     "sms_enabled": True,
#     "sms_gateway": "sms.example.com",
#     "api_key": "123456"
# })

# {
#         "preferences_code": "SMS_CONFIG",
#         "preferences": {
#             "Default":{
#                 "sms_provider": "Twilio",
#                 "api_key": "xyz"
#             },
#             "Gateway2":{
#                 "sms_provider": "Twilio",
#                 "api_key": "xyz"
#             },
#             "Gateway3":{
#                 "sms_provider": "Twilio",
#                 "api_key": "xyz"
#             }
#         }
#     }


def send_alert_sms(users, message, subject=None, gateway="Default", message_priority=1, notification_type=1, instance=None):
    """Send SMS alert to the user."""
    try:
        for user in users:
            receive_sms = False
            phone = None

            if isinstance(user, dict):
                phone = user.get('phone')
                receive_sms = user.get('receive_sms', True)
            else:
                phone = getattr(user, 'phone', None)
                receive_sms = getattr(user, 'receive_sms', False)

            if not receive_sms:
                log.warning(f"User {user} has turned off receive sms")
                continue
            
            try:
                message = format_variables(message, {
                    'user': user,
                    'instance': instance
                })

            except Exception as e:
                log.error(f"Failed to format message for user {user}: {str(e)}")
                continue

            if not phone or not isinstance(phone, str) or len(phone) != 10 or not phone.isdigit():
                log.warning(f"Invalid phone number format for user: {user}")
                continue
            
            log.info(f"Sending {message} to  {user} via SMS")
            sms_data = {
                "to_phone": phone,
                "message": message,
                "gateway": gateway
            }
            Util.send_sms(sms_data)

    except Exception as e:
        log.error(f"Failed to send SMS: {str(e)}")


def send_alert_email(users, message, subject=None, gateway="Default", instance=None,send_doc=False, screen=None,  is_attachment=False, attachment_variable=None, message_priority=1, notification_type=1):
    """Send email alert to the user."""
    results = {"sent": [], "failed": [], "skipped": []}
    try:
        for user in users:
            receive_email = False
            email = None

            if isinstance(user, dict):
                email = user.get('email')
                receive_email = user.get('receive_email', True)
            else:
                email = getattr(user, 'email', None)
                receive_email = getattr(user, 'receive_email', False)

            if not receive_email:
                log.warning(f"User {user} has turned off receive emails")
                results["skipped"].append(str(user))
                continue

            if not email or not is_valid_email(email):
                log.warning(f"Invalid email format for user: {user}")
                results["failed"].append(str(user))
                continue

            try:
                formatted_subject = format_variables(subject, {'user': user, 'instance': instance}) if subject else ''
                formatted_message = format_variables(message, {'user': user, 'instance': instance}) if message else ''
            except Exception as e:
                log.error(f"Failed to format subject/message for user {user}: {str(e)}")
                results["failed"].append(str(user))
                continue

            attachments = []
            if send_doc:
                if not screen:
                    log.error("Screen is required to get the document path.")
                    results["failed"].append(str(user))
                    continue
                
                pdf_path = get_doc_path(screen, instance.id)
                # print(f"PDF path: {pdf_path}")
                
                try:
                    if os.path.exists(pdf_path):
                        # Read file content
                        with open(pdf_path, 'rb') as pdf_file:
                            file_content = pdf_file.read()
                        
                        # Create attachment tuple (filename, content, content_type)
                        file_name = os.path.basename(pdf_path)
                        attachment = (file_name, file_content, 'application/pdf')
                        attachments.append(attachment)
                    else:
                        log.error(f"PDF file not found: {pdf_path}")
                except Exception as e:
                    log.error(f"Error reading PDF file {pdf_path}: {str(e)}")
                    results["failed"].append(str(user))
                    continue
                
            if is_attachment :
                if not attachment_variable:
                    log.error("Attachment variable is required to get the document path.")
                    results["failed"].append(str(user))
                    continue
                
                try:
                    doc_path = get_attribute_value(instance, attachment_variable, format=False)

                    if doc_path:
                        # Remove protocol/domain if present
                        # If doc_path is like "127.0.0.1:8000/media/temp/xxx.jpeg"
                        if 'media/' in doc_path:
                            relative_path = doc_path.split('media/')[-1]  # gives temp/xxx.jpeg
                            file_path = os.path.join(settings.MEDIA_ROOT, relative_path)
                        else:
                            file_path = doc_path  # fallback

                        if os.path.exists(file_path):
                            with open(file_path, 'rb') as doc_file:
                                file_content = doc_file.read()
                            file_name = os.path.basename(file_path)
                            attachment = (file_name, file_content, 'application/octet-stream')
                            attachments.append(attachment)
                        else:
                            log.error(f"Document file not found: {file_path}")
                    else:
                        log.error(f"Document path is empty.")

                except Exception as e:
                    log.error(f"Error reading document file {attachment_variable}: {str(e)}")
                    results["failed"].append(str(user))
                    continue
            
            email_data = {
                "email_subject": formatted_subject,
                "email_body": formatted_message,
                "to_email": email,
                "gateway": gateway,
            }

            try:
                Util.send_email(email_data, attachments)
                log.info(f"Email sent to {email}")
                results["sent"].append(email)
            except Exception as e:
                log.error(f"Failed to send email to {email}: {str(e)}")
                results["failed"].append(email)
    except Exception as e:
        log.error(f"Failed to send email: {str(e)}")
    return results


def send_alert_notification(users, message, subject=None, gateway=None, instance=None, web_navigation_url=None, mobile_navigation_url=None, message_priority=1, notification_type=1):
    """Send notification alert to the user."""
    try:
        for user in users:
            
            if getattr(user, 'receive_notification', False):
                try:
                    subject = format_variables(subject,{
                        'user': user,
                        'instance': instance
                    })
                    log.info(f"Sending {subject} to {user} via push notification")

                    # Format message for all users
                    message = format_variables(message,{
                        'user': user,
                        'instance': instance
                    })
                    log.info(f"Sending {message} to  {user} via push notification")
                    
                    # Format navigation URLs if provided
                    formatted_web_url = format_variables(web_navigation_url, {
                        'user': user,
                        'instance': instance
                    }) if web_navigation_url else None
                    
                    formatted_mobile_url = format_variables(mobile_navigation_url, {
                        'user': user,
                        'instance': instance
                    }) if mobile_navigation_url else None
                    
                except Exception as e:
                    log.error(f"Failed to format message for user {user}: {str(e)}")
                    continue
                try:
                    # Send push notification
                    send_push_notification(
                        user_identifier=user.id,
                        user_type=user.__class__.__name__,
                        title=subject,
                        message=message,
                        type=instance.__class__.__name__ if instance else "Common Notification",
                        ref_id=str(instance.id) if instance else None,
                        modified_on=datetime.datetime.now(),
                        web_navigation_url=formatted_web_url,
                        mobile_navigation_url=formatted_mobile_url,
                        message_priority=message_priority,
                        notification_type=notification_type
                    )
                    log.info(f"Push notification sent to {user.username}")
                except Exception as e:
                    log.error(f"Failed to send notification to {user.username}: {str(e)}")
            else:
                log.warning(f"User {user} has turned off receive notifications")
                
    except Exception as e:
        log.error(f"Failed to send notification: {str(e)}")


def send_alert(alert, instance= None ):
    """Send alerts based on type (SMS, email, or notification) to configured recipients"""
    log.info(f"Sending alert for instance: {instance}")
    
    # Collect recipients based on sender_type
    users = list()
    
    if alert.is_scheduled and alert.sender_type in [1,4]:
        log.warning(f"Scheduled alerts does not have instance so cant proceed with sender_type 1 and 4 ")
        return

    # Collect recipients based on sender type
    if alert.sender_type == 1:  # Created by
        # if (hasattr(instance, "created_by_type") and hasattr(instance, "created_by_identifier"))
        user_obj = user_by_type_id(instance.created_by_type,instance.created_by_identifier)
        if user_obj:
            users.append(user_obj)

    elif alert.sender_type == 2:  # Groups
        # if len(alert.send_to_groups.all()) == 0:
        #     log.warning(f"alert:{alert} has no send_to_groups")
        #     return
        # else:
        for user_model in settings.USER_MODELS:
            model_path = user_model.get('model')
            model_class = apps.get_model(model_path)
            
            user_objs = model_class.objects.filter(groups__alertconfigs__id = alert.id ).distinct()
            if user_objs.exists():
                users.extend(user_objs)
            else:
                log.warning(f"alert:{alert} has no send_to_groups {alert.send_to_groups.all()} with users")
        # for group in alert.send_to_groups.all():
        #     for user in group.user_set.all():
        #         users.append(user)

    elif alert.sender_type == 3:  # Users
        if len(alert.alert_users.filter(is_deleted = False)) == 0:
            log.warning(f"alert:{alert} has no alert_users")
            return
        else:
            alert_users = alert.alert_users.filter(is_deleted = False)
            for alert_user in alert_users:
                user_obj = user_by_type_id(alert_user.user_type,alert_user.user_identifier)
                if user_obj:
                    users.append(user_obj)
    
    elif alert.sender_type == 4:  # Dynamic field
        try:
            #Handle nested attributes with dot notation (e.g., 'user.name')
            attr_value = instance
            # if not alert.type == 3:
            #     for attr in alert.variable.split('.'):
            #         attr_value = getattr(attr_value, attr, None)
            #         if attr_value is None:
            #             break
            #     if attr_value:
            #         if alert.type == 2:
            #             # Check if the value is a valid email or phone number
            #             verified_email = is_valid_email(attr_value)
            #             if verified_email:
            #                 users.append({'email': attr_value})
            #             else:
            #                 log.warning(f"Invalid email format for {alert.variable}, value: {attr_value}")
                            
            #         elif alert.type == 1:
            #             # Check if the value is a valid phone number
            #             if isinstance(attr_value, str) and len(attr_value) == 10 and attr_value.isdigit():
            #                 users.append({'phone': attr_value})
            #             else:
            #                 log.warning(f"Invalid phone number format for {alert.variable}, value: {attr_value}")
                            
            # else:
            users_list = get_attribute_value(attr_value,alert.variable,format=False)
            users.extend(users_list)
            log.info(f"Added dynamic field {alert.variable} to recipients")
        except:
            log.warning(f"Failed to resolve attribute path: {alert.variable}")
            
    elif alert.sender_type == 5:  # Static value
        if alert.value:
            try:
                # Check if the value is a valid email or phone number
                if alert.type == 2:
                    verified_email = is_valid_email(alert.value)
                    if verified_email:
                        users.append({'email': alert.value})
                    else:
                        log.warning(f"Invalid email format for static value {alert.value}")
                elif alert.type == 1:
                    # Check if the value is a valid phone number
                    if isinstance(alert.value, str) and len(alert.value) == 10 and alert.value.isdigit():
                        users.append({'phone': alert.value})
                    else:
                        log.warning(f"Invalid phone number format for static value {alert.value}")

            except Exception as e:
                log.error(f"Failed to add static value {alert.value}: {str(e)}")
                
    body = alert.template.message if alert.template else None
    subject = alert.subject_template.message if alert.subject_template else None  
    web_url = alert.web_navigation_url.message if alert.web_navigation_url else None
    mobile_url = alert.mobile_navigation_url.message if alert.mobile_navigation_url else None

    if alert.type == 1:  # SMS

        send_alert_sms(users, body, subject, alert.gateway, alert.message_priority,alert.notification_type, instance)

    elif alert.type == 2:  # Email

        send_alert_email(users, body, subject, alert.gateway, instance, alert.send_doc, alert.screen, alert.is_attachment, alert.attachment_variable, alert.message_priority,alert.notification_type)

    elif alert.type == 3 and alert.sender_type in [1,2,3,4]:  # Push Notifications
        # Get web and mobile navigation URLs from variables if they exist
        # web_navigation_url = None
        # mobile_navigation_url = None
        
        # if alert.web_navigation_url_variable and instance:
        #     try:
        #         web_navigation_url = get_attribute_value(instance, alert.web_navigation_url_variable)
        #     except Exception as e:
        #         log.error(f"Failed to get web navigation URL from variable {alert.web_navigation_url_variable}: {str(e)}")
        
        # if alert.mobile_navigation_url_variable and instance:
        #     try:
        #         mobile_navigation_url = get_attribute_value(instance, alert.mobile_navigation_url_variable)
        #     except Exception as e:
        #         log.error(f"Failed to get mobile navigation URL from variable {alert.mobile_navigation_url_variable}: {str(e)}")
        send_alert_notification(users, body, subject, alert.gateway, instance, web_url, mobile_url, alert.message_priority, alert.notification_type)

    log.info("Alert process completed.")




def model_signal_handler(sender, instance,  created=None, **kwargs):
    # print(f"Signal triggered for {sender.__name__} - Instance: {instance}")
    # event = 3 if created is None else (1 if created else 2)
    if created is not None:
        event = 1 if created else 2  # post_save -> create or update
    else:
        event = 3  # post_delete -> delete

    if hasattr(instance, 'is_deleted') and instance.is_deleted:
        event = 3

    alerts = AlertConfig.objects.filter(screen__app_label = sender._meta.app_label, screen__model= sender._meta.model_name, event_type=event, is_active=True)
    for alert in alerts:
        send_alert(alert, instance)


def authantication_signal_handler(sender, instance, event_name, **kwargs):
    """
    Handles custom events like approval, Rejection of authentication.
    """
    event_mapping = {
        "approval": 4,
        "rejected": 5
    }
    event = event_mapping.get(event_name)

    alerts = AlertConfig.objects.filter(screen__app_label = sender._meta.app_label, screen__model= sender._meta.model_name, event_type=event, is_active=True)
    for alert in alerts:
        send_alert(alert, instance)


def assignee_signal_handler(sender, instance, event_name, **kwargs):
    """
    Handles custom events like approval, assignee_added.
    """
    event_mapping = {
        "AddAssignee": 6,
        "RemoveAssignee": 7
    }
    event = event_mapping.get(event_name)

    alerts = AlertConfig.objects.filter(screen__app_label = sender._meta.app_label, screen__model= sender._meta.model_name, event_type=event, is_active=True)
    for alert in alerts:
        send_alert(alert, instance)
        

def multi_lvl_approval_signal_handler(sender, instance,obj, event_name, **kwargs):
    """
    Handles custom events like approval
    """
    
    templates = Template.objects.in_bulk(
        field_name="name",
        id_list=[
            "Approval Notification subject For Created By",
            "Rejection Notification subject For Created By",
            "Record approved notification body For Created By",
            "Record Rejected notification body For Created By",
            "Approval Email subject For Created By",
            "Approval Email body For Created By",
            "Rejection Email subject For Created By",
            "Rejection Email body For Created By",
            "Approval Sms body For Created By",
            "Rejection Sms body For Created By",
            "Approval Notification subject For User",
            "Record approved notification body For User",
            "Approval Email subject For User",
            "Approval Email body For User",
            "Approval Sms body For User",
        ]
    )

    approvel_notification_sub_cb = templates.get("Approval Notification subject For Created By")
    reject_notification_sub_cb = templates.get("Rejection Notification subject For Created By")
    approval_notification_body_cb = templates.get("Record approved notification body For Created By")
    reject_notification_body_cb = templates.get("Record Rejected notification body For Created By")
    approval_email_sub_cb = templates.get("Approval Email subject For Created By")
    approval_email_body_cb = templates.get("Approval Email body For Created By")
    reject_email_sub_cb = templates.get("Rejection Email subject For Created By")
    reject_email_body_cb = templates.get("Rejection Email body For Created By")
    approval_sms_body_cb = templates.get("Approval Sms body For Created By")
    reject_sms_body_cb = templates.get("Rejection Sms body For Created By")
    approvel_notification_sub_user = templates.get("Approval Notification subject For User")
    approvel_notification_body_user = templates.get("Record approved notification body For User")
    approval_email_sub_user = templates.get("Approval Email subject For User")
    approval_email_body_user = templates.get("Approval Email body For User")
    approval_sms_body_user = templates.get("Approval Sms body For User")
    
    
    if not obj:
        log.warning(f"object not found for instance_id: {instance.instance_id}")
        return
    
    auth_def = AuthorizationDefinition.objects.filter(screen = instance.screen).first()
    if not auth_def:
        log.warning(f"Authorization Definition not found")
        return
    final_level = auth_def.level

    # is_final_level = instance.authorized_level >= final_level
    # next_level = min(instance.authorized_level + 1, final_level)
    
    user_obj = user_by_type_id(obj.created_by_type,obj.created_by_identifier)
    
    if user_obj:
            
        if instance.authorized_level <= final_level :
            if event_name == "approved":
                if auth_def.send_notification:
                    subject = approvel_notification_sub_cb.message
                    message = approval_notification_body_cb.message
                    send_alert_notification([user_obj], message, subject, None, obj)
                        
                if auth_def.send_email:
                    subject = approval_email_sub_cb.message
                    message = approval_email_body_cb.message
                    send_alert_email([user_obj], message, subject, instance=obj)
                    
                if auth_def.send_sms:
                    subject = ''
                    message = approval_sms_body_cb.message
                    send_alert_sms([user_obj], message, subject, instance=obj)
                    
            elif event_name == "rejected":
                if auth_def.send_notification:
                    subject = reject_notification_sub_cb.message
                    message = reject_notification_body_cb.message
                    send_alert_notification([user_obj], message, subject, None, obj)
                    
                if auth_def.send_email:
                    subject = reject_email_sub_cb.message
                    message = reject_email_body_cb.message
                    send_alert_email([user_obj], message, subject, instance=obj)
                
                if auth_def.send_sms:
                    subject = ''
                    message = reject_sms_body_cb.message
                    send_alert_sms([user_obj], message, subject, instance=obj)
                
    # if not is_final_level:
    approvals = Authorization.objects.filter(screen = instance.screen, is_deleted=False, level = instance.authorized_level + 1,)
    
    
    if not approvals:
        log.warning(f"No approvals found for instance: {instance}")
        return
    
    if instance.authorized_status == 2:
        
        for approval in approvals:
            
            users = []
            if approval.type == Authorization.USER:
                
                user_obj = user_by_type_id(approval.created_by_type,approval.created_by_identifier)
                if user_obj:
                    users.append(user_obj)

            elif approval.type == Authorization.GROUP:
                users.extend(approval.group.user_set.all())
                
            if not users:
                log.warning(f"No users found for approval: {approval}")
                continue
                
            if approval.send_sms:
                subject = ''
                message = approval_sms_body_user.message
                send_alert_sms(users, message, subject, instance=obj)
                
            if approval.send_email:
                subject = approval_email_sub_user.message
                message = approval_email_body_user.message
                send_alert_email(users, message, subject, instance=obj)
                
            if approval.send_notification:
                subject = approvel_notification_sub_user.message
                message = approvel_notification_body_user.message
                send_alert_notification(users, message, subject, instance=obj)



def register_signals():
    """Dynamically register signals for all models."""
    all_models = apps.get_models()
    # all_models = []
    
    for model in all_models:
        post_save.connect(model_signal_handler, sender=model, weak=False)
        post_delete.connect(model_signal_handler, sender=model, weak=False)

    # City = apps.get_model('DynamicDjango', 'City')
    # Account = apps.get_model('Masters', 'Account')

    # post_save.connect(model_signal_handler, sender=Account, weak=False,) 
    # post_delete.connect(model_signal_handler, sender=Account, weak=False)
approval_event.connect(authantication_signal_handler, weak=False)
assignee_added_event.connect(assignee_signal_handler, weak=False)
multi_approved_event.connect(multi_lvl_approval_signal_handler, weak=False)



def scheduled_alert_worker():
    """Thread worker to check and trigger scheduled alerts."""
    while True:
        time.sleep(60)
        current_time = timezone.now()
        today = current_time.date()

        alerts = AlertConfig.objects.filter(
            is_active=True,
            is_scheduled=True,
            start_time__lte=current_time
        ).filter(
            Q(next_run__lte=current_time) | Q(next_run__isnull=True)
        ).filter(
            Q(last_run__isnull=True) | (
                Q(repeat_interval__gt=0) & Q(is_active=True) & (
                    Q(
                        frequency=AlertConfig.MINUTES,
                        last_run__lte=current_time - timedelta(minutes=1)
                    ) |
                    Q(
                        frequency=AlertConfig.HOURS,
                        last_run__lte=current_time - timedelta(hours=1)
                    ) |
                    Q(
                        frequency=AlertConfig.DAYS,
                        last_run__lte=current_time - timedelta(days=1)
                    ) |
                    Q(
                        frequency=AlertConfig.WEEKS,
                        last_run__lte=current_time - timedelta(weeks=1),
                        start_time__week_day=today.weekday() + 1
                    )
                )
            )
        )

        for alert in alerts:
            send_alert(alert, None)
            alert.last_run = current_time
            next_time = calculate_next_run(alert)
            if next_time:
                alert.next_run = next_time
            else:
                alert.is_active = False
            alert.save()
            

def start_alert_scheduler_thread():
    """Starts the alert scheduler in a background thread."""
    thread = threading.Thread(target=scheduled_alert_worker, daemon=True)
    thread.start()
    


def scheduler_worker():
    while True:
        time.sleep(30)  # Check every 30 seconds
        TaskThreadManager.kill_expired_threads()

        now = timezone.now()
        now_local = timezone.localtime(now)
        today = now_local.date()

        # Prepare query to find tasks due to run
        # First run: last_run is null, or next_run is <= now
        tasks = TaskScheduler.objects.filter(
            is_active=True,
            start_time__lte=now_local
        ).filter(
            Q(next_run__lte=now_local) | Q(next_run__isnull=True)
        ).filter(
            Q(last_run__isnull=True) |  # First run ever
            Q(repeat_interval__gt=0)
        ).filter(
            Q(frequency=TaskScheduler.DAILY) |
            Q(frequency=TaskScheduler.WEEKLY, start_time__week_day=today.isoweekday()) |
            Q(frequency=TaskScheduler.MONTHLY, start_time__day=today.day) |
            Q(frequency=TaskScheduler.YEARLY, start_time__day=today.day, start_time__month=today.month) |
            Q(frequency=TaskScheduler.CUSTOM, custom_interval__isnull=False) |
            Q(frequency=TaskScheduler.ONETIME)
        )
        
        for task in tasks:
            # Prevent starting duplicate if parallel not allowed
            if not task.allow_parallel and any(t.task.id == task.id for t in TaskThreadManager.get_all_threads()):
                continue

            started = TaskThreadManager.start_task(task)
            if started:
                task.last_run = now
                next_run = calculate_next_run(task)
                task.next_run = next_run if next_run else None
                # Deactivate one-time tasks after execution
                if task.frequency == TaskScheduler.ONETIME:
                    task.is_active = False
                task.save()


def start_task_scheduler_thread():
    """Starts the task scheduler in a background thread."""
    t = threading.Thread(target=scheduler_worker, daemon=True)
    t.start()
    
    
def initialize_templates():
    """
    Initialize templates when program starts.
    Creates templates that don't exist and ignores existing ones with the same name.
    """
    # Define all required templates
    template_data = [
        {
            'name': "Approval Notification subject For Created By",
            'message': "Approval Notification",
        },
        {
            'name': "Rejection Notification subject For Created By",
            'message': "Rejection Notification",
        },
        {
            'name': "Record approved notification body For Created By",
            'message': "Your request for the record ((instance.code)) has been approved by ((instance.current_authorized_by))",
        },
        {
            'name': "Record Rejected notification body For Created By",
            'message': "Your request for the record ((instance.code)) has been Rejected by ((instance.authorized_by)) in the level ((instance.authorized_level))",
        },
        {
            'name': "Approval Email subject For Created By",
            'message': "Your request for the record ((instance.code)) has been Rejected by ((instance.authorized_by)) in the level ((instance.authorized_level))",
        },
        {
            'name': "Approval Email body For Created By",
            'message': "Your request for the record ((instance.code)) has been Rejected by ((instance.authorized_by)) in the level ((instance.authorized_level))",
        },
        {
            'name': "Rejection Email subject For Created By",
            'message': "Your request for the record ((instance.code)) has been Rejected by ((instance.authorized_by)) in the level ((instance.authorized_level))",
        },
        {
            'name': "Rejection Email body For Created By",
            'message': "Your request for the record ((instance.code)) has been Rejected by ((instance.authorized_by)) in the level ((instance.authorized_level))",
        },
        {
            'name': "Approval Sms body For Created By",
            'message': "Your request for the record ((instance.code)) has been Rejected by ((instance.authorized_by)) in the level ((instance.authorized_level))",
        },
        {
            'name': "Rejection Sms body For Created By",
            'message': "Your request for the record ((instance.code)) has been Rejected by ((instance.authorized_by)) in the level ((instance.authorized_level))",
        },
        {
            'name': "Approval Notification subject For User",
            'message': "Approval Notification",
        },
        {
            'name': "Record approved notification body For User",
            'message': "A record ((instance.code)) is waiting for your approval",
        },
        {
            'name': "Approval Email subject For User",
            'message': " A record ((instance.code)) is waiting for your approval",
        },
        {
            'name': "Approval Email body For User",
            'message': " A record ((instance.code)) is waiting for your approval",
        },
        {
            'name': "Approval Sms body For User",
            'message': " A record ((instance.code)) is waiting for your approval",
        },
        {
            'name': "OTP Login",
            'message': "Your OTP code is ((user.otp)). Please use it to log in.",
        },
        {
            'name': "OTP Verification",
            'message': "Your OTP code is ((user.otp)). Please use it to verify your account.",
        },
        {
            'name': "Email OTP Verification",
            'message': "Your OTP code is ((user.otp)). Please use it to verify your account.",
        },
    ]
    
    # Get all existing template names
    existing_template_names = set(Template.objects.values_list('name', flat=True))
    
    # Filter out templates that already exist
    
    for data in template_data :
        if data['name'] not in existing_template_names:
            Template.objects.create(**data)
    