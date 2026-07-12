from Core.Core.utils.formaters import format_print_data
from Core.Core.utils.utils import user_by_type_id
from Core.Reports.generic_import_export_view import GenericExportView
from rest_framework import generics, permissions
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import filters
from django_filters import DateFilter

from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import PdfTemplate, ReportRequest
from .serializers import PdfTemplateDataSerializer, PdfTemplateListCreateSerializer, PdfTemplateSerializer, ReportRequestSerializer
from django.shortcuts import get_object_or_404

from Core.Reports.models import ScheduledEmail
User = get_user_model()


from Core.Reports.generic_import_export_view import GenericExportView
from Core.Reports.serializers import ScheduledEmailSerializer


def create_scheduledemail(scheduledemailitem):

    class MockRequest:
        def __init__(self, data, user):
            self.data = data
            self.user = user
            self.query_params = {}
            self.method = 'POST'

    data = {
            'model_name': scheduledemailitem.reportname,
            'file_format': scheduledemailitem.fileformat,
            'response_type': 2, 
            'email': scheduledemailitem.email
        }
    # user = User.objects.get(id=1)
    user = user_by_type_id(scheduledemailitem.created_by_type, scheduledemailitem.created_by_id)
    mock_request = MockRequest(data=data, user=user)
    view = GenericExportView(request=mock_request)

    res= view.post(request=mock_request)

    if res.status_code == 201:
        print("Exported file sent via email.")
    else:
        print("Export failed:")



class ScheduledEmailFilter(FilterSet):

    start_date = DateFilter(field_name='createdon',lookup_expr=('gte'),) 
    end_date = DateFilter(field_name='createdon',lookup_expr=('lte'))

    class Meta:
        model = ScheduledEmail
        fields = ['start_date', 'end_date', 'frequency', 'fileformat',]


class ScheduledEmailList(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    serializer_class = ScheduledEmailSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_deleted=False, ).order_by('-id')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter,  filters.OrderingFilter]
    filterset_class = ScheduledEmailFilter
    search_fields = ['email','code', 'reportname']
    ordering_fields = ['code',]

    def perform_create(self, serializer):
        serializer.save()

class ScheduledEmailDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ScheduledEmailSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.all()

    def perform_update(self, serializer):
        serializer.save()
        
    def perform_destroy(self, instance):
        instance.is_deleted=True
        instance.save()




#     request_data = {
#         'file_format': scheduledemailitem.fileformat,
#         'responsetype': 1, 
#         'emailid': scheduledemailitem.email
#     }
    
# relativeLink = reverse('GenericExport')
#         absurl = 'http://'+current_site+relativeLink+"?token="+str(token)

#     def post(self, request):
#         user = request.data
#         serializer = self.serializer_class(data=user)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         user_data = serializer.data
#         user = User.objects.get(email=user_data['email'])
#         token = RefreshToken.for_user(user).access_token
#         current_site = get_current_site(request).domain
        
#         email_body = 'Hi '+user.username + \
#             ' Use the link below to verify your email \n' + absurl
#         data = {'email_body': email_body, 'to_email': user.email,
#                 'email_subject': 'Verify your email'}

#         Util.send_email(data)
#         return Response(user_data, status=status.HTTP_201_CREATED)
    

class PdfTemplateFilter(FilterSet):

    start_date = DateFilter(field_name='created_on',lookup_expr=('gte'),) 
    end_date = DateFilter(field_name='created_on',lookup_expr=('lte'))


    class Meta:
        model = PdfTemplate
        fields = ['start_date', 'end_date', 'screen', 'is_active',]


class PdfTemplateListCreate(generics.ListCreateAPIView):
    serializer_class = PdfTemplateListCreateSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_deleted=False, ).order_by('-id')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter,  filters.OrderingFilter]
    filterset_class = PdfTemplateFilter
    search_fields = ['screen_name', 'name']

    def perform_create(self, serializer):
        serializer.save()


class PdfTemplateDetails(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PdfTemplateListCreateSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.all()

    def perform_update(self, serializer):
        serializer.save()
        
    def perform_destroy(self, instance):
        instance.is_deleted=True
        instance.save()


class PdfTemplateListByModel(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, app_label, model_name):

        templates = PdfTemplate.objects.filter(screen__app_label=app_label, screen__model= model_name, is_active =True, is_deleted=False)
        serializer = PdfTemplateSerializer(templates, many=True)
        return Response(serializer.data)



class PdfTemplateData(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk, instance_id):
        template = get_object_or_404(PdfTemplate, pk=pk)
        serializer = PdfTemplateDataSerializer(template)
        data = serializer.data
        data['data'] = format_print_data(template, instance_id)
        return Response(data)

class ReportRequestFilter(FilterSet):
   
    class Meta:
        model = ReportRequest
        fields = ['unique_id','report_id','status', ]
 
 
class ReportRequestList(generics.ListAPIView):
    serializer_class = ReportRequestSerializer
    queryset = ReportRequest.objects.filter(is_deleted=False,).order_by('-created_on') # type=1
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code',  ]
    filterset_class = ReportRequestFilter
    ordering_fields = ['code','created_on']
 
    def get_queryset(self):
        instance = self.kwargs.get('report_id')  
        queryset = super().get_queryset()
        queryset=queryset.filter(report_id = instance)
        return queryset
   
 
 
class ReportRequestDetail(generics.RetrieveAPIView):
    serializer_class = ReportRequestSerializer
    queryset = ReportRequest.objects.filter(is_deleted=False)



    """
    List all available models for import.
    Uses the UserMenuSerializer to get menu items from MENU-002 (Import menu)
    with proper permission filtering.
    Returns items with model_name derived from menu item name.
    Supports search filtering via ?search=query parameter.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from Core.System.serializers import UserMenuSerializer
        
        # Get search query parameter
        search_query = request.query_params.get('search', '').strip().lower()
        
        # Get Import menu (MENU-002)
        try:
            import_menu = Menu.objects.get(code='MENU-002')
        except Menu.DoesNotExist:
            return Response([])
        
        # Use UserMenuSerializer to get menu items with permission filtering
        serializer = UserMenuSerializer(import_menu, context={'request': request})
        menu_data = serializer.data
        
        # Extract menu items (menuitems field contains permission-filtered items)
        menu_items = menu_data.get('menuitems', [])
        
        # Also get items from submenus if any
        for submenu in menu_data.get('submenus', []):
            menu_items.extend(submenu.get('menuitems', []))
        
        # Map menu item names to model names (remove spaces for model names)
        # e.g., "Superstockist Location" -> "SuperstockistLocation"
        for item in menu_items:
            item['model_name'] = item['name'].replace(' ', '')
        
        # Apply search filter if search query exists
        if search_query:
            filtered_items = []
            for item in menu_items:
                # Search in name and model_name (case-insensitive)
                if (search_query in item.get('name', '').lower() or 
                    search_query in item.get('model_name', '').lower()):
                    filtered_items.append(item)
            menu_items = filtered_items
        
        # Return in SearchableDropdown format (id, name, model_name)
        return Response(menu_items)


class ImportFieldsView(APIView):
    """
    Get field metadata for a specific model.
    Returns field info including mandatory status, data types, and help text.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, model_name):
        if model_name not in only_import_models:
            return Response(
                {'error': f'Model "{model_name}" not found or not available for import'},
                status=404
            )
        
        config = only_import_models[model_name]
        resource_class = config.get('resource_class')
        
        if not resource_class:
            return Response(
                {'error': f'No resource class configured for model "{model_name}"'},
                status=400
            )
        
        resource = resource_class()
        
        # Check if resource has get_field_info method
        if hasattr(resource, 'get_field_info'):
            fields = resource.get_field_info()
        else:
            # Fallback: generate field info from resource fields
            fields = []
            for field_name in resource.get_export_order():
                field = resource.fields.get(field_name)
                if field:
                    fields.append({
                        'field_name': field_name,
                        'display_name': field.column_name or field_name,
                        'is_mandatory': not getattr(field, 'saves_null_values', True),
                        'field_type': 'TEXT',
                        'help_text': '',
                    })
        
        return Response({
            'model_name': model_name,
            'fields': fields
        })


class ImportTemplateDownloadView(APIView):
    """
    Generate and download a CSV template for import.
    Accepts selected_fields as query params or all fields if not specified.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, model_name):
        if model_name not in only_import_models:
            return Response(
                {'error': f'Model "{model_name}" not found'},
                status=404
            )
        
        config = only_import_models[model_name]
        resource_class = config.get('resource_class')
        
        if not resource_class:
            return Response(
                {'error': f'No resource class configured for model "{model_name}"'},
                status=400
            )
        
        resource = resource_class()
        
        # Get selected fields from query params
        selected_fields_param = request.query_params.get('fields', '')
        selected_fields = [f.strip() for f in selected_fields_param.split(',') if f.strip()] if selected_fields_param else None
        
        # Get field info
        if hasattr(resource, 'get_field_info'):
            all_fields_info = resource.get_field_info()
        else:
            all_fields_info = [
                {'field_name': f, 'display_name': resource.fields.get(f).column_name if resource.fields.get(f) else f, 'is_mandatory': False, 'help_text': ''}
                for f in resource.get_export_order()
            ]
        
        # If selected_fields provided, filter but always include mandatory fields
        if selected_fields:
            mandatory_fields = [f['field_name'] for f in all_fields_info if f.get('is_mandatory')]
            fields_to_include = list(set(selected_fields + mandatory_fields))
            fields_info = [f for f in all_fields_info if f['field_name'] in fields_to_include]
            # Maintain original order
            fields_info.sort(key=lambda x: [f['field_name'] for f in all_fields_info].index(x['field_name']))
        else:
            fields_info = all_fields_info
        
        # Generate CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Header row with display names
        headers = [f['display_name'] for f in fields_info]
        writer.writerow(headers)
        
        # Example row with help text
        example_row = [f.get('help_text', '') for f in fields_info]
        writer.writerow(example_row)
        
        # Create response
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{model_name.lower()}_import_template.csv"'
        
        return response


class ImportHistoryListView(generics.ListAPIView):
    """
    List import history with pagination.
    Only shows actual imports (not dry runs/validations).
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        from Core.Reports.models import ImportRequest
        
        # Get pagination params
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        
        # Query import requests - only actual imports, not dry runs
        queryset = ImportRequest.objects.filter(is_dryrun=False).order_by('-created_on')
        
        # Paginate
        start = (page - 1) * page_size
        end = start + page_size
        
        total = queryset.count()
        items = queryset[start:end]
        
        results = []
        for item in items:
            results.append({
                'import_id': item.unique_id,
                'status': item.status,
                'status_display': self._get_status_display(item.status),
                'created_date': item.created_on,
                'screen_name': item.screen_name,
                'file_name': item.file_name,
                'total_records': item.total_records or 0,
                'new_records': item.new_records or 0,
                'updated_records': item.updated_records or 0,
                'error_records': item.error_records or 0,
            })
        
        return Response({
            'count': total,
            'page': page,
            'page_size': page_size,
            'results': results
        })
    
    def _get_status_display(self, status):
        # Status from model: 1=Pending, 2=Complete, 3=Failed
        status_map = {
            1: 'Pending',
            2: 'Completed',
            3: 'Failed',
        }
        return status_map.get(status, 'Unknown')


class ImportHistoryDetailView(APIView):
    """
    Get detailed import history for a specific import.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, import_id):
        from Core.Reports.models import ImportRequest
        
        try:
            item = ImportRequest.objects.get(unique_id=import_id)
        except ImportRequest.DoesNotExist:
            return Response({'error': 'Import not found'}, status=404)
        
        import json
        content = None
        if item.content:
            try:
                content = json.loads(item.content)
            except:
                content = item.content
        
        return Response({
            'import_id': item.unique_id,
            'status': item.status,
            'status_display': self._get_status_display(item.status),
            'created_date': item.created_on,
            'content': content,
        })
    
    def _get_status_display(self, status):
        status_map = {
            1: 'Processing',
            2: 'Failed', 
            3: 'Completed',
        }
        return status_map.get(status, 'Unknown')





