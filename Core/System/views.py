from django.core import management
from django.http import HttpResponse
from django.db.models.deletion import RestrictedError
from django.http import HttpResponseRedirect

from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from rest_framework import filters
from django_filters import DateFilter
from django_filters.filters import Filter

from dynamic_preferences.registries import global_preferences_registry 
from dynamic_preferences.api.viewsets import GlobalPreferencesViewSet

from django.utils import timezone
import datetime
import time
import json 


from django.contrib.auth import get_user_model

from Core.Core.authentication.Authentication import JWTAuthentication
from Core.Core.permissions.permissions import GetIOPermission, GetPermission
from Core.Users.models import Device
from Core.System.task_thread_manager import TaskThreadManager,active_threads
User = get_user_model()

from Core.Core.utils.utils import Util, calculate_next_run

from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import filters

from rest_framework import generics, status, permissions
from Core.System.models import Menuitem

from Core.Core.utils.utils import removeDuplicates
from Core.Core.lexer.LexerBySly import formula_validator,formula_executer

from .models import Menu, RecentActivity, Submenu, Menuitem, Notification, Attachment, Backup, Restore, Formula, FormulaUpdate, ActivityLog, NotificationUsers, TaskScheduler, TemporaryVerification, Setting, AlertConfig, Template
from .serializers import EmailTemporaryOTPRequestSerializer, EmailTemporaryVerifyOTPSerializer, MenuSerializer, MenuitemSerializer2, RecentActivitySerializer, SubmenuSerializer, MenuitemSerializer, TaskSchedulerSerializer, UserMenuSerializer, NotificationSerializer, BackupSerializer, RestoreSerializer, AttachmentSerializer, ResetDatabaseSerializer, FormulaSerializer, FormulaValidationSerializer, FormulaValidation2Serializer, FormulaUpdateSerializer, ActivityLogSerializer, ActivityLogMiniSerializer, SmsSerializer, ErrorSerializer, BackupValidationserializer, TemporaryOTPRequestSerializer, TemporaryVerifyOTPSerializer, DownloadSerializer, AlertConfigSerializer, AnnouncementSerializer, AuditLogSerializer,  TemplateMiniSerializer, TemplateSerializer
from .services import get_dependent_models, get_preferences, send_alert_email, send_alert_sms


from rest_framework.response import Response


from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.response import Response
from django.db.models import Q, Prefetch

from rest_framework import  status
from Users.models import User

from Core.System.management.forms import UserForm
from django.contrib import messages


from Core.System.socketio_app import maintenance_mode

class UserMenuList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserMenuSerializer

    def get_queryset(self):
        user = self.request.user
        all_menus = Menu.objects.filter(is_deleted=False).order_by('name')

        # Superuser / no-permission fallback: return everything, eagerly prefetched.
        if user.is_superuser:
            return all_menus.prefetch_related(
                'submenus',
                Prefetch('submenus__menuitems', queryset=Menuitem.objects.filter(is_deleted=False)),
                Prefetch('menuitems', queryset=Menuitem.objects.filter(is_deleted=False, submenu__isnull=True)),
            )

        user_permissions = set(user.get_all_permissions())

        if not user_permissions:
            # No perms assigned -> show everything.
            return all_menus.prefetch_related(
                'submenus',
                Prefetch('submenus__menuitems', queryset=Menuitem.objects.filter(is_deleted=False)),
                Prefetch('menuitems', queryset=Menuitem.objects.filter(is_deleted=False, submenu__isnull=True)),
            )

        # ponytail: 1 query to fetch every menuitem + its permission FK, then Python filter.
        # Was: ~M*(1+S) queries (~150 for typical menu trees).
        items = (
            Menuitem.objects
            .filter(is_deleted=False)
            .select_related('permission')
            .values_list(
                'menu_id',
                'permission__content_type__app_label',
                'permission__codename',
            )
        )

        accessible_menu_ids = set()
        for menu_id, app_label, codename in items:
            if app_label is None or codename is None:
                # No permission gate -> accessible to anyone.
                accessible_menu_ids.add(menu_id)
                continue
            perm_str = f"{app_label}.{codename}"
            if perm_str in user_permissions:
                accessible_menu_ids.add(menu_id)

        return (
            all_menus
            .filter(id__in=accessible_menu_ids)
            .prefetch_related(
                'submenus',
                Prefetch('submenus__menuitems', queryset=Menuitem.objects.filter(is_deleted=False)),
                Prefetch('menuitems', queryset=Menuitem.objects.filter(is_deleted=False, submenu__isnull=True)),
            )
        )
   

class UserMenuDetail(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Menu.objects.all().order_by('name')
    serializer_class = UserMenuSerializer

class UserMenuDetailByCode(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Menu.objects.all().order_by('name')
    serializer_class = UserMenuSerializer
    lookup_field = 'code'


class MenuList(generics.ListCreateAPIView):
    queryset = Menu.objects.filter(is_deleted=False, ).order_by('name')
    serializer_class = MenuSerializer

    def perform_create(self, serializer):
        serializer.save()

class MenuDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer

    def perform_update(self, serializer):
        serializer.save( modified_on= datetime.datetime.now())


class SubmenuList(generics.ListCreateAPIView):
    queryset = Submenu.objects.filter(is_deleted=False, ).order_by('name')
    serializer_class = SubmenuSerializer

    def perform_create(self, serializer):
        serializer.save()

class SubmenuDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Submenu.objects.all()
    serializer_class = SubmenuSerializer

    def perform_update(self, serializer):
        serializer.save( modified_on= datetime.datetime.now())


class MenuitemList(generics.ListCreateAPIView):
    queryset = Menuitem.objects.filter(is_deleted=False, ).order_by('-id')
    serializer_class = MenuitemSerializer

    def perform_create(self, serializer):
        serializer.save()

class MenuitemList2(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MenuitemSerializer2
    filter_backends = [filters.SearchFilter]
    search_fields = ['name','menu__name','submenu__name']
    
    def get_queryset(self):
        user = self.request.user
        queryset = Menuitem.objects.filter(is_deleted = False)
        if not user.is_superuser:
            queryset = queryset.filter(
                Q(permission__user=user) |
                Q(permission__group__user=user)
            ).distinct()
            
        return queryset.select_related('permission','menu','submenu').order_by('-id')

class MenuitemDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Menuitem.objects.all()
    serializer_class = MenuitemSerializer

    def perform_update(self, serializer):
        serializer.save(modified_on= datetime.datetime.now())

class NotificationFilter(FilterSet):
    start_date = DateFilter(field_name='created_on', lookup_expr='gte')
    end_date = DateFilter(field_name='created_on', lookup_expr='lte')
    class Meta:
        model = Notification
        fields = ['start_date', 'end_date', 'message_priority','notification_type']

class NotificationList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = NotificationFilter
    search_fields = ['subject', 'body', 'type']
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_superuser:
            queryset = Notification.objects.filter(is_deleted=False)
        else:
            queryset = Notification.objects.filter(is_deleted=False, notificationusers__seen= 0, notificationusers__user_identifier= self.request.user.id) #  user_type=user_type,
        return queryset.order_by('-created_on')
        

class NotificationClear(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    model = serializer_class.Meta.model
    queryset = Notification.objects.all()
    
    def update(self, request, *args, **kwargs ):
        user = request.user
        notification = self.get_object()
        obj = NotificationUsers.objects.filter(user_identifier=user.id, notification=notification, ).update(seen=1, seen_time = timezone.now()) #  user_type=user_type,
        return Response({}, status=status.HTTP_200_OK)
        

class NotificationClearAll(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
 
    def post(self, request, *args, **kwargs):
        user = request.user
        if user.is_superuser:
            updated_count = NotificationUsers.objects.filter(seen=False).update(seen=True,seen_time=timezone.now())
        else:
            updated_count = NotificationUsers.objects.filter(user_identifier=user.id,seen=False).update(seen=True,seen_time=timezone.now())
        return Response(
            {"message": f"{updated_count} notifications marked as seen."},
            status=status.HTTP_200_OK
        )

def CreateBackup(user):
    
    timestr = time.strftime("%Y%m%d%H%M%S")
    filename = "DATABASE_BACKUP_" + timestr + ".psql.bin.gz"
    
    management.call_command('dbbackup', compress=True, interactive=False, output_filename=filename)

    serializer = BackupSerializer(data={ "name": filename, })
    if serializer.is_valid(raise_exception=True):
        serializer.save(created_by=user) 

def RestoreBackup(user, filename):
    CreateBackup(user)

    
    management.call_command('dbrestore', database='default', uncompress=True, interactive=False, input_filename=filename)
    management.call_command('migrate',)
    
    serializer = RestoreSerializer(data={ "name": filename, })
    if serializer.is_valid(raise_exception=True):
        serializer.save(created_by=user) 


class BackupNow(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BackupSerializer
        
    def get(self, request, format=None):
        try:
            CreateBackup(self.request.user)
            return Response({ }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({ }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


      
class BackupList(generics.ListAPIView):
    queryset = Backup.objects.filter(is_deleted=False, ).order_by('-id')
    serializer_class = BackupSerializer
    permission_classes = [IsAuthenticated]

class BackupValidation(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BackupValidationserializer
    queryset = Backup.objects.filter(is_deleted=False, ).order_by('-id')
        
    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = BackupValidationserializer(obj,data=request.data,context={'request': request})
        if serializer.is_valid(raise_exception=True):
            data = serializer.validated_data
       
        return Response(serializer.data, status=status.HTTP_200_OK)    
        

  
class RestoreList(generics.ListAPIView):
    queryset = Restore.objects.filter(is_deleted=False, ).order_by('-id')
    serializer_class = RestoreSerializer
    permission_classes = [IsAuthenticated]
    
    
class RestoreNow(generics.UpdateAPIView):
    queryset = Backup.objects.all().order_by('-id')
    serializer_class = BackupSerializer
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            RestoreBackup(self.request.user, instance.name)
            return Response({ }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({ }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class ResetDatabase(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ResetDatabaseSerializer
    queryset = Backup.objects.filter(is_deleted=False, ).order_by('-id')
        
    def post(self, request, *args, **kwargs):
        try:
            CreateBackup(request.user)
        except Exception as e:
            return Response({"error": "Failed to Create Backup"}, status=200)    

        dryrun = kwargs['dryrun']
        
        serializer_context = { 'request' : request }
        serializer = ResetDatabaseSerializer(data=request.data, context=serializer_context)
        if serializer.is_valid(raise_exception=True):
            data = serializer.validated_data

        apps = []
        successmodels = []
        failedmodels = []
        all_dependent_models = {}

        for contenttype in data['contenttype_ids']:
            model_class = contenttype.model_class()
            models = get_dependent_models(model_class)
            # models.append(model_class)
            models = removeDuplicates(models)
            all_dependent_models[model_class._meta.verbose_name] = []
            
            for model in models:
                if dryrun == 'dryrun':

                    all_dependent_models[model_class._meta.verbose_name].append(model._meta.verbose_name)

                elif dryrun == 'process':
                    apps.append(model._meta.app_label)
                    try:
                        model.objects.all().delete()
                        successmodels.append(model._meta.verbose_name)
                    except RestrictedError as e:
                        failedmodels.append(model._meta.verbose_name)

        if dryrun == 'dryrun':
            return Response({"all_dependent_models": all_dependent_models }, status=200)

        elif dryrun == 'process':
            apps = removeDuplicates(apps)
            sequenceresetres =management.call_command('sqlsequencereset', *apps, database='default')
            return Response({ "successmodels": successmodels, "failedmodels": failedmodels,  }, status=status.HTTP_200_OK)

        else:
            return Response({"error":"Invalid Dryrun type" }, status=400)




class AttachmentCreate(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Attachment.objects.all().order_by('-id')
    serializer_class = AttachmentSerializer

    def perform_create(self, serializer):
        serializer.save()

class AttachmentDetail(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Attachment.objects.all().order_by('-id')
    serializer_class = AttachmentSerializer


class AllFormulasList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FormulaSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter( is_deleted=False, ).order_by('-id')
    pagination_class = None

    def perform_create(self, serializer):
        serializer.save()


class FormulaList(generics.ListCreateAPIView):
    serializer_class = FormulaSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter( is_deleted=False, ).order_by('-id')

    def perform_create(self, serializer):
        serializer.save()

class FormulaDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FormulaSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.all()

    def perform_update(self, serializer):
        serializer.save()
        
    def perform_destroy(self, instance):
        instance.status=3
        instance.save()


class DynamicSettings(GlobalPreferencesViewSet):
    lookup_field='section__name'
        
    def get(self, request, format=None):
        try:
            data = global_preferences_registry.manager().all()

            if data['COMPANY__LOGO'] != None:
                data['COMPANY__LOGO'] = data['COMPANY__LOGO'].url
            # else:
            #     url = "static/images/thumbnail/default_no_file.png"
            #     data['COMPANY__LOGO'] = request.build_absolute_uri(url)

            if data['COMPANY__SMALLLOGO'] != None:   
                data['COMPANY__SMALLLOGO'] = data['COMPANY__SMALLLOGO'].url
            # else:
            #     url = "static/images/thumbnail/default_no_file.png"
            #     data['COMPANY__SMALLLOGO'] = request.build_absolute_uri(url)

            return Response(data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({ }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# class FormulaVariablesList(generics.ListCreateAPIView):
#     serializer_class = FormulaVariablesSerializer
#     model = serializer_class.Meta.model
#     queryset = model.objects.filter( is_deleted=False, ).order_by('-id')

#     def perform_create(self, serializer):
#         serializer.save()

# class FormulaVariablesDetail(generics.RetrieveUpdateDestroyAPIView):
#     serializer_class = FormulaVariablesSerializer
#     model = serializer_class.Meta.model
#     queryset = model.objects.all()

#     def perform_update(self, serializer):
#         serializer.save()
        
#     def perform_destroy(self, instance):
#         instance.status=3
#         instance.save()






class FormulaValidator(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FormulaValidationSerializer

    def create(self, request, *args, **kwargs):  
        serializer = FormulaValidationSerializer(data=request.data, )
        if serializer.is_valid(raise_exception=True):
            data = serializer.validated_data
        
        formula = data['formula']

        res = formula_validator( formula, )

        return Response(res, status = status.HTTP_200_OK)


class FormulaExecuter(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FormulaValidation2Serializer

    def create(self, request, *args, **kwargs):  
        serializer = FormulaValidation2Serializer(data=request.data, )
        if serializer.is_valid(raise_exception=True):
            data = serializer.validated_data
        
        code = data['code']
        variables = data['variables']

        formula = Formula.objects.filter(code = code)[0].formula
        
        res = formula_executer( formula, variables)

        return Response(res, status = status.HTTP_200_OK)



class FormulaUpdateList(generics.RetrieveAPIView):
    queryset = FormulaUpdate.objects.all()
    serializer_class = FormulaUpdateSerializer
    
    def retrieve(self, request, *args, **kwargs):
        instance = FormulaUpdate.objects.filter( formula = kwargs['pk'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class ActivityLogFilter(FilterSet):

    class Meta:
        model = ActivityLog
        fields = ['screen_name', 'type', 'instance_id', 'user_type', 'user_identifier']


class ActivityLogMini(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ActivityLogMiniSerializer
    pagination_class= None
    model = serializer_class.Meta.model
    queryset = model.objects.filter( is_deleted=False, ).only('id','screen_name').order_by('screen_name')
    filter_backends = [DjangoFilterBackend, ]
    filterset_class = ActivityLogFilter
    
class ActivityLogList(generics.ListAPIView):
    serializer_class = ActivityLogSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter( is_deleted=False, ).order_by('-id')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ActivityLogFilter
    search_fields = ['screen_name', ]
    ordering_fields = ['id','created_on']

    # def perform_create(self, serializer):
    #     user = self.request.user

    #     serializer.save(user=user)
        
    # def get_queryset(self):
    #     user = self.request.user
    #     queryset = ActivityLog.objects.filter(is_deleted=False )

    #     return queryset.order_by('-id')




class ActivityLogDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ActivityLogSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.all()

    def perform_update(self, serializer):
        serializer.save()
        
    def perform_destroy(self, instance):
        instance.status=3
        instance.save()

class AuditLogList(generics.ListAPIView):
    permission_classes = [GetPermission('System.can_view_audit_logs')]
    serializer_class = AuditLogSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter( is_deleted=False, ).order_by('-created_on')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ActivityLogFilter
    search_fields = ['tablename', ]
    ordering_fields = ['id',]

class ActivityLogByProjectListView(generics.ListAPIView):
    serializer_class = ActivityLogSerializer
    def get_queryset(self):
        project_id = self.kwargs.get('project_id')
        return ActivityLog.objects.filter(data__project__id=project_id)

class SmsList(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SmsSerializer
    
    def get(self, request, format=None):
        serializer = SmsSerializer()
        return Response({
            'messages':[
                # SMS.welcome_touser + SMS.postfix,
                # SMS.purchase_create_customer + SMS.postfix,
                # SMS.sale_create_customer + SMS.postfix,
                # SMS.salequotation_create_customer + SMS.postfix,
                # SMS.purchasequotation_create_customer + SMS.postfix,
                # SMS.ovfquotation_create_customer + SMS.postfix,
                # SMS.enquiry_create_customer + SMS.postfix,
            ]
        } )

    def post(self, request, format=None):
        serializer = SmsSerializer(data=request.data,)

        if serializer.is_valid(raise_exception=True):

            Util.send_sms(serializer.data)

        return Response(status=status.HTTP_204_NO_CONTENT)




class ErrorList(generics.ListAPIView):
    serializer_class = ErrorSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.order_by('-id')


class ActivityLogByUser(generics.ListAPIView):
    serializer_class = ActivityLogSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ActivityLogFilter
    search_fields = ['user__username',]
    ordering_fields = ['id', 'login','device','user','logout']

    def get_queryset(self, **kwargs):
        return ActivityLog.objects.filter(user_identifier=self.kwargs['pk'],  is_deleted= False).order_by('-created_on')

    # def get_queryset(self):
    #     user_id = self.kwargs.get('pk')  # Avoid KeyError
    #     if user_id:
    #         return ActivityLog.objects.filter(user=user_id, is_deleted=False).order_by('-id')
    #     return ActivityLog.objects.none()  # Return an empty queryset if no user ID is found
    

class ActivityLogByUserListView(generics.ListAPIView):
    serializer_class = ActivityLogSerializer
    def get_queryset(self):
        user = self.request.user
        view_all = self.request.query_params.get("view_all")
        queryset = ActivityLog.objects.filter(is_deleted=False)
        if not user.is_superuser:
            queryset = queryset.filter(user_identifier=user.id)

        queryset = queryset.order_by('-created_on')
        if view_all != "true":
            queryset = queryset[:10]

        return queryset
        

global_preferences = global_preferences_registry.manager()


class Maintenance_On(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        # global_preferences.set('DEVLOPER__MAINTENANCEMODE', False)
        # # maintenance_mode(True)
        # Otokens=OutstandingToken.objects.exclude(user__is_superuser = True)
        # for Otoken in Otokens:
        #     try:
        #         RefreshToken(Otoken.token).blacklist()
        #     # except:
        #     #     print("RefreshToken")
        #     except Exception as e:
        #         print("%s : %s " % (type(e).__name__, e, ))
        #         pass
         
        return Response({'message':'Maintenance Mode Enable'},status=status.HTTP_200_OK )




class Maintenance_Off(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        # global_preferences['DEVLOPER__MAINTENANCEMODE'] = False
        # maintenance_mode(False)
        return Response({'message':'Maintenance Mode Disable'},status=status.HTTP_200_OK )



def RestoreById(request,id):
    context={}
    if request.method=='POST':
        output=request.POST.get('output')
        if output=='YES':
            file=Backup.objects.get(id=id)
            filename=file.name
            management.call_command('dbrestore', database='default', uncompress=True, interactive=False, input_filename=filename)
            management.call_command('migrate',)
            serializer = RestoreSerializer(data={ "name": filename, })
            if serializer.is_valid(raise_exception=True):
                serializer.save()
            messages.add_message(request, messages.INFO, 'Successfully Restored into Database')   
            return HttpResponseRedirect("/admin/System/backup/")
        else:
            messages.add_message(request, messages.INFO, 'Not Restored into Database') 
            return HttpResponseRedirect("/admin/System/backup/")
    return render(request, "Restorecheckbox.html",{'form':UserForm})


def DownloadById(request, id):
    context = {}
    filename = None

    if request.method == 'POST':
        output = request.POST.get('output')

        if output == 'YES':
            file = Backup.objects.get(id=id)
            filename = file.name

            # Download the file
            with open(filename, 'rb') as file_content:
                response = HttpResponse(file_content.read(), content_type='application/force-download')
                response['Content-Disposition'] = f'attachment; filename={filename}'

                # Save download information
                serializer = DownloadSerializer(data={"name": filename})
                if serializer.is_valid(raise_exception=True):
                    serializer.save()

                messages.add_message(request, messages.INFO, 'Successfully Downloaded File')
                return response
        else:
            messages.add_message(request, messages.INFO, 'Not Downloaded File')
            return HttpResponseRedirect("/admin/System/backup/")

    return render(request, "DownloadById.html", {'filename': filename})


class IO_LogIn(APIView):
    permission_classes = [GetIOPermission()]
    
    def post(self, request, format=None):
        data=request.data

        access_token = data['access_token']
        device_uuid = data['device_uuid']
        
        try :
            jwtauthentication = JWTAuthentication()
            validated_token = jwtauthentication.get_validated_token(access_token)
            user = jwtauthentication.get_user(validated_token)

            if user :           
                devices=Device.objects.filter(user=user,uuid= device_uuid)
                if devices:
                    devices.update( socket = data['sid'], )

                    maintenance_mode(global_preferences['DEVLOPER__MAINTENANCEMODE'], user)

                    return Response({
                        'payload': { 'status':'success','data':'Socket Login successfully'}
                    },status=status.HTTP_200_OK )      
                else :               
                    return Response({
                        'payload': {'status':'failed','data':'login failed'}
                    },status=status.HTTP_200_OK )
            else:
                return Response({
                    'payload': {'status':'failed','data':'login failed'}
                },status=status.HTTP_200_OK )
        except :        
            return Response({
                'payload': {'status':'failed','data':'login failed'}
            },status=status.HTTP_200_OK )
            
            
class IO_LogOut(APIView):
    permission_classes = [GetIOPermission(),]
    
    def post(self, request, format=None):
        data=request.data
        Device.objects.filter(socket = data['sid'],).update( socket = '' )
        return Response({'payload': { 'status':'success','data':'Socket Logout successfully'}},status=status.HTTP_200_OK )


class TemporaryOTPRequestView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = TemporaryOTPRequestSerializer

    def get_queryset(self):
        return User.objects.filter(status= 1).order_by('-id')

class TemporaryVerifyOTPView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = TemporaryVerifyOTPSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'Message': 'Phone Number Verified'}, status=status.HTTP_200_OK)


class TemporaryOTPResendView(APIView):
    permission_classes = [AllowAny]
    serializer_class = TemporaryOTPRequestSerializer
        
    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        mobile = serializer.validated_data['mobile']
        instance = get_object_or_404(TemporaryVerification, mobile=mobile)
        
        message = Template.objects.get(name='OTP Verification').message
        send_alert_sms([{'phone': instance.mobile,'otp':instance.otp}],message)

        return Response({'message':'OTP Send successfully'},status=status.HTTP_200_OK )
    

class EmailTemporaryOTPRequestView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = EmailTemporaryOTPRequestSerializer
    
    def get_queryset(self):
        return User.objects.filter(status= 1).order_by('-id')


class EmailTemporaryVerifyOTPView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = EmailTemporaryVerifyOTPSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'Message': 'Email Verified'}, status=status.HTTP_200_OK)


class EmailTemporaryOTPResendView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = EmailTemporaryOTPRequestSerializer
        
    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        instance = get_object_or_404(TemporaryVerification, email=email, type=2)
        
        
        email_body = Template.objects.get(name='Email OTP Verification').message
        send_alert_email([{'email': instance.email,'otp':instance.otp}],email_body)

        return Response({'message':'OTP Send successfully'},status=status.HTTP_200_OK )


 
 
    
class CustomerAppJsonDataView(APIView):
    permission_classes= [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    def get(self, request, *args, **kwargs):

        GLOBAL_VARS = global_preferences_registry.manager().all()

        helplinephone = GLOBAL_VARS['CUSTOMERAPP__HELPLINEPHONE']
        helplineemail = GLOBAL_VARS['CUSTOMERAPP__HELPLINEEMAIL']
        maxdeliverydays = GLOBAL_VARS['CUSTOMERAPP__MAXIMUMDELIVERYDAYS']
        cutofftime = GLOBAL_VARS['CUSTOMERAPP__CUTOFFTIME']
        recentorderdeactivatecount = GLOBAL_VARS['CUSTOMERAPP__RECENTORDERDEACTIVATECOUNT']
    
        return Response({
            'helplinephone': helplinephone,
            'helplineemail': helplineemail,
            'maxdeliverydays': maxdeliverydays,
            'cutofftime': cutofftime,
            'recentorderdeactivatecount': recentorderdeactivatecount
        }, status=status.HTTP_200_OK)
    
        
    def put(self, request, *args, **kwargs):
        global_preferences = global_preferences_registry.manager()
        updated_data = {}
        errors = {}

        if 'helplinephone' in request.data:
            phone = request.data['helplinephone']
            if phone.isdigit() and len(phone) >= 10:
                global_preferences['CUSTOMERAPP__HELPLINEPHONE'] = phone
                updated_data['helplinephone'] = phone
            else:
                errors['helplinephone'] = 'Invalid phone number format.'

        if 'helplineemail' in request.data:
            email = request.data['helplineemail']
            try:
                validate_email(email)
                global_preferences['CUSTOMERAPP__HELPLINEEMAIL'] = email
                updated_data['helplineemail'] = email
            except ValidationError:
                errors['helplineemail'] = 'Invalid email format.'

        if 'maxdeliverydays' in request.data:
            try:
                days = int(request.data['maxdeliverydays'])
                if days > 0:
                    global_preferences['CUSTOMERAPP__MAXIMUMDELIVERYDAYS'] = str(days)
                    updated_data['maxdeliverydays'] = days
                else:
                    errors['maxdeliverydays'] = 'Maximum delivery days must be a positive integer.'
            except ValueError:
                errors['maxdeliverydays'] = 'Invalid value for maximum delivery days.'

        if 'cutofftime' in request.data:
            time = request.data['cutofftime']
            if ':' in time and len(time.split(':')) == 2:
                global_preferences['CUSTOMERAPP__CUTOFFTIME'] = time
                updated_data['cutofftime'] = time
            else:
                errors['cutofftime'] = 'Invalid time format. Use HH:MM.'

        if 'recentorderdeactivatecount' in request.data:
            try:
                count = int(request.data['recentorderdeactivatecount'])
                if count > 0:
                    global_preferences['CUSTOMERAPP__RECENTORDERDEACTIVATECOUNT'] = str(count)
                    updated_data['recentorderdeactivatecount'] = count
                else:
                    errors['recentorderdeactivatecount'] = 'Maximum recent order deactivate count must be a positive integer.'
            except ValueError:
                errors['recentorderdeactivatecount'] = 'Invalid value for recent order deactivate count.'

        if errors:
            return Response({
                'error': 'Some fields could not be updated.',
                'details': errors,
                'updated_fields': updated_data
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'message': 'Customer app settings updated successfully.',
            'updated_fields': updated_data
        }, status=status.HTTP_200_OK)


class DeliveryAppCallManagerView(APIView):
    permission_classes= [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    def get(self, request, *args, **kwargs):

        GLOBAL_VARS = global_preferences_registry.manager().all()

        callmanager = GLOBAL_VARS['DELIVERYAPP__MOBILENUMBER']
    
        return Response({'callmanager': callmanager}, status=status.HTTP_200_OK)
    
    def put(self, request, *args, **kwargs):
        new_number = request.data.get('callmanager')
        
        if not new_number:
            return Response({'error': 'Please provide a mobile number.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not new_number.isdigit() or len(new_number) < 10:
            return Response({'error': 'Invalid phone number format.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            global_preferences = global_preferences_registry.manager()
            global_preferences['DELIVERYAPP__MOBILENUMBER'] = new_number
            return Response({'message': 'Manager number updated successfully.', 'manager number': new_number}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Failed to update manager number: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
              


class SyncJsonDataView(APIView):
    permission_classes= [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    def get(self, request, *args, **kwargs):

        GLOBAL_VARS = global_preferences_registry.manager().all()

        enable_auto_sync = GLOBAL_VARS['THIRDPARTY__ENABLE_AUTOSYNC']

        amcu_enable_auto_sync = GLOBAL_VARS['THIRDPARTY__AMCU_ENABLE_AUTOSYNC']

        focus_base_url = GLOBAL_VARS['THIRDPARTY__FOCUS_BASEURL']
        focus_username = GLOBAL_VARS['THIRDPARTY__FOCUS_USERNAME']
        focus_password = GLOBAL_VARS['THIRDPARTY__FOCUS_PASSWORD']
        focus_companycode = GLOBAL_VARS['THIRDPARTY__FOCUS_COMPANY_CODE']
        focus_sync_on = GLOBAL_VARS['THIRDPARTY__FOCUS_SYNC_ON']

        amcu_api_key = GLOBAL_VARS['THIRDPARTY__AMCU_API_KEY']
        amcu_username = GLOBAL_VARS['THIRDPARTY__AMCU_PASSWORD']
        amcu_password = GLOBAL_VARS['THIRDPARTY__AMCU_USERNAME']
        amcu_baseurl = GLOBAL_VARS['THIRDPARTY__AMCU_BASEURL']
        amcu_sync_on = GLOBAL_VARS['THIRDPARTY__AMCU_SYNC_ON']

    
        return Response({
            'enable_auto_sync': enable_auto_sync,
            'amcu_enable_auto_sync': amcu_enable_auto_sync,

            'focus_base_url': focus_base_url,
            'focus_username': focus_username,
            'focus_password': focus_password,
            'focus_companycode': focus_companycode,
            'focus_sync_on': focus_sync_on,

            'amcu_api_key': amcu_api_key,
            'amcu_username': amcu_username,
            'amcu_password': amcu_password,
            'amcu_baseurl': amcu_baseurl,
            'amcu_sync_on': amcu_sync_on

        }, status=status.HTTP_200_OK)
    
        
    def put(self, request, *args, **kwargs):
        global_preferences = global_preferences_registry.manager()
        updated_data = {}
        errors = {}

        if 'enable_auto_sync' in request.data:
            enable_auto_sync = request.data['enable_auto_sync']
            try:
                global_preferences['THIRDPARTY__ENABLE_AUTOSYNC'] = enable_auto_sync
                updated_data['enable_auto_sync'] = enable_auto_sync
            except ValidationError:
                errors['enable_auto_sync'] = 'Invalid Input.'


        if 'focus_base_url' in request.data:
            base_url = request.data['focus_base_url']
            if base_url:
                global_preferences['THIRDPARTY__FOCUS_BASEURL'] = base_url
                updated_data['focus_base_url'] = base_url


        if 'focus_username' in request.data:
            username = request.data['focus_username']
            try:
                global_preferences['THIRDPARTY__FOCUS_USERNAME'] = username
                updated_data['focus_username'] = username
            except ValidationError:
                errors['focus_username'] = 'Invalid Username.'

        if 'focus_password' in request.data:
            password = request.data['focus_password']
            try:
                global_preferences['THIRDPARTY__FOCUS_PASSWORD'] = password
                updated_data['focus_password'] = password
            except ValidationError:
                errors['focus_password'] = 'Invalid Password.'

        if 'focus_companycode' in request.data:
            company_code = request.data['focus_companycode']
            try:
                global_preferences['THIRDPARTY__FOCUS_COMPANY_CODE'] = company_code
                updated_data['focus_companycode'] = company_code
            except ValidationError:
                errors['focus_companycode'] = 'Invalid CompanyCode.'


        if 'focus_sync_on' in request.data:
            sync_on = request.data['focus_sync_on']
            try:
                global_preferences['THIRDPARTY__FOCUS_SYNC_ON'] = sync_on
                updated_data['focus_sync_on'] = sync_on
            except ValidationError:
                errors['focus_sync_on'] = 'Invalid Input.'

# -----------------------------------------------------------------------  AMCU ------------------

        if 'amcu_enable_auto_sync' in request.data:
            amcu_enable_auto_sync = request.data['amcu_enable_auto_sync']
            try:
                global_preferences['THIRDPARTY__AMCU_ENABLE_AUTOSYNC'] = amcu_enable_auto_sync
                updated_data['amcu_enable_auto_sync'] = amcu_enable_auto_sync
            except ValidationError:
                errors['amcu_enable_auto_sync'] = 'Invalid Input.'


        if 'amcu_baseurl' in request.data:
            base_url = request.data['amcu_baseurl']
            if base_url:
                global_preferences['THIRDPARTY__AMCU_BASEURL'] = base_url
                updated_data['amcu_baseurl'] = base_url


        if 'amcu_username' in request.data:
            username = request.data['amcu_username']
            try:
                global_preferences['THIRDPARTY__AMCU_USERNAME'] = username
                updated_data['amcu_username'] = username
            except ValidationError:
                errors['amcu_username'] = 'Invalid Username.'

        if 'amcu_password' in request.data:
            password = request.data['amcu_password']
            try:
                global_preferences['THIRDPARTY__AMCU_PASSWORD'] = password
                updated_data['amcu_password'] = password
            except ValidationError:
                errors['amcu_password'] = 'Invalid Password.'

        if 'amcu_api_key' in request.data:
            apikey = request.data['amcu_api_key']
            try:
                global_preferences['THIRDPARTY__AMCU_API_KEY'] = apikey
                updated_data['amcu_api_key'] = apikey
            except ValidationError:
                errors['amcu_api_key'] = 'Invalid ApiKey.'


        if 'amcu_sync_on' in request.data:
            sync_on = request.data['amcu_sync_on']
            try:
                global_preferences['THIRDPARTY__AMCU_SYNC_ON'] = sync_on
                updated_data['amcu_sync_on'] = sync_on
            except ValidationError:
                errors['amcu_sync_on'] = 'Invalid Input.'



        if errors:
            return Response({
                'error': 'Some fields could not be updated.',
                'details': errors,
                'updated_fields': updated_data
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'message': 'Data updated successfully.',
            'updated_fields': updated_data
        }, status=status.HTTP_200_OK)
        
        
class RecentActivityList(generics.ListCreateAPIView):
    serializer_class = RecentActivitySerializer
    model = serializer_class.Meta.model

    def get_queryset(self):
        user=self.request.user
        queryset = RecentActivity.objects.filter(
            user_identifier=user.id,
            user_type = type(user).__name__,
            is_deleted=False
        ).order_by('-created_on')[:5]
        return queryset
    
    # def get_queryset(self):
    #     return RecentActivity.objects.filter(user=self.request.user, is_deleted=False,).order_by('-created_on')[5:]
    
class SettingAPIView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, **kwargs):
        """
        Create or update a setting.
        """
        preferences_code = request.data.get("preferences_code")
        preferences = request.data.get("preferences")

        if not preferences_code or not preferences:
            return Response({"error": "Missing preferences_code or preferences"}, status=status.HTTP_400_BAD_REQUEST)

        # Convert preferences to JSON string
        preferences_json = json.dumps(preferences)

        # Save data
        setting, created = Setting.objects.update_or_create(
            preferences_code=preferences_code,
            defaults={"preferences": preferences_json}
        )
        
        # set_preferences(preferences_code,preferences_json)
        # preferences_res = get_preferences(preferences_code, default=None)
        # created= True if preferences_res else False

        return Response(
            {
                "message": "Preferences saved successfully",
                "created": created,
                "data": {
                    "code": preferences_code,
                    "preferences": preferences,
                }
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )

    def get(self, request, preferences_code=None):
        
        if preferences_code:
            try:
                # setting = Setting.objects.get(preferences_code=preferences_code)
                return Response(
                    {"code": preferences_code, "preferences": get_preferences(preferences_code, default=None)},
                    status=status.HTTP_200_OK
                )
            except Setting.DoesNotExist:
                return Response({"error": "Preferences not found"}, status=status.HTTP_404_NOT_FOUND)

        # Fix for getting all records
        settings = Setting.objects.all()
        data = [{"code": obj.preferences_code, "preferences": json.loads(obj.preferences)} for obj in settings]
        return Response(data, status=status.HTTP_200_OK)
    
class TemplateFilter(FilterSet):
    start_date = DateFilter(field_name='created_on',lookup_expr=('gte'),) 
    end_date = DateFilter(field_name='created_on',lookup_expr=('lte'))

    class Meta:
        model = Template
        fields = ['start_date' ,'end_date','is_active',]

class TemplateMini(generics.ListAPIView):
    serializer_class = TemplateMiniSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_deleted=False ).order_by('-created_on')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter,]
    filterset_class = TemplateFilter
    search_fields = [ 'code',  'name', 'message',]

class TemplateList(generics.ListCreateAPIView):
    serializer_class = TemplateSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_active = True, is_deleted=False ).order_by('-created_on')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter,]
    filterset_class = TemplateFilter
    search_fields = [ 'code',  'name', 'message',]
    
    def perform_create(self, serializer):
        serializer.save()
        
class TemplateDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TemplateSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_active = True, is_deleted = False)

    def perform_update(self, serializer):
        serializer.save()
        
    def perform_destroy(self, instance):
        instance.is_deleted=True
        instance.save()

class TemplateStatusUpdateView(APIView):
    """
    API view to update the is_active status of a Template.
    """
    
    def patch(self, request, template_id):
        # Get the template or return 404
        template = get_object_or_404(Template, id=template_id)
        
        # Validate request data
        if 'is_active' not in request.data:
            return Response(
                {"status": "error", "message": "is_active field is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the new status
        is_active = request.data.get('is_active')
        if not isinstance(is_active, bool):
            return Response(
                {"status": "error", "message": "is_active must be a boolean value"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update the template
        template.is_active = is_active
        template.save()
        
        # Return the updated template
        serializer = TemplateSerializer(template)
        return Response(
            {"status": "success", "message": "Template status updated", "data": serializer.data},
            status=status.HTTP_200_OK
        )


class ListFilter(Filter):
    def filter(self, qs, value):
        if not value:
            return qs

        self.lookup_expr = 'in'
        values = value.split(',')
        return super(ListFilter, self).filter(qs, values)
    

class AlertConfigFilter(FilterSet):
    start_date = DateFilter(field_name='created_on',lookup_expr=('gte'),) 
    end_date = DateFilter(field_name='created_on',lookup_expr=('lte'))

    class Meta:
        model = AlertConfig
        fields = ['start_date' ,'end_date', 'send_to_groups','event_type','sender_type','type','template','is_active','is_scheduled','message_priority','notification_type']



class AlertConfigList(generics.ListAPIView):
    serializer_class = AlertConfigSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_deleted=False ).order_by('-created_on')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter,]
    filterset_class = AlertConfigFilter
    search_fields = [ 'code','value','variable','send_to_users__first_name','send_to_users__last_name','send_to_groups__name'  ]
    ordering_fields = ['code',]

class AlertConfigCreate(generics.CreateAPIView):
    serializer_class = AlertConfigSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_active = True, is_deleted=False ).order_by('-created_on')
    
    def perform_create(self, serializer):
        serializer.save()

    
class AlertConfigDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AlertConfigSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_active = True, is_deleted = False)

    def perform_update(self, serializer):
        serializer.save()
        
    def perform_destroy(self, instance):
        instance.is_deleted=True
        instance.save()



class AnnouncementsList(generics.ListAPIView):
    serializer_class = AnnouncementSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter( is_deleted=False ).order_by('-created_on')
    filter_backends = [filters.SearchFilter,]
    search_fields = [ 'code','body','subject', ]
    ordering_fields = ['code',]

class AnnouncementCreate(generics.CreateAPIView):
    serializer_class = AnnouncementSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_deleted=False ).order_by('-created_on')
    
    def perform_create(self, serializer):
        serializer.save()

    
class AnnouncementDetail(generics.RetrieveAPIView):
    serializer_class = AnnouncementSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_deleted = False)


class TaskSchedulerFilter(FilterSet):
    start_date = DateFilter(field_name='start_time', lookup_expr='gte')
    end_date = DateFilter(field_name='start_time', lookup_expr='lte')
    
    class Meta:
        model = TaskScheduler
        fields = ['name', 'frequency', 'is_active', 'start_time', 'allow_parallel']
        

class TaskSchedulerList(generics.ListAPIView):
    serializer_class = TaskSchedulerSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_active=True).order_by('-start_time')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = TaskSchedulerFilter
    search_fields = ['name', 'description', 'function_path']
    ordering_fields = ['name', 'start_time']


class TaskSchedulerCreate(generics.CreateAPIView):
    serializer_class = TaskSchedulerSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.all()

    def perform_create(self, serializer):
        serializer.save()


class TaskSchedulerDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSchedulerSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_active=True)

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        instance.is_active = False 
        instance.is_deleted = True
        instance.save()



class ActiveThreadsListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        active_threads = TaskThreadManager.get_all_threads()
        return Response(active_threads)

class StartTaskAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        try:
            task = TaskScheduler.objects.get(pk=pk)
            if not task.is_active:
                return Response({"detail": "Task is not active."}, status=status.HTTP_400_BAD_REQUEST)

            started = TaskThreadManager.start_task(task)
            if not started:
                return Response({"detail": "Task already running and parallel execution not allowed."}, status=status.HTTP_400_BAD_REQUEST)

            task.last_run = timezone.now()
            task.next_run = calculate_next_run(task)
            task.save()
            return Response({"detail": "Task started."})
        

        except TaskScheduler.DoesNotExist:
            return Response({"detail": "Task not found."}, status=status.HTTP_404_NOT_FOUND)


class StopTaskAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, task_id):
        stopped_any = False

        # Loop through all active threads and stop those with matching task_id
        for thread_ident, thread in list(active_threads.items()):
            if str(thread.task.id) == str(task_id):
                thread.stop()
                TaskThreadManager.unregister_thread(thread_ident)
                stopped_any = True

        if stopped_any:
            return Response({"detail": "All threads for the task were stopped."})
        return Response({"detail": "No running threads found for the task."}, status=status.HTTP_400_BAD_REQUEST)

class TaskStatusAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        statuses = TaskThreadManager.get_status()
        return Response(statuses)


class KillExpiredThreadsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        killed = TaskThreadManager.kill_expired_threads()
        return Response({"detail": f"{killed} expired threads stopped."})


# Import filter views for URL routing
from Core.System.filter_views import (
    SavedFilterListCreate,
    SavedFilterDetail,
    apply_saved_filter,
    FilterPresetList,
    FilterPresetDetail
)