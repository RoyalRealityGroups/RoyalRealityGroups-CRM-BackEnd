
#-------------------------------------------------------------------------------------------------sameple masters

from Dynamics.model_factory import create_dynamic_model, validate_and_generate, MODEL_ACCEPTED_FIELDS, MODEL_REQUIRED_FIELDS
from Dynamics.serializer_factory import create_dynamic_serializer, SER_ACCEPTED_FIELDS, SER_REQUIRED_FIELDS
from Dynamics.models import DynamicModel
import json


fields_dict = {
    'name': {'type': 'Char', 'required': False, 'max_length': 100, 'min_length': 1,'show_in_view':True,'show_in_report':True,'show_in_edit':True,'show_in_filter':False,'show_in_list':True,'show_in_add':True},
    'location': {'type': 'ForeignKey','to': 'Masters.Location','read_fields':['name'],'filter_data':{}, 'required': False,'related_name':'sampletest_show','show_in_view':True,'show_in_report':True,'show_in_edit':True,'show_in_filter':True,'show_in_list':True,'show_in_add':True,'import_fields':['name'],'export_fields':['name']},
    'remarks': {'type': 'Text', 'required': False, 'max_length': 1000, 'min_length': 5,'show_in_view':True,'show_in_report':True,'show_in_edit':True,'show_in_filter':False,'show_in_list':True,'show_in_add':True},
    'gender': {'type': 'Choice', 'required': False, 'default': 1, 'show_in_view':True,'choices': [[1, 'Male'], [2, 'Female'], [3, 'Others']],'show_in_report':True,'show_in_edit':True,'show_in_filter':True,'show_in_list':True,'show_in_add':True},
    'age': {'type': 'Integer', 'required': False, 'default': 0,'show_in_view':True,'show_in_report':True,'show_in_edit':True,'show_in_filter':False,'show_in_list':True,'show_in_add':True},
    'datetime': {'type': 'DateTime', 'required': False,  'read_only': True,'show_in_view':True,'show_in_report':True,'show_in_edit':True,'show_in_filter':True,'show_in_list':True,'show_in_add':True,'range_filter':True},
    'date': {'type': 'Date', 'required': False, 'read_only': True,'show_in_view':True,'show_in_report':True,'show_in_edit':True,'show_in_filter':True,'show_in_list':True,'show_in_add':True,'range_filter':True},
    'time': {'type': 'Time', 'required': False, 'read_only': True,'show_in_view':True,'show_in_report':True,'show_in_edit':True,'show_in_filter':True,'show_in_list':True,'show_in_add':True},
    'duration': {'type': 'Duration', 'required': False, 'read_only': True,'show_in_view':True,'show_in_report':True,'show_in_edit':True,'show_in_filter':False,'show_in_list':True,'show_in_add':True},
    'radius': {'type': 'Decimal', 'required': False, 'max_digits': 9, 'decimal_places': 2, 'default': 0,'show_in_view':True,'show_in_report':True,'show_in_edit':True,'show_in_filter':False,'show_in_list':True,'show_in_add':True},
    'groups': {'type': 'ManyToMany', 'to': 'auth.Group','multiple_filter': True,'read_fields':['name'],'filter_data':{}, 'required': True,'related_name':'sampletest_show_multi','show_in_view':True,'show_in_report':True,'show_in_edit':True,'show_in_filter':True,'show_in_list':False,'show_in_add':True},
    'created_by': {'type': 'ForeignKey','to': 'Users.user','read_fields':['username'],'filter_data':{}, 'required': False,'related_name':'sampletest_show_created_dy','show_in_view':True,'show_in_report':True,'show_in_edit':True,'show_in_filter':True,'show_in_list':True,'show_in_add':True,'import_fields':['id'],'export_fields':['id','username']},
    'modified_by': {'type': 'ForeignKey','to': 'Users.user','read_fields':['username'],'filter_data':{}, 'required': False,'related_name':'sampletest_show_modify_by','show_in_view':True,'show_in_report':True,'show_in_edit':True,'show_in_filter':True,'show_in_list':True,'show_in_add':True,'import_fields':['id'],'export_fields':['id','username']},
    'is_deleted': {'type': 'Boolean','default': False,'required': False ,'show_in_view':False,'show_in_report':False,'show_in_edit':False,'show_in_filter':False,'show_in_list':False,'show_in_add':False},
}

fields_dict = {
    'name': {'type': 'Char', 'required': False, 'max_length': 100, 'min_length': 1,'show_in_view':True,'show_in_report':True,'show_in_edit':True,'show_in_filter':False,'show_in_list':True,'show_in_add':True},
    'code': {'type': 'Char', 'required': False, 'max_length': 30, 'min_length': 1,'show_in_view':True,'show_in_report':True,'show_in_edit':True,'show_in_filter':False,'show_in_list':True,'show_in_add':True},
    'location': {'type': 'ForeignKey','to': 'Masters.Location','read_fields':['name','state__id'],'filter_data':{}, 'required': False,'related_name':'sampletest_show','show_in_view':True,'show_in_report':True,'show_in_edit':True,'show_in_filter':True,'show_in_list':True,'show_in_add':True,'import_fields':['name'],'export_fields':['name']},
    'remarks': {'type': 'Text', 'required': False, 'max_length': 1000, 'min_length': 5,'show_in_view':True,'show_in_report':True,'show_in_edit':True,'show_in_filter':False,'show_in_list':True,'show_in_add':True},
    'created_by': {'type': 'ForeignKey','to': 'Users.user','read_fields':['username'],'filter_data':{}, 'required': False,'related_name':'sampletest_show_created_dy','show_in_view':True,'show_in_report':True,'show_in_edit':True,'show_in_filter':True,'show_in_list':True,'show_in_add':True,'import_fields':['id'],'export_fields':['id','username']},
    'modified_by': {'type': 'ForeignKey','to': 'Users.user','read_fields':['username'],'filter_data':{}, 'required': False,'related_name':'sampletest_show_modify_by','show_in_view':True,'show_in_report':True,'show_in_edit':True,'show_in_filter':True,'show_in_list':True,'show_in_add':True,'import_fields':['id'],'export_fields':['id','username']},
    'created_on': {'type': 'DateTime', 'required': False,  'read_only': True,'show_in_view':True,'show_in_report':True,'show_in_edit':True,'show_in_filter':True,'show_in_list':True,'show_in_add':True,'range_filter':True},
    'modified_on': {'type': 'DateTime', 'required': False,  'read_only': True,'show_in_view':True,'show_in_report':True,'show_in_edit':True,'show_in_filter':True,'show_in_list':True,'show_in_add':True,'range_filter':True},
    'is_deleted': {'type': 'Boolean','default': False,'required': False ,'show_in_view':False,'show_in_report':False,'show_in_edit':False,'show_in_filter':False,'show_in_list':False,'show_in_add':False},
}

sample_rules = []

# sample_rules = [{
#     "apply_on": {"new": True, "existing": True},
#     "evalute_on": {"on_load": True, "on_save": True},
#     "status": True,
#     "condition": 'data.get("age", 0) >= 18',
#     "formating": [{
#         "feild_name": "is_deleted",
#         "change_type": "set_value",
#         "change_value": "True"
#     }]
# }]


fields_str = json.dumps(fields_dict)
fields_str

sample_rules_str = json.dumps(sample_rules)
sample_rules_str

other_attributes = {'CODE_PREFIX': 'WH' }
other_attributes_str = json.dumps(other_attributes)
other_attributes_str

obj = DynamicModel.objects.update_or_create(app_label = 'Masters', model_name = 'WareHouse', defaults={ 'fields' : fields_str,'rules' : sample_rules, 'other_attributes' : other_attributes_str })


#--------------------------------------------------------------------------Masters Jsons---------------------------------------------------------------------- #


from Core.System.services import register_signals
register_signals()

from Core.System.models import Template
import json
code = 'TEMP00001'
var = {'code': 'created_by.username'}
msg_var = json.dumps(var)
msg_var

obj = Template.objects.filter(code=code).update(msg_variables=msg_var)



# def get_attribute_value(instance, attr_name, default=None):
#     """
#     Get the value of an attribute from an instance.
#     Supports dot notation for nested attributes.
    
#     Args:
#         instance (object): The instance to get the attribute from.
#         attr_name (str): The name of the attribute to get.
#         default: The default value to return if the attribute is not found.
        
#     Returns:
#         The value of the attribute or the default value.
#     """
#     if not instance:
#         return default
        
#     try:
#         # Handle nested attributes with dot notation (e.g., 'user.name')
#         parts = attr_name.split('.')
#         value = instance
        
#         for part in parts:
#             if hasattr(value, part):
#                 value = getattr(value, part)
#             elif isinstance(value, dict) and part in value:
#                 value = value[part]
#             else:
#                 return default
                
#         # Convert value to string if it's not None
#         if value is not None:
#             return str(value)
#         return default
#     except Exception:
#         return default


# def replace_variables(pattern, text, instance=None, variables_map=None):
#     """
#     Replace variables in text with their values.
    
#     Args:
#         pattern (str): The regex pattern to match variables.
#         text (str): The text containing variables.
#         instance (object, optional): The instance to get variable values from.
#         variables_map (dict, optional): A mapping of variable names to instance attributes.
        
#     Returns:
#         str: The text with variables replaced.
#     """
#     try:
#         def replacer(match):
#             var = match.group(1).strip()
            
#             # If we have a variables map, use it to get the actual attribute name
#             if variables_map and var in variables_map:
#                 actual_var = variables_map[var]
#             else:
#                 actual_var = var
                
#             # Get the value from the instance
#             value = get_attribute_value(instance, actual_var, match.group(0))
#             return value
        
#         return re.sub(pattern, replacer, text)
#     except Exception as e:
#         raise Exception(f"Error replacing variables: {str(e)}")


# def format_variables(obj, instance=None):
#     """
#     Format the message template by replacing variables with their values.
    
#     Args:
#         obj (Template): The Template object containing the message and msg_variables.
#         instance (object, optional): The instance to get variable values from.
        
#     Returns:
#         str: The formatted message.
#     """
#     text = obj.message
#     print("text",text)
    
#     if not text:
#         return ""
    
#     variables_map = {}
#     if obj.msg_variables:
#         try:
#             variables_map = json.loads(obj.msg_variables)
#         except json.JSONDecodeError:
#             raise Exception("Invalid JSON in msg_variables field")
    
#     try:
#         # Pattern to match ((variable_name))
#         pattern = r'\(\(\s*(.*?)\s*\)\)'
        
#         # Find all variables in the text
#         matches = re.findall(pattern, text)
        
#         if len(matches) > 0:
#             # Replace variables
#             text = replace_variables(pattern, text, instance, variables_map)
            
#             # Check if all variables were replaced
#             matches2 = re.findall(pattern, text)
#             if len(matches2) > 0:
#                 error_msg = f"Failed to replace variables: {', '.join(matches2)}"
#                 raise Exception(error_msg)
        
#         return text
#     except Exception as e:
#         raise Exception(f"Error formatting variables: {str(e)}")

from Core.System.database_event_listener import start_listener

start_listener()

from Core.System.models import Setting
import json

preferences_code= "SMS_CONFIG"
preferences= {
    "Default":{
        "sms_provider": "Twilio",
        "api_key": "xyz"
    },
    "Gateway2":{
        "sms_provider": "Twilio",
        "api_key": "xyz"
    },
    "Gateway3":{
        "sms_provider": "Twilio",
        "api_key": "xyz"
    }
}

obj = Setting.objects.update_or_create(preferences_code=preferences_code, defaults={ 'preferences' : json.dumps(preferences) })
obj

from Core.System.services import request_cfgs
request_cfgs.preferences

import threading
print('number of current threads is ', threading.active_count())

from Core.System.signals import approval_event
from Masters.models import UOM
from django.utils import timezone

instance = UOM.objects.get(code='UOM00001')

if instance.authorized_status != 2:
            instance.authorized_status = 3
            instance.authorized_on = timezone.now()
            instance.authorized_level = 3
            instance.save()
            approval_event.send(sender=instance.__class__, instance=instance, event_name="rejected")

approval_event.send(sender=instance.__class__, instance=instance, event_name="approval")