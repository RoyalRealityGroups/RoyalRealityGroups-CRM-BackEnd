 
from django.http import HttpResponse, JsonResponse, FileResponse
from django.utils.encoding import force_str
from django.core.files import File
 
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import  GenericAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
 
 
from import_export.formats import base_formats
from import_export.resources import modelresource_factory
from import_export.tmp_storages import TempFolderStorage
from import_export.results import RowResult
from import_export.mixins import ExportViewMixin
 
import pandas as pd
import threading
import time
from io import BytesIO
from django.core.files.base import ContentFile
 
from Core.Core.permissions.DataPermissions import get_data_permission_functions
from Core.Core.permissions.permissions import GetPermission
from Core.Core.utils.utils import Util
from Core.Reports.models import ImportRequest, ReportRequest
 
import json
import random
 
import pandas as pd
import threading

 
from django.utils.functional import Promise
from django.utils.encoding import force_str
from django.core.serializers.json import DjangoJSONEncoder
 
 
from Core.Reports.serializers import GenericImportExportSerializer, GenericImportSerializer, GenericConfirmImportSerializer, GenericExportSerializer
from .import_export_models import only_import_models, only_export_models
 
 
from Core.Users.models import DataPermissions, AssigneeDefnition, Assignee
 
get_qs, get_dp_qs =  get_data_permission_functions( DataPermissions, AssigneeDefnition, Assignee)
 
 
 
def get_model_class(model_name):
   
    model = None
    resource_class = None
    resource = None
    permissions = []
   
    import_models = only_import_models
    if model_name in import_models.keys() :
        print('model_name:', model_name)
        model = import_models[model_name]['model_class']
        if 'resource_class' in import_models[model_name].keys():
            resource_class = import_models[model_name]['resource_class']
            resource =  resource_class()
        if 'permissions' in import_models[model_name].keys():
            permissions = import_models[model_name]['permissions']
 
    if resource_class == None and model != None:
        resource_class =  modelresource_factory(model)
        resource =  resource_class()
 
   
 
    return (model, resource, permissions)
 
 
 
class GenericExportModelsView(APIView):
    permission_classes = [IsAuthenticated]
   
    def get(self, request, *args, **kwargs):
        export_models = only_export_models
        models = export_models.keys()
        return Response(models)
 
 
class GenericImportModelsView(APIView):
    permission_classes = [IsAuthenticated]
   
    def get(self, request, *args, **kwargs):
        import_models = only_import_models
        models = import_models.keys()
        return Response(models)
   
class LazyEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_str(obj)
        return super(LazyEncoder, self).default(obj)


import re

def strip_html_tags(value):
    """Remove HTML tags from a string value."""
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    # Remove HTML tags like <ins>, <del>, <span>, etc.
    clean_value = re.sub(r'<[^>]+>', '', str(value))
    return clean_value


def get_display_value(value, resource, field_name):
    """
    Convert a value to its display representation.
    For foreign keys, this returns both the code and the name.
    """
    if value is None:
        return None
    
    # First strip any HTML tags from the value
    clean_value = strip_html_tags(value)
    
    # Check if this field is a ForeignKey by looking at the resource fields
    try:
        for field in resource.get_fields():
            if field.column_name == field_name or field.attribute == field_name:
                # Check if this field uses ForeignKeyWidget
                if hasattr(field, 'widget') and hasattr(field.widget, 'model'):
                    # This is a foreign key field
                    fk_model = field.widget.model
                    fk_field = getattr(field.widget, 'field', 'pk')
                    
                    # Try to find the related object
                    try:
                        related_obj = fk_model.objects.filter(**{fk_field: clean_value}).first()
                        if related_obj:
                            # Return both code and name for display
                            name = getattr(related_obj, 'name', str(related_obj))
                            return f"{clean_value} ({name})"
                    except Exception:
                        pass
                break
    except Exception:
        pass
    
    return clean_value
           

def start_import(request_id, request, resource, cleaned_data, input_format, data, import_file_name, tmp_storage_name, model, dryrun):
    formats = base_formats.DEFAULT_FORMATS
    obj = None
    
    try:
        # For dry run (validation), create a temporary record to store results
        # For actual import, create a permanent history record
        is_actual_import = (dryrun == 'process')
        
        obj = ImportRequest.objects.create(
            unique_id=request_id,
            status=1,
            screen_name=model._meta.verbose_name.title() if model else None,
            file_name=import_file_name,
            is_dryrun=not is_actual_import,
        )
    except Exception as e:
        print(f'Error creating ImportRequest: {type(e).__name__}: {e}')
        # Try to create a minimal ImportRequest to record the failure
        try:
            obj = ImportRequest.objects.create(
                unique_id=request_id,
                status=3,  # Failed
                screen_name=model._meta.verbose_name.title() if model else 'Unknown',
                file_name=import_file_name,
                is_dryrun=not (dryrun == 'process'),
                content=json.dumps({"error": f"Failed to initialize import: {type(e).__name__}: {e}"})
            )
        except Exception as inner_e:
            print(f'Failed to create error ImportRequest: {type(inner_e).__name__}: {inner_e}')
        return False
    
    try:
       
        try:
            dataset = input_format.create_dataset(data)
            result = resource.import_data(dataset, dry_run=True, raise_errors=False, file_name=import_file_name, )  # Test the import data
        except Exception as e:
            print('e',e)
            obj.content= json.dumps({"error":"%s : %s , encountered while trying to read file: %s" % (type(e).__name__, e, import_file_name,)})
            obj.status = 3  # Failed
            obj.save()
            return False
 
        context = {}
        context['has_errors'] = result.has_errors()
        context['has_validation_errors'] = result.has_validation_errors()
 
        # Filter diff_headers to only include columns actually present in CSV
        # Check if resource has _csv_headers (set by before_import)
        if hasattr(resource, '_csv_headers') and resource._csv_headers:
            # Only include headers that are in the uploaded CSV
            context['diff_headers'] = [h for h in result.diff_headers if h in resource._csv_headers]
        else:
            context['diff_headers'] = result.diff_headers
       
        context['app_label'] = model._meta.app_label
        context['model_name'] = model._meta.model_name
        context['verbose_name'] = model._meta.verbose_name
        context['verbose_name_plural'] = model._meta.verbose_name_plural
       
        print('context', context)
 
        if context['has_errors']:
            context['base_errors'] = []
            context['row_errors'] = []
            for error in result.base_errors:
               
                e = error.error
                e = "%s : %s " % (type(e).__name__, e)
                t = error.traceback,
                t = list(t)
               
                context['base_errors'].append({
                    "error": t,
                    "traceback": t,
                })
            for line, errors in result.row_errors():
                out_errors =[]
                for error in errors:
                    r = error.row.values()
                    r = list(r)
                    e = error.error
                    e = "%s : %s " % (type(e).__name__, e)
                    t = error.traceback,
                    t = list(t)
                    out_errors.append({
                        "error": e,
                        "traceback": t,
                        "row": r,
                    })
                   
                context['row_errors'].append({
                    "line": line,
                    "errors": out_errors,
                })
            # Update error count
            obj.error_records = len(context.get('row_errors', []))
        elif context['has_validation_errors']:
            context['invalid_rows'] = []
            for row in result.invalid_rows:
                error_list_data = {}
                for field_name, error_list in row.field_specific_errors.items():
                    error_list_data[field_name] = error_list
                if row.non_field_specific_errors:
                    error_list_data["non_field_specific_errors"] = row.non_field_specific_errors
 
                row_data ={
                    "row": row.number,
                    "errors":{
                        "error_count": row.error_count,
                        "error_list":error_list_data
                    }
                }
                for i in  range(len(result.diff_headers)):
                    field_name = result.diff_headers[i]
                    raw_value = row.values[i]
                    # Get display value with resolved FK names
                    display_value = get_display_value(raw_value, resource, field_name)
                    row_data[field_name] = display_value


                context['invalid_rows'].append(row_data)
            # Update error count
            obj.error_records = len(context.get('invalid_rows', []))
        elif dryrun == 'dryrun':
            context['valid_rows'] = []
            for row in result.valid_rows():
                row_data ={
                    "import_type": row.import_type,
                }
                for i in range(len(result.diff_headers)):
                    field_name = result.diff_headers[i]
                    raw_value = row.diff[i]
                    # Get display value with resolved FK names
                    display_value = get_display_value(raw_value, resource, field_name)
                    row_data[field_name] = display_value
                context['valid_rows'].append(row_data)
 
            initial = {
                'import_file_name': tmp_storage_name,
                'original_file_name': import_file_name,
                'input_format': cleaned_data['input_format'],
            }
            context['initial'] = initial
            
            # Count totals for dry run preview
            new_count = sum(1 for row in result.valid_rows() if row.import_type == RowResult.IMPORT_TYPE_NEW)
            update_count = sum(1 for row in result.valid_rows() if row.import_type == RowResult.IMPORT_TYPE_UPDATE)
            obj.total_records = len(context.get('valid_rows', []))
            obj.new_records = new_count
            obj.updated_records = update_count
        elif dryrun == 'process':
            result = resource.import_data(dataset, dry_run=False, raise_errors=True, file_name=import_file_name, )  # Import the data from the file
           
            tmp_storage = TempFolderStorage(name=import_file_name)
            tmp_storage.remove()
            opts = model._meta
            
            # Store import counts
            new_count = result.totals.get(RowResult.IMPORT_TYPE_NEW, 0)
            update_count = result.totals.get(RowResult.IMPORT_TYPE_UPDATE, 0)
            obj.new_records = new_count
            obj.updated_records = update_count
            obj.total_records = new_count + update_count
            
            context['success_message'] = 'Import finished, with {} new and ' \
                    '{} updated {}.'.format(new_count, update_count, opts.verbose_name_plural)
            context['new_records'] = new_count
            context['updated_records'] = update_count
 
        print('context1', context)
       
        o = json.dumps(context, cls=LazyEncoder)
 
        # o = json.dumps( deepcopy(context))
        print('context2', context)
 
        obj.content= o
 
        print('context3', context)
 
        obj.status = 2  # Complete
        obj.save()
       
        return True
    except Exception as e:
 
        print(e)
        obj.content= json.dumps({"error":"{} : {} , parameters request_id: {}, request: {}, resource: {}, cleaned_data: {}, model: {}, dryrun: {}, ".format(type(e).__name__, e, request_id, request, resource, cleaned_data, model, dryrun)})
        obj.status = 3  # Failed
        obj.error_records = 1
        obj.save()
        return False
 
def start_import_thread(request_id, request, resource, cleaned_data, model, dryrun):
    thread = threading.Thread(target=start_import, args=(request_id, request, resource, cleaned_data, model, dryrun))
    thread.start()
   
 
class GenericImportView(APIView):
    permission_classes = [IsAuthenticated]
    # serializer_class = GenericImportSerializer
    formats = base_formats.DEFAULT_FORMATS
    from_encoding = "utf-8"
 
   
    def write_to_tmp_storage(self, import_file, input_format):
        tmp_storage = TempFolderStorage()
        data = bytes()
        for chunk in import_file.chunks():
            data += chunk
 
        tmp_storage.save(data) # , input_format.get_read_mode()
        return tmp_storage
 
    def post(self, request, *args, **kwargs):
        # file_obj = request.data['import_file']
        dryrun = kwargs['dryrun']
       
        model = None
        resource = None
        permissions = []
        if permissions is None:
            permissions = []
 
        # dataset = Dataset()
        import_formats = [f for f in self.formats if f().can_import()]
 
       
        serializer = GenericImportExportSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            model_name = serializer.validated_data['model_name']
            model, resource, permissions = get_model_class(model_name)
 
        if model is None:
            return Response({"error":"Invalid Model type" }, status=400)
       
        permissions = permissions + [ GetPermission(model._meta.app_label + ".import_"+ model._meta.model_name) ]
        for permission in permissions:
            if permission().has_permission(request, self):
                permission_check = True
               
        if not permission_check:
            return Response({"error":"You do not have permission to perform this action." }, status=403)
             
 
        if resource is None:
            return Response({"error":"Invalid Model Resource type" }, status=400)
 
        if dryrun == 'dryrun':
            serializer = GenericImportSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                cleaned_data = serializer.validated_data
        elif dryrun == 'process':
            serializer = GenericConfirmImportSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                cleaned_data = serializer.validated_data
        else:
            cleaned_data = {}
            return Response({"error":"Invalid Dryrun type" }, status=400)
       
        try:
            input_format = import_formats[
                cleaned_data['input_format']
            ]()
 
            if dryrun == 'dryrun':
                import_file = cleaned_data['import_file']
                tmp_storage = self.write_to_tmp_storage(import_file, input_format)
                import_file_name = import_file.name
                tmp_storage_name = tmp_storage.name
            if dryrun == 'process':
                tmp_storage = TempFolderStorage(name=cleaned_data['import_file_name'])
                import_file_name = cleaned_data['import_file_name']
                tmp_storage_name = tmp_storage.name
               
 
            data = tmp_storage.read() # input_format.get_read_mode()
            if not input_format.is_binary() and self.from_encoding:
                data = force_str(data, self.from_encoding)
           
        except UnicodeDecodeError as e:
            return JsonResponse({"error":"Imported file has a wrong encoding: %s" % e })
        except Exception as e:
            return JsonResponse({"error":"%s : %s , encountered while trying to read file: " % (type(e).__name__, e)})
           
 
        # except UnicodeDecodeError as e:
        #     obj.content= json.dumps({"error":"Imported file has a wrong encoding: %s" % e })
        #     obj.status = 2
        #     obj.save()
        #     return False
       
        # except Exception as e:
        #     obj.content= json.dumps({"error":"%s : %s , encountered while trying to read file" % (type(e).__name__, e,)})
        #     obj.status = 2
        #     obj.save()
        #     return False
       
        current_time = int(time.time())
        random_int = random.randint(0, 99)
        request_id = f"{current_time}_{random_int}"
       
        thread = threading.Thread(target=start_import, args=(request_id, request, resource, cleaned_data, input_format, data, import_file_name, tmp_storage_name, model, dryrun))
        thread.start()
       
        # thread = ImportThread(request_id, self, resource, cleaned_data, model, dryrun )
        # thread.start()
        # start_import_thread(request_id, self, resource, cleaned_data, model, dryrun )
       
        return Response({ "message": "Started Importing/Validation", "request_id": request_id }, status=200)
 
class ImportThread(threading.Thread):
    def __init__(self, request_id, request, resource, cleaned_data, model, dryrun):
        self.status = 0
        self.request_id = request_id
        self.request = request
        self.resource = resource
        self.cleaned_data = cleaned_data
        self.model = model
        self.dryrun = dryrun
       
        threading.Thread.__init__(self)
 
    def run(self):
        start_import(self.request_id, self.request, self.resource, self.cleaned_data, self.model, self.dryrun)
         
 
def generate_report(self, file_format, queryset):
    export_data = self.get_export_data(file_format, queryset)
    content_type = file_format.get_content_type()
    file_name = self.get_export_filename(file_format)
   
    return export_data, content_type, file_name
 
class ReportThread(threading.Thread):
    def __init__(self, request,request_id , file_format, queryset,report_id):
        self.status = 0
        self.request_id = request_id
        self.report_id = report_id
        self.request = request
        self.file_format = file_format
        self.queryset = queryset
        self.export_data = None
        self.content_type = None
        self.file_name = None
       
        threading.Thread.__init__(self)
 
    def run(self):
 
        obj = ReportRequest.objects.filter(unique_id=self.request_id).first()
        if not obj:
            obj = ReportRequest.objects.create(
                unique_id=self.request_id,
                report_id=self.report_id,
                status=1
            )
 
        export_data, content_type, file_name = generate_report(self.request, self.file_format, self.queryset)
       
        if isinstance(export_data, str):
            # export_file = File(BytesIO(export_data.encode()))
            export_file = ContentFile(export_data.encode(), name=file_name)
        else:
            # export_file = File(BytesIO(export_data))
            export_file = ContentFile(export_data, name=file_name)
 
        obj.file_name = file_name
        obj.file= export_file
        obj.content_type= content_type
        obj.status = 2
        obj.save()
       
 
def start_generate_report(request,request_id, file_format, queryset, report_id):
 
    print(request,request_id, file_format)
 
    thread = ReportThread(request,request_id, file_format, queryset, report_id)
    thread.start()
 
 
def get_export_model_class(model_name):
   
    model = None
    resource_class = None
    filter_backends = None
    queryset = None
    post_queryset = None
    filterset_class = None
    search_fields = None
    ordering_fields = None
    request_filters = []
    permissions = []
 
    export_models = only_export_models
    if model_name in export_models.keys() :
        model = export_models[model_name]['model_class']
        if 'resource_class' in export_models[model_name].keys():
            resource_class = export_models[model_name]['resource_class']
        if 'queryset' in export_models[model_name].keys():
            queryset = export_models[model_name]['queryset']
        if 'post_queryset' in export_models[model_name].keys():
            post_queryset = export_models[model_name]['post_queryset']
        if 'filter_backends' in export_models[model_name].keys():
            filter_backends = export_models[model_name]['filter_backends']
        if 'filterset_class' in export_models[model_name].keys():
            filterset_class = export_models[model_name]['filterset_class']
        if 'search_fields' in export_models[model_name].keys():
            search_fields = export_models[model_name]['search_fields']
        if 'ordering_fields' in export_models[model_name].keys():
            ordering_fields = export_models[model_name]['ordering_fields']
        if 'request_filters' in export_models[model_name].keys():
            request_filters = export_models[model_name]['request_filters']
        if 'permissions' in export_models[model_name].keys():
            permissions = export_models[model_name]['permissions']
           
 
    if resource_class == None and model != None:
        resource_class =  modelresource_factory(model)
 
    return (model, resource_class, queryset, post_queryset, filter_backends, filterset_class, search_fields, ordering_fields, request_filters, permissions)
 
class GenericExportView(GenericAPIView, ExportViewMixin):
    permission_classes = [IsAuthenticated]
    formats = base_formats.DEFAULT_FORMATS
    LONG_DATA_THRESHOLD = 10000
 
    def post(self, request, *args, **kwargs):
        model_name = ''
        report_id = ''
        serializer = GenericImportExportSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            model_name = serializer.validated_data['model_name']
            model, resource_class, queryset, post_queryset, filter_backends, filterset_class, search_fields, ordering_fields, request_filters, permissions = get_export_model_class(model_name)
 
        if model is None:
            return Response({"error": "Invalid Model type"}, status=400)
 
        permission_check = False
        if permissions is None:
            permissions = []
 
        permissions = permissions + [GetPermission(model._meta.app_label + ".export_" + model._meta.model_name),
                                     GetPermission(model._meta.app_label + ".reports_" + model._meta.model_name)]
        for permission in permissions:
            if permission().has_permission(request, self):
                permission_check = True
 
        if not permission_check:
            return Response({"error": "You do not have permission to perform this action."}, status=403)
 
        if resource_class is None:
            return Response({"error": "Invalid Model Resource type"}, status=400)
 
        if queryset is None:
            return Response({"error": "Queryset not Defined"}, status=400)
 
        self.model = model
        self.resource_class = resource_class
        queryset = queryset
        user = request.user
 
        if not user.is_superuser: #and not user.has_perm('System.all_data')
            app_label = model._meta.app_label
            model_name = model._meta.model_name
            queryset = get_qs(app_label, model_name, queryset, user, screen_type = 'report')
 
        for request_filter in request_filters:
            queryset = request_filter(request, queryset)
 
        if filter_backends is not None:
            self.filter_backends = filter_backends
        if filterset_class is not None:
            self.filterset_class = filterset_class
        if search_fields is not None:
            self.search_fields = search_fields
        if ordering_fields is not None:
            self.ordering_fields = ordering_fields
        if post_queryset is not None and callable(post_queryset):
            self.post_queryset = post_queryset
 
        serializer = GenericExportSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            cleaned_data = serializer.validated_data
 
 
        formats = self.get_export_formats()
 
        file_format = formats[int(cleaned_data['file_format'])]()
        response_type = int(cleaned_data.get('response_type', 0))
        email = cleaned_data.get('email', None)
 
        if hasattr(self, 'filter_queryset'):
            queryset = self.filter_queryset(queryset)
 
        if hasattr(self, 'post_queryset'):
            queryset = post_queryset(queryset, request)
 
       
        if int(cleaned_data['file_format']) == 5: # JSON
            count = queryset.count()
            page = self.paginate_queryset(queryset)
 
            if page is not None:
                queryset=page
 
            export_data = self.get_export_data(file_format, queryset)
            content_type = file_format.get_content_type()
           
            req_data = "{\"count\": "+str(count)+", \"results\": " + export_data + "}"
           
            return HttpResponse(req_data, content_type= content_type)
 
        elif response_type == 2:
           
            export_data = self.get_export_data(file_format, queryset)
            content_type = file_format.get_content_type()
            file_name = self.get_export_filename(file_format)
            attachment = (file_name, export_data, content_type)
            email_subject = f"Scheduled Report: {file_name}"
            email_body = f"Please find the attached {model_name} report."
            data = {'email_subject': email_subject, 'email_body': email_body, 'to_email': email}
 
            Util.send_email(data, attachments=[attachment])
 
            return Response({"message": "Exported file sent via email."}, status=status.HTTP_201_CREATED)
       
        else:
            current_time = int(time.time())
            random_int = random.randint(0, 99)
            request_id = f"{current_time}_{random_int}"
            report_id = model_name
            count = queryset.count()
            # Create the ReportRequest upfront so status checks never hit None
            ReportRequest.objects.create(
                unique_id=request_id,
                report_id=report_id,
                status=1
            )
            start_generate_report(self, request_id, file_format, queryset, report_id)
            return JsonResponse({'message': "Started generating report","request_id":request_id,"is_long_query": count > self.LONG_DATA_THRESHOLD,"report_id":report_id}, status=201)
       
 
class DownloadExportView(GenericAPIView):
    permission_classes = [IsAuthenticated]
 
    def post(self, request, *args, **kwargs):
        request_id = kwargs.get('request_id')
 
        try:
            obj = ReportRequest.objects.get(unique_id=request_id)
        except ReportRequest.DoesNotExist:
            return JsonResponse({'message': "ID Does Not Exist", 'status': False}, status=404)
 
        if not obj.file:
            return JsonResponse({'message': "File not available", 'status': False}, status=400)
 
        response = FileResponse(obj.file.open('rb'), content_type=obj.content_type)
        response['Content-Disposition'] = f'attachment; filename="{obj.file_name}"'
 
        return response
 
 
class CheckExportView(GenericAPIView,ExportViewMixin):
    permission_classes = [IsAuthenticated]
    formats = base_formats.DEFAULT_FORMATS
 
    def post(self, request, *args, **kwargs):
       
        request_id = kwargs['request_id']
 
        try:
            obj=ReportRequest.objects.filter(unique_id=request_id).first()
            if not obj:
                return JsonResponse({'message': "ID Does Not Exist",'status': False}, status=404)
            print("obj",obj)
            if obj.status == 2:
                return JsonResponse({'message': "Report is Completed",'status': True}, status=201)
            else:
                return JsonResponse({'message': "Report is generating",'status': False}, status=202)
 
        except Exception as e:
            return JsonResponse({'message': "ID Does Not Exist",'status': False, 'error': str(e)}, status=404)
       
 
#  New_import type get_model_class_serializers  2
class CheckImportView(GenericAPIView,ExportViewMixin):
    permission_classes = [IsAuthenticated]
    formats = base_formats.DEFAULT_FORMATS
 
    def post(self, request, *args, **kwargs):
       
        request_id = kwargs['request_id']
 
        try:
            obj = ImportRequest.objects.filter(unique_id=request_id).first()
            print("obj", obj)
            if not obj:
                return JsonResponse({'message': "ID Does Not Exist", 'status': False}, status=404)

            if obj.status == 2:
                payload = {}
                try:
                    payload = json.loads(obj.content) if obj.content else {}
                except Exception:
                    payload = {'raw_content': obj.content}
                return JsonResponse({'message': payload, 'status': True}, status=201)

            if obj.status == 3:
                payload = {}
                try:
                    payload = json.loads(obj.content) if obj.content else {}
                except Exception:
                    payload = {'raw_content': obj.content}
                return JsonResponse(
                    {
                        'message': payload.get('error') or payload or 'Import failed',
                        'status': False,
                        'failed': True,
                    },
                    status=200,
                )

            return JsonResponse({'message': 'Import is still running', 'status': False}, status=202)
 
        except Exception as e:
            return JsonResponse({ 'message': "ID Does Not Exist",'status': False }, status=404)
 
 
 
def get_model_class_2(model_name):
   
   
    model = None
    SerializerClass = None
    queryset = None
   
    import_models = only_import_models
    if model_name in import_models.keys() :
        print('model_name:', model_name)
        model = import_models[model_name]['model_class']
        SerializerClass = import_models[model_name].get('serializer_class', None )
        queryset = import_models[model_name].get('queryset', None )
        if import_models[model_name].get('import_type',1) == 1:
            model = None
 
 
    return (model, SerializerClass, queryset)
 
 
 
 
class ImportView(APIView):
    permission_classes = [AllowAny]
    # permission_classes = [IsAuthenticated]
 
    # SerializerClass = GenericImportSerializer
    formats = base_formats.DEFAULT_FORMATS
    from_encoding = "utf-8"
 
   
    def write_to_tmp_storage(self, import_file, input_format):
        tmp_storage = TempFolderStorage()
        data = bytes()
        for chunk in import_file.chunks():
            data += chunk
 
        tmp_storage.save(data) # , input_format.get_read_mode()
        return tmp_storage
 
   
    def format_row(self, index, row, import_fields, outobj={}, Notfoundlist=[]):
        for field in import_fields:
            try:
                if field.get("is_serializer", False) and not field.get("is_serializer_many", False): # if many False
                    Notfoundlist, outobj[field["key"]] = self.format_row(index, row, field["serializer_fields"], {}, Notfoundlist)
 
                elif field.get("is_serializer", False) and field.get("is_serializer_many", False): # if many True
                    Notfoundlist, obj = self.format_row(index, row, field["serializer_fields"], {}, Notfoundlist)
                    outobj[field["key"]] = [obj,]
 
                elif field.get("is_many_to_many", False):
                    value = row[field["label"]]
                    if value != '':
                        value = value.split(',')
                    else:
                        value = []
                    outobj[field["key"]] = value
                else:
                    outobj[field["key"]] = row[field["label"]]
 
            except KeyError:
                Notfoundlist.append(field["label"])
       
        # print(index, len(Notfoundlist))
        return (Notfoundlist, outobj )
 
    def get_field_by_key(self, import_fields, key):
        return next((sub for sub in import_fields if sub['key'] == key), None)
 
    def get_instance(self, queryset, import_fields, SerializerClass, row):
        params = {}
        NotFoundKeys2 = []
        for key in self.get_import_id_fields(SerializerClass):
            try:
                field = self.get_field_by_key(import_fields, key)
                params[key] = row[field["label"]]
            except KeyError:
                NotFoundKeys2.append(field["label"])
        if params and len(NotFoundKeys2) ==0:
            try:
                return queryset.get(**params), NotFoundKeys2
            except:
                return None, NotFoundKeys2
        else:
            return None, NotFoundKeys2
 
    def get_import_id_fields(self, SerializerClass):
        if hasattr(SerializerClass.Meta, "import_id_fields"):
            return SerializerClass.Meta.import_id_fields
        else:
            return ( 'id', )
 
    def import_dataframe(self, model, SerializerClass, queryset, request, df, import_fields, dryrun= True ):
        data_list = []
        has_errors = False
        for index, row in df.iterrows():
            NotFoundKeys, data_obj = self.format_row(index, row, import_fields, {}, [] )
            # queryset = State.objects.all()
            instance, NotFoundKeys2 = self.get_instance(queryset, import_fields, SerializerClass, row)
            # print("instance", instance)
           
            serializer_context = { 'request' : request }
 
            if len(NotFoundKeys2) > 0:
                has_errors = True
            serializer = SerializerClass(data= data_obj, instance= instance, many= False, context= serializer_context )
            is_valid = serializer.is_valid(raise_exception=False)
            if not is_valid :
                has_errors = True
            elif dryrun == False and has_errors == False:
                serializer.save()
           
            data_list.append({
                # "input": data_obj,
                "import_status":  "New" if instance == None else "Update" ,
                "has_errors": not is_valid,
                "errors": serializer.errors,
                "validated_data": serializer.validated_data,
                "output_data": serializer.data,
                "keys_notfound": NotFoundKeys,
                "import_id_keys_notfound": NotFoundKeys2,
            })
        return (data_list, has_errors)
       
    def post(self, request, *args, **kwargs):
        dryrun = kwargs['dryrun']
       
        model = None
        SerializerClass = None
        queryset = None

        import_formats = [f for f in self.formats if f().can_import()]
        
        serializer = GenericImportExportSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            model_name = serializer.validated_data['model_name']
            model, SerializerClass, queryset = get_model_class_2(model_name)
           
        if model is None:
            return Response({"error":"Invalid Model type" }, status=400)
        
        
        # permission = GetPermission(model._meta.app_label + ".import_"+ model._meta.model_name)()
        # if not permission.has_permission(request, self):
        #     return Response({"error":"You do not have permission to perform this action." }, status=403)


        if SerializerClass is None:
            return Response({"error":"Invalid Model Serializer type" }, status=400)

        if dryrun == 'dryrun':
            serializer = GenericImportSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                cleaned_data = serializer.validated_data
        elif dryrun == 'process':
            serializer = GenericConfirmImportSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                cleaned_data = serializer.validated_data
        else:
            cleaned_data = {}
            return Response({"error":"Invalid Dryrun type" }, status=400)

        try:
            input_format = import_formats[
                cleaned_data['input_format']
            ]()
            # import_file = cleaned_data['import_file']
            # tmp_storage = self.write_to_tmp_storage(import_file, input_format)
            # import_file_name = import_file.name
            # data = tmp_storage.read('r')
            
            if dryrun == 'dryrun':
                import_file = cleaned_data['import_file']
                tmp_storage = self.write_to_tmp_storage(import_file, input_format)
                import_file_name = import_file.name
                original_file_name = import_file.name
            if dryrun == 'process':
                tmp_storage = TempFolderStorage(name=cleaned_data['import_file_name'])
                import_file_name = cleaned_data['import_file_name']
                original_file_name = cleaned_data['original_file_name']
            

            import_fields = SerializerClass.Meta.import_fields

            df = pd.read_csv(tmp_storage.get_full_path() ,keep_default_na = '')
            
        except UnicodeDecodeError as e:
            return JsonResponse({"error":"Imported file has a wrong encoding: %s" % e })
        except Exception as e:
            return JsonResponse({"error":"%s : %s , encountered while trying to read file: %s" % (type(e).__name__, e, import_file_name)})
        
        data_list, has_errors = self.import_dataframe( model, SerializerClass, queryset, request, df, import_fields, dryrun = True )
        # print(data_list)
        initial= {
            'import_file_name': tmp_storage.name,
            'original_file_name': original_file_name,
            'input_format': cleaned_data['input_format'],
        }
        if dryrun == 'process' and has_errors == False:
            data_list = self.import_dataframe( model, SerializerClass, queryset, request, df, import_fields, dryrun = False )

            
        # print("data_list", data_list)

        return Response( {'initial': initial, 'data_list': data_list, "import_fields" : import_fields, "has_errors" : has_errors})
