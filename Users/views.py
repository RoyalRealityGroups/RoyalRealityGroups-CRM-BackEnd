from django.apps import apps
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from Core.Core.utils.utils import get_model_path
from Core.Users.serializers import CoreUserMiniSerializer
User = get_user_model()


from rest_framework import filters

from .serializers import RegisterSerializer, UserSerializer
# from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken 
from rest_framework.views import APIView
from rest_framework import generics, status, permissions
from django.conf import settings
from Core.Users.models import JwtToken, Device

from rest_framework.exceptions import ValidationError
from utils import (
    apply_company_location_filter_for_users,
    apply_channel_partner_company_location_filter
)




def get_user_group(user, group_name):
    return  user.groups.filter(name=group_name).exists()


TRANSACTION_APP_LABELS = {'Sales', 'Dispatch', 'Invoice', 'Receipts', 'Delivery'}
SKIP_DEPENDENCY_APPS = {'admin', 'auth', 'contenttypes', 'sessions'}


def _has_field(model, field_name):
    return any(f.name == field_name for f in model._meta.fields)


def _active_queryset(model):
    qs = model.objects.all()
    if _has_field(model, 'is_deleted'):
        qs = qs.filter(Q(is_deleted=False) | Q(is_deleted__isnull=True))
    return qs


def _format_model_name(model):
    return f"{model._meta.app_label}.{model._meta.object_name}"


def _collect_user_delete_references(user):
    user_id_str = str(user.id)
    user_model = user.__class__

    transaction_refs = set()
    tagged_refs = set()

    for model in apps.get_models():
        if model == user_model or model._meta.app_label in SKIP_DEPENDENCY_APPS:
            continue

        try:
            qs = _active_queryset(model)
        except Exception:
            continue

        has_reference = False

        identifier_fields = [
            'created_by_identifier',
            'modified_by_identifier',
            'user_identifier',
            'authorized_by_identifier',
            'current_authorized_by_identifier',
        ]
        identifier_q = Q()
        has_identifier_field = False
        for field_name in identifier_fields:
            if _has_field(model, field_name):
                identifier_q |= Q(**{field_name: user_id_str})
                has_identifier_field = True
        if has_identifier_field and qs.filter(identifier_q).exists():
            has_reference = True

        if not has_reference:
            for field in model._meta.get_fields():
                if not getattr(field, 'is_relation', False) or getattr(field, 'auto_created', False):
                    continue

                related_model = getattr(field, 'related_model', None)
                if related_model != user_model:
                    continue

                try:
                    if getattr(field, 'many_to_many', False):
                        if qs.filter(**{f"{field.name}__id": user.id}).exists():
                            has_reference = True
                            break
                    else:
                        if qs.filter(**{field.name: user}).exists():
                            has_reference = True
                            break
                except Exception:
                    continue

        if has_reference:
            model_name = _format_model_name(model)
            if model._meta.app_label in TRANSACTION_APP_LABELS:
                transaction_refs.add(model_name)
            else:
                tagged_refs.add(model_name)

    return sorted(transaction_refs), sorted(tagged_refs)

class RegisterView(generics.CreateAPIView):
          
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer



class UserFilter(FilterSet):
    # date_range = DateRangeFilter(field_name='created_at')
    # start_date = DateFilter(field_name='created_at',lookup_expr=('gte'),)
    # end_date = DateFilter(field_name='created_at',lookup_expr=('lte'))

    class Meta:
        model = User
        fields = ['phone','created_at']
        

class UserList(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    # queryset = User.objects.filter( is_superuser = False)
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter,]
    search_fields = ['username', 'email', 'phone', 'first_name', 'last_name',]
    
    def get_queryset(self):
        user = self.request.user
        queryset = User.objects.filter(is_superuser=False)

        if not user.is_superuser:
            queryset = apply_company_location_filter_for_users(queryset, user)

        queryset = queryset.order_by('-created_at')
        return queryset

class UserCreate(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter,]
    search_fields = ['username', 'email', 'phone', 'first_name', 'last_name', 'pincode', 'groups__name']
    
    def get_queryset(self):
        user = self.request.user
        queryset = User.objects.filter(is_active=True)

        # Handle location field safely - may not exist on all user models
        try:
            user_locations = user.location.all() if hasattr(user, 'location') else []
            if not user.is_superuser and user_locations:
                queryset = queryset.filter(Q(id=user.id) | Q(location__in=user_locations))
        except Exception:
            pass

        return queryset
    
    


class UserDetails(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_queryset(self):
        user = self.request.user
        # Allow superusers to view their own profile
        if user.is_superuser and self.kwargs.get('pk') == str(user.id):
            return User.objects.filter(id=user.id)
        queryset = User.objects.filter(is_superuser=False)
        return apply_company_location_filter_for_users(queryset, user)

    def perform_update(self, serializer):
        serializer.save(modified_by=self.request.user,)

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()

        if request.user.id == user.id:
            return Response(
                {"message": "You cannot delete your own user account."},
                status=status.HTTP_400_BAD_REQUEST
            )

        transaction_refs, tagged_refs = _collect_user_delete_references(user)

        if transaction_refs or tagged_refs:
            if user.is_active:
                user.is_active = False
                user.save(update_fields=['is_active', 'updated_at'])

            JwtToken.objects.filter(user_type='User', user_identifier=user.id).delete()
            Device.objects.filter(user_type='User', user_identifier=user.id).update(
                accesstoken='',
                fcmtoken='',
                apntoken='',
                socket='',
            )

            message_parts = []
            if transaction_refs:
                message_parts.append("existing transactions")
            if tagged_refs:
                message_parts.append("other references")
            reason = " and ".join(message_parts)

            return Response(
                {
                    "message": (
                        f'User "{user.username}" cannot be deleted because it is linked with {reason}. '
                        "The user has been marked as inactive."
                    ),
                    "status": "inactive",
                    "transaction_references": transaction_refs[:10],
                    "tagged_references": tagged_refs[:10],
                },
                status=status.HTTP_200_OK
            )

        username = user.username
        user.delete()
        return Response(
            {"message": f'User "{username}" deleted successfully.'},
            status=status.HTTP_200_OK
        )



class UserPermissionList(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        l = request.user.get_all_permissions()
        l_as_list = list(l)  
        return Response(l_as_list, status=status.HTTP_200_OK)


class UserMini(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CoreUserMiniSerializer
    model = serializer_class.Meta.model
    filter_backends = [DjangoFilterBackend, filters.SearchFilter,]
    search_fields = ['username', 'email', 'phone', 'first_name', 'last_name']
    

    def get_queryset(self):
        user_type = self.kwargs.get('user_type')

        if not user_type:
            return Response({"error": "User type is required"},status=status.HTTP_400_BAD_REQUEST)

        user_model_map = {entry['type'].lower(): entry['model'] for entry in settings.USER_MODELS}

        model_path = user_model_map.get(user_type.lower())
        if not model_path:
            raise ValidationError({"error": f"Invalid user_type: {user_type}"})

        model = apps.get_model(model_path)

        queryset = model.objects.filter(is_active=True, is_superuser=False).order_by('first_name', 'last_name')
        queryset = apply_company_location_filter_for_users(queryset, self.request.user)

        return queryset.distinct()

class UserMiniByUserType(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CoreUserMiniSerializer
    model = serializer_class.Meta.model
    filter_backends = [DjangoFilterBackend, filters.SearchFilter,]
    search_fields = ['username', 'email', 'phone', 'first_name', 'last_name']

    def get_queryset(self):
        user_type = self.kwargs.get('user_type')

        if not user_type:
            return Response({"error": "User type is required"},status=status.HTTP_400_BAD_REQUEST)

        model_path = get_model_path(user_type)

        if not model_path:
            raise ValidationError({"error": f"Invalid user_type: {user_type}"})

        model = apps.get_model(model_path)

        queryset = model.objects.filter(is_active=True, is_superuser=False).order_by('first_name', 'last_name')
        queryset = apply_company_location_filter_for_users(queryset, self.request.user)

        return queryset.distinct()


# Channel Partner Endpoints
class SuperstockistListView(generics.ListAPIView):
    """List all active superstockists for dropdown"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        from Masters.models import Superstockist
        
        search = request.GET.get('search', '')
        user_id = request.GET.get('user_id')  # ID of user being edited
        
        queryset = Superstockist.filtered_objects.get_qs(
            user=request.user,
            is_active=True
        )
        queryset = apply_channel_partner_company_location_filter(
            queryset,
            request.user,
            company_field='company',
            state_field='state',
            city_field='city',
            coverage_relation='locations'
        )
        
        # If editing a specific user, ensure their assigned superstockist is included
        if user_id:
            try:
                editing_user = User.objects.get(id=user_id)
                if editing_user.superstockist:
                    # Include the assigned superstockist even if not in filtered results
                    queryset = queryset | Superstockist.objects.filter(id=editing_user.superstockist.id)
            except User.DoesNotExist:
                pass
        
        # Apply search filter if provided
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(code__icontains=search)
            )
        
        superstockists = queryset.distinct().values('id', 'code', 'name').order_by('name')
        
        return Response(list(superstockists), status=status.HTTP_200_OK)


class DistributorListView(generics.ListAPIView):
    """List all active distributors for dropdown"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        from Masters.models import Distributor
        
        search = request.GET.get('search', '')
        user_id = request.GET.get('user_id')  # ID of user being edited
        
        queryset = Distributor.filtered_objects.get_qs(
            user=request.user,
            is_active=True
        )
        queryset = apply_channel_partner_company_location_filter(
            queryset,
            request.user,
            company_field='company',
            state_field='state',
            city_field='city',
            coverage_relation='locations'
        )
        
        # If editing a specific user, ensure their assigned distributor is included
        if user_id:
            try:
                editing_user = User.objects.get(id=user_id)
                if editing_user.distributor:
                    # Include the assigned distributor even if not in filtered results
                    queryset = queryset | Distributor.objects.filter(id=editing_user.distributor.id)
            except User.DoesNotExist:
                pass
        
        # Apply search filter if provided
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(code__icontains=search)
            )
        
        distributors = queryset.distinct().values('id', 'code', 'name').order_by('name')
        
        return Response(list(distributors), status=status.HTTP_200_OK)


class RetailerListView(generics.ListAPIView):
    """List all active retailers for dropdown"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        from Masters.models import Retailer
        
        search = request.GET.get('search', '')
        user_id = request.GET.get('user_id')  # ID of user being edited
        
        queryset = Retailer.filtered_objects.get_qs(
            user=request.user,
            is_active=True
        )
        queryset = apply_channel_partner_company_location_filter(
            queryset,
            request.user,
            company_field='company',
            state_field='state',
            city_field='city',
            coverage_relation='locations'
        )
        
        # If editing a specific user, ensure their assigned retailer is included
        if user_id:
            try:
                editing_user = User.objects.get(id=user_id)
                if editing_user.retailer:
                    # Include the assigned retailer even if not in filtered results
                    assigned_retailer = Retailer.objects.filter(id=editing_user.retailer.id, is_deleted=False)
                    queryset = queryset.union(assigned_retailer)
            except User.DoesNotExist:
                pass
        
        # Apply search filter if provided
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(code__icontains=search)
            )
        
        retailers = queryset.distinct().values('id', 'code', 'name').order_by('name')
        
        return Response(list(retailers), status=status.HTTP_200_OK)


class CompanyDropdownView(generics.ListAPIView):
    """List all active companies for dropdown"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        from Masters.models import Company
        
        search = request.GET.get('search', '')
        
        queryset = Company.objects.filter(is_deleted=False)

        user = request.user
        if not user.is_superuser:
            if getattr(user, 'has_all_companies', False):
                pass
            else:
                user_company_ids = user.companies.values_list('id', flat=True)
                queryset = queryset.filter(id__in=user_company_ids)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(code__icontains=search)
            )
        
        companies = queryset.values('id', 'code', 'name').order_by('name')
        
        return Response(list(companies), status=status.HTTP_200_OK)


class LocationDropdownView(generics.ListAPIView):
    """List all active locations for dropdown (filtered by company)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        from Masters.models import Location
        
        search = request.GET.get('search', '')
        company_ids = request.GET.getlist('company_ids[]')  # Array of company IDs
        if not company_ids:
            raw_company_ids = request.GET.get('company_ids') or request.GET.get('company_id') or request.GET.get('company') or ''
            if raw_company_ids:
                company_ids = [cid.strip() for cid in raw_company_ids.split(',') if cid.strip()]
        
        queryset = Location.objects.filter(is_deleted=False)

        user = request.user
        if not user.is_superuser:
            if getattr(user, 'has_all_locations', False):
                pass
            else:
                user_location_ids = user.locations.values_list('id', flat=True)
                queryset = queryset.filter(id__in=user_location_ids)
        
        # Filter by companies if provided
        if company_ids:
            queryset = queryset.filter(companies__id__in=company_ids).distinct()
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(code__icontains=search)
            )
        
        locations = queryset.values('id', 'code', 'name').order_by('name')
        
        return Response(list(locations), status=status.HTTP_200_OK)


class ReportingManagerDropdownView(generics.ListAPIView):
    """List all active users for reporting manager dropdown"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CoreUserMiniSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['username', 'email', 'phone', 'first_name', 'last_name']

    def get_queryset(self):
        return User.objects.filter(is_active=True).order_by('first_name', 'last_name')


# =============================================================================
# RRGMS Permission API Views
# =============================================================================

class ScreenListView(generics.ListAPIView):
    """List all screens"""
    from Users.models import Screen
    from Users.serializers import ScreenSerializer
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ScreenSerializer
    queryset = Screen.objects.filter(is_active=True).order_by('order', 'name')


class UserPermissionView(APIView):
    """Get/Update permissions for a specific user"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, user_id):
        from Users.models import UserPermission
        from Users.serializers import UserPermissionSerializer
        
        # Check if user has permission to manage users
        user_perm = UserPermission.objects.filter(
            user=request.user, screen__code='USER_PERMISSION', can_view=True, can_edit=True
        ).first()
        
        if not request.user.is_superuser and not user_perm:
            return Response({'error': 'Permission denied'}, status=403)
        
        permissions = UserPermission.objects.filter(user_id=user_id)
        serializer = UserPermissionSerializer(permissions, many=True)
        return Response(serializer.data)
    
    def post(self, request, user_id):
        from Users.models import UserPermission, PermissionAuditLog
        
        # Check permission
        user_perm = UserPermission.objects.filter(
            user=request.user, screen__code='USER_PERMISSION', can_view=True, can_edit=True
        ).first()
        
        if not request.user.is_superuser and not user_perm:
            return Response({'error': 'Permission denied'}, status=403)
        
        target_user = User.objects.get(id=user_id)
        permissions_data = request.data.get('permissions', [])
        
        updated = 0
        for perm_data in permissions_data:
            screen_id = perm_data.get('screen')
            if not screen_id:
                continue
            
            perm, created = UserPermission.objects.update_or_create(
                user=target_user,
                screen_id=screen_id,
                defaults={
                    'can_view': perm_data.get('can_view', False),
                    'can_add': perm_data.get('can_add', False),
                    'can_edit': perm_data.get('can_edit', False),
                    'can_delete': perm_data.get('can_delete', False),
                    'can_export': perm_data.get('can_export', False),
                    'is_view_only': perm_data.get('is_view_only', False),
                }
            )
            updated += 1
            
            PermissionAuditLog.objects.create(
                changed_by=request.user,
                target_user=target_user,
                action='UPDATE' if not created else 'CREATE',
                field_changed='permissions',
                old_value='',
                new_value=str(perm_data),
                ip_address=request.META.get('REMOTE_ADDR')
            )
        
        return Response({'message': f'Updated {updated} permissions'})


class MyPermissionsView(APIView):
    """Get current user's permissions"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        from Users.models import UserPermission
        from Users.serializers import UserPermissionSerializer
        
        permissions = UserPermission.objects.filter(user=request.user)
        serializer = UserPermissionSerializer(permissions, many=True)
        return Response(serializer.data)


class PermissionAuditLogView(generics.ListAPIView):
    """List permission audit logs for a user"""
    from Users.models import PermissionAuditLog
    from Users.serializers import PermissionAuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PermissionAuditLogSerializer
    
    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        return PermissionAuditLog.objects.filter(target_user_id=user_id)


# =============================================================================
# MODULE 10 - EMPLOYEE MANAGEMENT
# =============================================================================

class EmployeeListView(generics.ListCreateAPIView):
    """
    Module 10: Employee Management — list all employees with performance stats.
    GET  /api/usermanagement/employees/
    POST /api/usermanagement/employees/   (create)
    """
    from Users.serializers import UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'username', 'email', 'designation']
    ordering_fields = ['first_name', 'last_name', 'joining_date', 'leads_assigned']
    ordering = ['first_name', 'last_name']

    def get_queryset(self):
        qs = User.objects.filter(is_active=True, is_superuser=False).select_related('reporting_manager')
        reporting_manager = self.request.query_params.get('reporting_manager')
        user_status = self.request.query_params.get('user_status')
        designation = self.request.query_params.get('designation')
        if reporting_manager:
            qs = qs.filter(reporting_manager_id=reporting_manager)
        if user_status:
            qs = qs.filter(user_status=user_status)
        if designation:
            qs = qs.filter(designation__icontains=designation)
        return qs


class EmployeeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Module 10: Single employee CRUD.
    GET/PATCH/DELETE /api/usermanagement/employees/<pk>/
    """
    from Users.serializers import UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer
    queryset = User.objects.filter(is_active=True, is_superuser=False)


class EmployeePerformanceView(APIView):
    """
    Module 10: Live performance stats for one employee.
    GET /api/usermanagement/employees/<pk>/performance/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        from django.utils import timezone
        from django.db.models import Count

        try:
            employee = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)

        today = timezone.now().date()

        # Live counts from related models
        try:
            from Lead.models import Lead
            from SiteVisit.models import SiteVisit
            leads_total = Lead.objects.filter(assigned_employee=employee, is_deleted=False).count()
            leads_this_month = Lead.objects.filter(
                assigned_employee=employee, is_deleted=False,
                created_on__year=today.year, created_on__month=today.month
            ).count()
            site_visits_total = SiteVisit.objects.filter(
                assigned_employee=employee, is_deleted=False
            ).count()
            site_visits_completed = SiteVisit.objects.filter(
                assigned_employee=employee, is_deleted=False, status='COMPLETED'
            ).count()
        except Exception:
            leads_total = leads_this_month = site_visits_total = site_visits_completed = 0

        try:
            from Booking.models import Booking
            bookings_total = Booking.objects.filter(
                sales_executive=employee, is_deleted=False
            ).exclude(status='CANCELLED').count()
            registrations = Booking.objects.filter(
                sales_executive=employee, is_deleted=False, status='REGISTERED'
            ).count()
        except Exception:
            bookings_total = registrations = 0

        return Response({
            'employee_id': str(employee.id),
            'employee_name': f"{employee.first_name} {employee.last_name}".strip() or employee.username,
            'designation': getattr(employee, 'designation', None),
            'joining_date': getattr(employee, 'joining_date', None),
            'user_status': getattr(employee, 'user_status', None),
            'performance': {
                'leads_total': leads_total,
                'leads_this_month': leads_this_month,
                'site_visits_total': site_visits_total,
                'site_visits_completed': site_visits_completed,
                'bookings_total': bookings_total,
                'registrations': registrations,
            }
        })
