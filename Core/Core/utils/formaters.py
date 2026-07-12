import base64
import json
import re
import logging
from datetime import date, datetime, timedelta
from django.db.models.manager import BaseManager
from django.db.models.query import QuerySet
from django.db.models.fields.files import FieldFile
from collections.abc import Iterable

from Core.Core.utils.converters import build_abs_doc_url
from Core.Core.utils.utils import user_by_type_id

log = logging.getLogger(__name__)

def format_mobile_number(number):
    # Convert number to string and remove any whitespace
    number = str(number).strip()
    if number.startswith('+91'):
        return number
    else:
        return '+91' + number


def format_attribute_value(value, default):
    # Post-processing: format datetime / date
    if isinstance(value, datetime):
        value = value + timedelta(hours=5, minutes=30)
        return value.strftime("%d-%m-%Y %H:%M:%S")
    elif isinstance(value, date):
        return value.strftime("%d-%m-%Y")
    elif isinstance(value, FieldFile):
        value = build_abs_doc_url(value)
        return value
    elif value is not None:
        return str(value)
    return default
 
 
def get_attribute_value(obj, attr_name, default=None, format= True):
    """
    Get the value of an attribute from an object.
    Supports dot notation for nested attributes.
    Supports ManyToOne / ManyToMany reverse relationships.
   
    Args:
        obj (object): The object to get the attribute from.
        attr_name (str): The name of the attribute to get.
        default: The default value to return if the attribute is not found.
       
    Returns:
        The value of the attribute or the default value.
    """
    if not obj:
        return default
   
    parts = attr_name.split('.')
    value = obj
    part = parts[0] if parts else None
    remaining_path = '.'.join(parts[1:])
   
    if isinstance(value, (BaseManager, QuerySet)):
        if attr_name:
            values_list = []
            for item in value.all():
                sub_value = get_attribute_value(item, attr_name, default, format=False)
                if sub_value is not default:
                    if isinstance(sub_value, list):
                        values_list.extend(sub_value)
                    else:
                        if format:
                            sub_value = format_attribute_value(sub_value, default)
                       
                        values_list.append(sub_value)
            return values_list if values_list else default
        else:
            return list(value.all())
       
    # Regular attribute
    if hasattr(value, part):
        value = getattr(value, part)
    # Dictionary support
    elif isinstance(value, dict) and part in value:
        value = value[part]
    # Special user_by_type_id logic
    elif hasattr(value, f'{part}_type') and hasattr(value, f'{part}_identifier'):
        value = user_by_type_id(
            getattr(value, f'{part}_type', None),
            getattr(value, f'{part}_identifier', None)
        )
 
    if remaining_path or isinstance(value, (BaseManager, QuerySet)):
        # Normal recursion
        value = get_attribute_value(value, remaining_path, default, format=False)  
       
    if format == True:
        value = format_attribute_value(value, default)
        return value
    else:
        return value

def replace_variables(pattern, text, context=None):
    """
    Replace variables in text with their values.
    
    Args:
        pattern (str): The regex pattern to match variables.
        text (str): The text containing variables.
        context (dict, optional): Dictionary containing objects or direct values.
        
    Returns:
        str: The text with variables replaced.
    """
    if context is None:
        context = {}
    
    missing_vars = []
    
    try:
        def replacer(match):
            var = match.group(1).strip()
            
            # Extract the object identifier and variable name
            if '.' in var:
                obj_id, var_name = var.split('.', 1)
            else:
                obj_id = var
                var_name = ''
                
            value = match.group(0)  # Default to keeping the original pattern
            
            # Try to get the value from the context
            if obj_id in context:
                obj = context[obj_id]
                if var_name:
                    # If we have a dotted path, use get_attribute_value
                    value = get_attribute_value(obj, var_name, None, format=False)
                    if value is None:
                        missing_vars.append(f"{obj_id}.{var_name}")
                        return value
                else:
                    # If there's no dotted path, use the object directly
                    value = str(obj) if obj is not None else None
                    
                if value is None:
                    missing_vars.append(var)
                    return match.group(0)
                return value
            else:
                missing_vars.append(var)
                return value
                
        result = re.sub(pattern, replacer, text)
        
        # If we have missing variables, raise an exception
        if missing_vars:
            error_msg = f"Failed to replace variables: {', '.join(missing_vars)}"
            raise Exception(error_msg)
            
        return result
    
    except Exception as e:
        log.error(f"Error replacing variables: {e}")
        raise Exception(f"Error replacing variables: {str(e)}")


def format_variables(text, context={}):
    """
    Format the message template by replacing variables with their values using Django template engine.
    
    Args:
        text (str): The text containing variables.
        context (dict or object, optional): Either a dictionary with 'user' and/or 'instance'
                                           keys, or a direct user or instance object.
        
    Returns:
        str: The formatted message.
    """
    if not text:
        return ""
    
    try:
        # Extract all variables from the text
        var_pattern = r'\(\(\s*(.*?)\s*\)\)'
        all_vars = re.findall(var_pattern, text)
        
        # Create a processed context with resolved values
        processed_context = dict(context)
        
        # Track variables that need to be transformed (dot to double underscore)
        transformed_vars = {}
        
        # Process each variable
        for var in all_vars:
            if '.' in var:
                obj_id, attr_path = var.split('.', 1)
                
                if obj_id in context:
                    # Get the base object
                    obj = context[obj_id]
                    
                    # Process the attribute path
                    parts = attr_path.split('.')
                    current_obj = obj
                    resolved_value = None
                    user_type_id_used = False
                    
                    for i, part in enumerate(parts):
                        # Special case: user_by_type_id
                        if hasattr(current_obj, f'{part}_type') and hasattr(current_obj, f'{part}_identifier'):
                            type_val = getattr(current_obj, f'{part}_type', None)
                            id_val = getattr(current_obj, f'{part}_identifier', None)
                            user_obj = user_by_type_id(type_val, id_val)
                            user_type_id_used = True
                            
                            # If this is the last part, use the user object
                            if i == len(parts) - 1:
                                resolved_value = user_obj
                            # Otherwise, continue with remaining parts on the user object
                            elif user_obj is not None:
                                current_obj = user_obj
                                continue
                            else:
                                break
                        # Regular attribute access
                        elif hasattr(current_obj, part):
                            current_obj = getattr(current_obj, part)
                            
                            # If we're at the end, this is our value
                            if i == len(parts) - 1:
                                resolved_value = current_obj
                        else:
                            break
                    
                    # Only add to processed context if user_by_type_id was used
                    if resolved_value is not None and user_type_id_used:
                        # Format datetime and date objects
                        if isinstance(resolved_value, datetime):
                            resolved_value = resolved_value + timedelta(hours=5, minutes=30)
                            resolved_value = resolved_value.strftime("%d-%m-%Y %H:%M:%S")
                        elif isinstance(resolved_value, date):
                            resolved_value = resolved_value.strftime("%d-%m-%Y")
                        elif resolved_value is not None:
                            resolved_value = str(resolved_value)
                        
                        # Create transformed variable name with double underscore
                        transformed_var = var.replace('.', '__')
                        transformed_vars[var] = transformed_var
                        
                        # Add to processed context with the transformed variable name
                        processed_context[transformed_var] = resolved_value
        
        # Create a modified template text with transformed variable names
        modified_text = text
        for original_var, transformed_var in transformed_vars.items():
            # Replace ((original.var)) with ((transformed__var))
            pattern = r'\(\(\s*' + re.escape(original_var) + r'\s*\)\)'
            modified_text = re.sub(pattern, f'(({transformed_var}))', modified_text)
        
        # Convert ((variable)) syntax to Django's {{variable}} syntax
        django_template_text = re.sub(r'\(\(\s*(.*?)\s*\)\)', r'{{ \1 }}', modified_text)
        
        # Import Django template engine
        from django.template import engines
        
        # Get the Django template engine
        django_engine = engines['django']
        
        # Create a template from the string
        template = django_engine.from_string(django_template_text)
        
        # Render the template with the processed context
        rendered_text = template.render(processed_context)
        
        # Check if any variables weren't replaced (would still have {{ }} syntax)
        if '{{' in rendered_text and '}}' in rendered_text:
            # Find all remaining variables
            remaining_vars = re.findall(r'{{(.*?)}}', rendered_text)
            if remaining_vars:
                error_msg = f"Failed to replace variables: {', '.join(var.strip() for var in remaining_vars)}"
                log.error(error_msg)
                raise Exception(error_msg)
        
        return rendered_text
    except Exception as e:
        log.error(f"Error formatting variables: {e}")
        raise Exception(f"Error formatting variables: {str(e)}")


def _is_iterable(obj):
    return isinstance(obj, Iterable) and not isinstance(obj, (str, bytes))

def format_print_data(template, instance_id):
    variables_data = template.variables_data or {}
    model = template.screen.model_class()

    if not model:
        return {"error": "Invalid model"}

    try:
        instance = model.objects.get(pk=instance_id)
    except model.DoesNotExist:
        return {"error": "Instance not found"}

    # Step 1: Add normal variables to a single dict
    output = {}
    for var in variables_data.get("variables", []):
        val = get_attribute_value(instance, var, format=False)
        if val is not None:
            output[var] = str(val)
    
    # Step 2: Add normal variables to a single dict
    for mul_var in variables_data.get("multi_variables", []):
        mul_var_name = mul_var.get("name")
        mul_output = {}
        for var in mul_var.get("variables", []):
            val = get_attribute_value(instance, var, format=False)
            if val is not None:
                mul_output[var] =str(val)
        output[mul_var_name] = json.dumps(mul_output)

    # Step 3: Add table variables
    for table in variables_data.get("table_variables", []):
        table_name = table.get("name")
        variable_list = table.get("variables", [])

        related = get_attribute_value(instance, table_name)
        if not related:
            continue

        # related = related.all() if hasattr(related, "all") else related # all method Handled in get_attribute_value
        if not _is_iterable(related):
            continue

        rows = []
        for item in related:
            row = [str(get_attribute_value(item, v, "", format=False)) for v in variable_list]
            rows.append(row)

        if rows:
            output[table_name] = rows

    # Step 4: Add svg variables
    for svg in variables_data.get("svg_variables", []):
        val = get_attribute_value(instance, svg)
        if val:
            try:
                if hasattr(val, 'path'):  # It's a file
                    with open(val.path, "rb") as svg_file:
                        encoded = base64.b64encode(svg_file.read()).decode("utf-8")
                        output[svg] = f"data:image/svg+xml;base64,{encoded}"
                elif isinstance(val, str):  # Inline SVG string
                    encoded = base64.b64encode(val.encode("utf-8")).decode("utf-8")
                    output[svg] = f"data:image/svg+xml;base64,{encoded}"
            except Exception:
                output[svg] = None
        else:
            output[svg] = None

    # Step 5: Add image variables
    for image in variables_data.get("image_variables", []):
        val = get_attribute_value(instance, image)
        if val and hasattr(val, 'path'):
            try:
                with open(val.path, "rb") as image_file:
                    encoded = base64.b64encode(image_file.read()).decode("utf-8")
                    mime_type = "image/png"
                    output[image] = f"data:{mime_type};base64,{encoded}"
            except Exception as e:
                output[image] = None
        else:
            output[image] = None

    # Step 3: Wrap in a list
    return [output]