from django.apps import apps
from django.db.models.signals import  post_save
from Core.Core.context.Context import get_user
from Core.Core.utils.converters import model_to_dict
from Core.System.models import ActivityLog
from Core.Users.models import ContentTypeDetail
from django.contrib.contenttypes.models import ContentType

main_type= type
 
def handler_log(sender,  instance,  created, *args, **kwargs):
   
    if not (hasattr(instance, 'code') and  hasattr(instance, 'is_deleted')):
        return None
   
    data = model_to_dict(instance)
    
    user = get_user()
    # user = None
    
    if created:
        type = 1
 
    elif instance.is_deleted:
        type = 3
 
    else:
        type = 2
 
    if user != None:
        user_type= user.__class__.__name__
        user_identifier = user.id
        # model_path = get_model_path(user_type)
    else:
        # If action_user is None, we need to handle this scenario
        user_type = None
        user_identifier = None
        # model_path = None


    try:
        screen = ContentType.objects.get_for_model(sender)
        screen_name = ContentTypeDetail.objects.filter(contenttype=screen).first()
        if not screen_name:
            screen_name = "ContentTypeDetail not found"
 
    except ContentType.DoesNotExist:
        screen = None
        screen_name = "ContentType not found"
   
    
    activitylog = ActivityLog.objects.create(user_type=user_type,user_identifier =user_identifier, type = type, screen_name = screen_name, screen = screen, instance_id = instance.id,  instance_code = instance.code, data=data)
    # data_obj = ActivityLogData.objects.create( activitylog=activitylog,data=data)
   
for model_class in apps.get_models():
    post_save.connect(handler_log, sender=model_class, dispatch_uid="post_log_"+model_class.__name__)
