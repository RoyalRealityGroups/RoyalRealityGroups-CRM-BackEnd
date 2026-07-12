import os
from django.conf import settings
import requests
from dynamic_preferences.registries import global_preferences_registry

from Core.Core.utils.formaters import format_mobile_number



GLOBAL_VARS = global_preferences_registry.manager().all()

apikey = GLOBAL_VARS.get('DoubleTick__KEY','')
Baseurl = GLOBAL_VARS.get('DoubleTick__URL','') #https://public.doubletick.io/whatsapp/message/
from_number = GLOBAL_VARS.get('DoubleTick__FROMNUMBER','')



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
        # print('=====================================================',e,)
        url = settings.GLOBAL_API_URL + "/static/images/thumbnail/default_no_file.png"

    # res = settings.MEDIA_URL + url
    res = url
    
    return res


def send_whatsapp_document_message(to,file_url,caption):

    url = Baseurl + "/document"
    
    payload = {
        "content": {
            "mediaUrl": file_url,
            "filename": "testing",
            "caption": caption
        },
        "from": from_number,
        "to": to
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": apikey
    }

    response = requests.post(url, json=payload, headers=headers)
    
    res = response.json()
    
    if response.status_code == 200:
        return True,"msg sent sucessfully"
    else:
        return False,res['message']



def send_whatsapp_template_message(to,template_name): 

    url = Baseurl + "/template"

    payload = { "messages": [
            {
                "content": {
                    "language": "en",
                    "templateName": template_name
                },
                "from": from_number,
                "to": to
            }
        ] }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": apikey
    }

    response = requests.post(url, json=payload, headers=headers)

    
    res = response.json()
    
    if response.status_code == 200:
        return True,"msg sent sucessfully"
    else:
        return False,res['message']
    


def send_whatsapp_catalog_links(obj):
    

    url = Baseurl + "/template"

    payload = { "messages": [
            {
                "content": {
                        "language": "en",
                        "templateData": {
                            "body": { "placeholders": [obj.name,obj.link,] }
                        },
                        "templateName": "link_test"
                    },
                "from": from_number,
                "to": format_mobile_number(obj.mobile)
            }
        ] }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": apikey
    }

    response = requests.post(url, json=payload, headers=headers)

    
    res = response.json()
    
    if response.status_code == 200:
        return True,"msg sent sucessfully"
    else:
        return False,res['message']
    

def send_purchase_invoice_link(obj):
    
    try:
        name = f'{obj.customer.firstname} {obj.customer.middlename} {obj.customer.lastname}'
    except (AttributeError, TypeError):
        name = obj.customer.first_name
        
    #----------------------------------------------------------------------------------
    
    try:
        date = obj.date.date().strftime("%d/%m/%Y")
    except (AttributeError, TypeError):
        date = obj.createdon.date().strftime("%d/%m/%Y")
        
    #----------------------------------------------------------------------------------
    
    try:
        docno = f'{name} {obj.vehicle.vehicleno} {date}'
    except (AttributeError, TypeError):
        docno = f'{name} {date}'
        
    #----------------------------------------------------------------------------------

    url = Baseurl + "/template"

    payload = { "messages": [
            {
                "content": {
                        "language": "en",
                        "templateData": 
                            {
                            "header": {
                                "type": "DOCUMENT",
                                "mediaUrl": build_abs_doc_url(obj.receipt_file),
                                "filename": docno
                            },
                            "body": { "placeholders": [name,docno,date,str(obj.total),'wheelsmart'] }
                        },
                        "templateName": "purchase_docuemen_send"
                    },
                "from": from_number,
                "to": format_mobile_number(obj.customer.mobile)
            }
        ] }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": apikey
    }

    response = requests.post(url, json=payload, headers=headers)

    
    res = response.json()
    
    if response.status_code == 200:
        return True,"msg sent sucessfully"
    else:
        return False,res['message']
    
    

def send_sale_invoice_link(obj):
    
    try:
        name = f'{obj.customer.firstname} {obj.customer.middlename} {obj.customer.lastname}'
    except (AttributeError, TypeError):
        name = obj.customer.first_name
        
    #----------------------------------------------------------------------------------
    
    try:
        date = obj.date.date().strftime("%d/%m/%Y")
    except (AttributeError, TypeError):
        date = obj.createdon.date().strftime("%d/%m/%Y")
        
    #----------------------------------------------------------------------------------
    
    try:
        docno = f'{name} {obj.vehicle.vehicleno} {date}'
    except (AttributeError, TypeError):
        docno = f'{name} {date}'
        
    #----------------------------------------------------------------------------------

    url = Baseurl + "/template"

    payload = { "messages": [
            {
                "content": {
                        "language": "en",
                        "templateData": 
                            {
                            "header": {
                                "type": "DOCUMENT",
                                "mediaUrl": build_abs_doc_url(obj.receipt_file),
                                "filename": docno
                            },
                            "body": { "placeholders": [name,docno,date,str(obj.total),'wheelsmart'] }
                        },
                        "templateName": "purchase_docuemen_send"
                    },
                "from": from_number,
                "to": format_mobile_number(obj.customer.mobile)
            }
        ] }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": apikey
    }

    response = requests.post(url, json=payload, headers=headers)

    
    res = response.json()
    
    if response.status_code == 200:
        return True,"msg sent sucessfully"
    else:
        return False,res['message']