

import base64
from datetime import datetime
import json
import os

import subprocess
from django.conf import settings

from Core.Core.parser.Json_parser import FIELD_PARSERS


def model_to_dict(instance):
    """
    Convert a Django model instance into a dictionary, applying a parser
    for each field based on the field's class. FKs and M2M fields use
    the string representation of related objects here.
    """
    data = {}

    for field in instance._meta.get_fields():
        parser = FIELD_PARSERS.get(field.__class__.__name__, None)

        if field.is_relation:
            # If you'd prefer to handle relations separately (e.g., storing IDs),
            # you could do so here. But this example delegates to FIELD_PARSERS.
            # If there's no specialized parser for the relation, just use str
            if parser is None:
                # As a fallback, convert the related object(s) to string
                if field.many_to_many:
                    value = getattr(instance, field.name)
                    data[field.name] = ', '.join([str(obj) for obj in value.all()])
                elif field.one_to_one:
                    try:
                        value = getattr(instance, field.get_accessor_name())
                        data[field.name] = str(value) if value else None
                    except Exception:
                        data[field.name] = None
                elif field.one_to_many or field.many_to_one:
                    # Handle ForeignKey reverse relationships
                    try:
                        if hasattr(instance, field.get_accessor_name()):
                            value = getattr(instance, field.get_accessor_name())
                            if hasattr(value, 'all'):
                                # It's a manager (one-to-many)
                                data[field.name] = ', '.join([str(obj) for obj in value.all()[:5]])  # Limit to 5 items
                            else:
                                # It's a single object (many-to-one)
                                data[field.name] = str(value) if value else None
                        else:
                            data[field.name] = None
                    except Exception:
                        data[field.name] = None
                else:
                    value = getattr(instance, field.name)
                    data[field.name] = str(value) if value else None
            else:
                data[field.name] = parser(field, instance)
        else:
            # Regular (non-relation) field
            if parser:
                data[field.name] = parser(field, instance)
            else:
                # Fallback: just get the raw value
                data[field.name] = str(getattr(instance, field.name))

    return data


def focus_date_to_int(dt):
    year = dt.year
    month = dt.month
    day = dt.day
    
    int_value = (year * 65536) + (month * 256) + (day) 
    
    return int_value

def focus_int_to_date(int_val):
    year = int(int_val / 65536)
    month = int((int_val % 65536) / 256)
    day = int_val % 256

    return datetime(year, month, day)
    
def time_to_int(time_str):
    if ':' not in time_str:
        return 0
    elif time_str.count(':') == 1:
        time_str += ':00'
    
    hours = int(time_str[0:2])
    minutes = int(time_str[3:5])
    seconds = int(time_str[6:8])
    
    int_value = (hours * 0x10000) | (minutes * 0x100) | seconds
    
    return int_value

def time_to_focus_int(time_str):

    hours = int(time_str[0:2])
    minutes = int(time_str[3:5])
    # seconds = int(time_str[6:8])

    time_int = (hours * 0x10000) | (minutes * 0x100) # | seconds
    
    return time_int


def datetime_to_int(dt):
    year = dt.year
    month = dt.month
    day = dt.day
    hour = dt.hour
    minute = dt.minute
    second = dt.second
    
    int_value = (year * 8589934592) | (month * 33554432) | (day * 131072) | (hour * 4096) | (minute * 64) | second
    
    return int_value



    
def image_to_base64(image_file):
    try:
        # Read the image file as binary data
        image_binary = image_file.read()
        
        # Encode the binary data as Base64
        base64_data = base64.b64encode(image_binary).decode('utf-8')
        
        return base64_data
    except Exception as e:
        print("Error:", e)
        return ''
    
    
def convert_to_dict(response_str):
    response_str = response_str.replace("'", '"')  # Replace single quotes with double quotes
    print('Replace single quotes with double quotes',response_str)
    response_str = response_str.replace('None', 'null')  # Replace None with null if necessary
    print('Replace None with null if necessary',response_str)

    try:
        response_dict = json.loads(response_str)
        print('json loads',response_dict)
        return response_dict
    except Exception as e:
        print("JSON decode error:", e)


def build_abs_doc_url(obj):
    try:
        url = obj.url

        file_name = os.path.basename(obj.name)

        media_dir_path = os.path.join(settings.BASE_DIR, 'media', 'temp')

        if not os.path.exists(media_dir_path):
            os.makedirs(media_dir_path)

        media_path = os.path.join(media_dir_path, file_name)

        with open(media_path, 'wb') as f:
            for chunk in obj.chunks():
                f.write(chunk)


        url = settings.GLOBAL_API_URL + '/media/temp/' + file_name
    except Exception as e:
        print('=====================================================',e,)
        url = settings.GLOBAL_API_URL + "/static/images/thumbnail/default_no_file.png"

    # res = settings.MEDIA_URL + url
    res = url
    
    return res


def generate_pdf_via_node(template_path, data_path, output_path):
    # print(f"Generating PDF using Node.js script with template: {template_path}, data: {data_path}, output: {output_path}")

    try:
        # Absolute path to Node.js script
        node_script_path = os.path.abspath('./Core/node/pdf.js')

        # Build the command
        command = [
            'node', node_script_path,
            template_path,
            data_path,
            output_path
        ]

        # print(f"Running command: {' '.join(command)}")

        # Run the command
        result = subprocess.run(command, capture_output=True, text=True)

        # print(f"Node.js return code: {result.returncode}")
        # print("Node.js stdout:")
        # print(result.stdout)
        # print("Node.js stderr:")
        # print(result.stderr)

        # Check result
        if result.returncode != 0:
            raise Exception(f"Node script failed with return code {result.returncode}: {result.stderr}")

        # Check if output file exists
        # print(f"Checking if output file exists: {output_path}")
        if not os.path.exists(output_path):
            # List directory contents for debugging
            # print("Current directory listing:")
            # print(os.listdir(os.path.dirname(output_path)))
            raise Exception("PDF was not generated at expected location.")

        # print(f"✅ PDF successfully generated at: {output_path}")
        return output_path

    except FileNotFoundError as fnf_error:
        print(f"Node.js or script not found: {fnf_error}")
        return None

    except Exception as e:
        print(f"Error in generate_pdf_via_node: {e}")
        return None
