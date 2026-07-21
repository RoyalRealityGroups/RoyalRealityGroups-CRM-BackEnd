from datetime import timedelta
import json
import os
from django.apps import apps
from django.db import models
from django.db.models import Q, Max, OuterRef, Subquery,CharField
from django.db.models.functions import Cast
from django.utils.timezone import now
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework import generics, status, permissions, filters, views
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError

from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from django_filters import DateRangeFilter, DateFilter
import django_filters
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

from Core.Core.authentication.CustomJWT import update_access_token
from Core.Core.permissions.permissions import GetPermission
from Core.System.models import RecentActivity
from Core.Users.models import (
    Assignee, AssigneeByPass, AssigneeDefnition, Authorization, AuthorizationDefinition,
    AuthorizationHistory, ContentTypeDetail, DataPermissions, Device, DeviceLog,
    DjangoApp, JwtToken, UserPreferences, UserType
)
from rest_framework import pagination

from Core.Users.serializers import (
    AllContentTypeSerializer, AllContentTypesSerializer, AssigneeByPassSerializer, AssigneeDefnitionSerializer, AssigneeSerializer,
    AuthorizationDefinitionSerializer, AuthorizationHistorySerializer, AuthorizationSerializer, AuthorizedHistorySerializer,
    ChangePasswordSerializer, CheckAuthorizationHistorySerializer, CheckBulkAuthorizationHistorySerializer, ContentTypeSerializer, DataPermissionsGroupUpdateSerializer,
    DataPermissionsSerializer, DataPermissionsUpdateSerializer, DeviceLogSerializer, DeviceSerializer, DjangoAppSerializer,
    DynamicIDNameSerializer, EmailVerificationSerializer, ForgotPasswordSerializer, GroupMini2Serializer, GroupSerializer, IamUserSerializer, InstanceAuthorizationHistorySerializer,
    LoginSerializer, LogoutSerializer, OTPRequestSerializer, OTPResendSerializer, PermissionJoinSerializer,
    TokenRefreshSerializer, UpdatePasswordSerializer, UserEmailValidateSerializer, UserGroupSerializer,
    UserPhoneValidateSerializer, UserUserNameValidateSerializer, ValidateCurrentPasswordSerializer, ValidateUsernameSerializer
)
from django.db import transaction
User = get_user_model()

# -------------------- Utility Functions -------------------- #

def get_user_group(user, group_name):
    return user.groups.filter(name=group_name).exists()

def model_has_field(model_class, f):
    try:
        model_class._meta.get_field(f)
        return True
    except:
        return False


def _active_soft_delete_q(prefix=''):
    return Q(**{f'{prefix}is_deleted': False}) | Q(**{f'{prefix}is_deleted__isnull': True})


def _active_definition_q(prefix='authorization_definition__'):
    today = now().date()
    return (
        Q(**{f'{prefix}status': True})
        & _active_soft_delete_q(prefix)
        & (
            Q(**{f'{prefix}effective_from__lte': today})
            | Q(**{f'{prefix}effective_from__isnull': True})
        )
    )


def _get_user_authorization_for_screen(user, content_type):
    user_type = user.__class__.__name__
    user_identifier = str(user.id)
    user_group_ids = list(user.groups.values_list("id", flat=True))

    base_queryset = (
        Authorization.objects.filter(screen=content_type)
        .filter(_active_soft_delete_q())
        .filter(Q(authorization_definition__isnull=True) | _active_definition_q())
    )

    if user.is_superuser:
        return base_queryset.only('id', 'level', 'authorization_definition_id').order_by('-level', '-created_on').first()

    authorization_obj = base_queryset.filter(
        user_type=user_type,
        user_identifier=user_identifier
    ).only('id', 'level', 'authorization_definition_id').order_by('-level', '-created_on').first()

    if authorization_obj:
        return authorization_obj

    if user_group_ids:
        return base_queryset.filter(
            group_id__in=user_group_ids
        ).only('id', 'level', 'authorization_definition_id').order_by('-level', '-created_on').first()

    return None

# -------------------- User Model Views -------------------- #

@method_decorator(csrf_exempt, name='dispatch')
class LoginAPIView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class LogoutAPIView(generics.GenericAPIView):
    serializer_class = LogoutSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

class OTPRequestAPIView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = OTPRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class OTPResendAPIView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = OTPResendSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class TokenRefreshView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = TokenRefreshSerializer

    def post(self, request, *args, **kwargs):
        serializer = TokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        return Response(data, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class RefreshTokenView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        refresh = request.data.get('refresh')
        if not refresh:
            return Response({'detail': 'Refresh token is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            response_data = update_access_token(refresh)
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class VerifyEmail(views.APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = EmailVerificationSerializer

    def get(self, request):
        serializer = self.serializer_class(data={'token': request.GET.get('token')})
        serializer.is_valid(raise_exception=True)
        return Response({'email': 'Successfully activated'}, status=status.HTTP_200_OK)

class ChangePasswordView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def get_queryset(self):
        user = self.request.user
        return User.objects.filter(id=user.id)

    def get_object(self):
        user = self.request.user
        return User.objects.get(id=user.id)

@method_decorator(csrf_exempt, name='dispatch')
class ValidateCurrentPasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        current_password = request.data.get('current_password')
        
        if not current_password:
            return Response(
                {"current_password": ["This field is required."]}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Directly check password
        user = request.user
        is_valid = user.check_password(current_password)
        
        if not is_valid:
            return Response(
                {"current_password": ["Current password is incorrect"]}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({"message": "Password is valid", "valid": True}, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class ValidateUsernameView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ValidateUsernameSerializer(data=request.data)
        if serializer.is_valid():
            return Response({"message": "Username is valid", "valid": True}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UpdatePasswordView(generics.UpdateAPIView):
    serializer_class = UpdatePasswordSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_active=True).order_by('-id')
    lookup_field = 'id'


@method_decorator(csrf_exempt, name='dispatch')
class ForgotPasswordAPIView(generics.GenericAPIView):
    """
    Step 1: Send OTP to user's email for password reset.
    Since SMTP is not configured, OTP is printed to the console.
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        import random
        import logging
        from django.core.cache import cache

        logger = logging.getLogger('Common')

        username_or_email = request.data.get('username', '').strip()
        if not username_or_email:
            return Response(
                {"error": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Find user by email
        user = User.objects.filter(
            email__iexact=username_or_email,
            is_active=True
        ).first()

        if not user:
            return Response(
                {"error": "No active user found with this email"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Generate 5-digit OTP
        otp = str(random.randint(10000, 99999))

        # Store OTP in cache for 5 minutes (keyed by user id)
        cache_key = f"password_reset_otp_{user.id}"
        cache.set(cache_key, otp, timeout=300)

        # Print OTP to console (SMTP not configured)
        print("\n" + "=" * 50)
        print("  PASSWORD RESET OTP")
        print("=" * 50)
        print(f"  User:  {user.username} ({user.email})")
        print(f"  OTP:   {otp}")
        print(f"  Valid:  5 minutes")
        print("=" * 50 + "\n")

        logger.info(f"Password reset OTP for {user.username}: {otp}")

        # Try sending via email (falls back to console if SMTP not configured)
        from Core.System.email_service import send_email
        if user.email:
            send_email(
                to=[user.email],
                subject='Password Reset OTP',
                body=f'Your password reset OTP is: {otp}\n\nThis OTP is valid for 5 minutes.\n\nIf you did not request this, please ignore this email.',
            )

        return Response({
            "message": "OTP has been sent to your registered email.",
            "user_id": str(user.id),
        }, status=status.HTTP_200_OK)


class ResetPasswordConfirmView(APIView):
    """
    Step 2: Verify OTP and reset password.
    POST: { user_id, otp, password }
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        from django.core.cache import cache

        user_id = request.data.get('user_id', '').strip()
        otp = request.data.get('otp', '').strip()
        new_password = request.data.get('password', '').strip()

        if not user_id or not otp or not new_password:
            return Response(
                {"error": "user_id, otp, and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate password strength
        from Core.Core.utils.password_validator import validate_password_strength
        password_errors = validate_password_strength(new_password)
        if password_errors:
            return Response(
                {"error": password_errors[0], "errors": password_errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify OTP from cache
        cache_key = f"password_reset_otp_{user_id}"
        stored_otp = cache.get(cache_key)

        if not stored_otp:
            return Response(
                {"error": "OTP has expired. Please request a new one."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if stored_otp != otp:
            return Response(
                {"error": "Invalid OTP. Please try again."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # OTP is valid — reset password
        try:
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        user.set_password(new_password)
        user.must_reset_password = False
        user.save(update_fields=['password', 'must_reset_password'])

        # Clear OTP from cache
        cache.delete(cache_key)

        return Response(
            {"message": "Password reset successfully. You can now login."},
            status=status.HTTP_200_OK
        )


class UserActive(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        id = kwargs['id']
        try:
            user = User.objects.get(id=id)
            if request.user.id == user.id:
                return Response({"Message": "You Cant Perform This Action"}, status=status.HTTP_200_OK)
            if User.objects.filter(username=user.username, is_active=True).count() > 0:
                return Response({"username": 'UserName Already exists in Active Users'}, status=status.HTTP_400_BAD_REQUEST)
            if User.objects.filter(phone=user.phone, is_active=True).count() > 0:
                return Response({"phone": 'Phone Number Already exists in Active Users'}, status=status.HTTP_400_BAD_REQUEST)
            if User.objects.filter(email=user.email, is_active=True).count() > 0:
                return Response({"phone": 'Email Already exists in Active Users'}, status=status.HTTP_400_BAD_REQUEST)
            user.is_active = True
            user.save()
            return Response({"Message": "User Activated"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"user": 'user does not exists'}, status=status.HTTP_400_BAD_REQUEST)

class UserInActive(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        id = kwargs['id']
        try:
            user = User.objects.get(id=id)
            if request.user.id == user.id:
                return Response({"Message": "You Cant Perform This Action"}, status=status.HTTP_200_OK)
            JwtToken.objects.filter(user_type='User', user_identifier=user.id).delete()
            user.is_active = False
            user.save()
            Device.objects.filter(user_type='User', user_identifier=user.id).update(
                accesstoken='', fcmtoken='', apntoken='', socket='',
            )
            return Response({"Message": "User Inactivated"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"user": 'user does not exists'}, status=status.HTTP_400_BAD_REQUEST)

class IamUserDetails(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = IamUserSerializer
    queryset = User.objects.all()

    def get_object(self):
        obj = User.objects.get(pk=self.request.user.pk)
        self.check_object_permissions(self.request, obj)
        return obj

class UserNameValidate(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserUserNameValidateSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter().order_by('-id')

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({}, status=status.HTTP_200_OK)

class UserEmailValidate(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserEmailValidateSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter().order_by('-id')

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({}, status=status.HTTP_200_OK)

class UserPhoneValidate(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserPhoneValidateSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter().order_by('-id')

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({}, status=status.HTTP_200_OK)

class LoggedInUsersAPIView(APIView):
    permission_classes = [GetPermission('System.can_view_current_logged_users')]

    def get(self, request):
        time_threshold = now() - timedelta(minutes=15)

        # Subquery for recent access time
        recent_activity_qs = RecentActivity.objects.filter(
            user_identifier=Cast(OuterRef('id'), CharField()),
            created_on__gte=time_threshold
        ).order_by('-created_on')

        # Annotated list of active users with recent activity
        users = User.objects.filter(
            is_active=True,
            id__in=[
                uuid for uuid in RecentActivity.objects.filter(
                    created_on__gte=time_threshold
                ).values_list('user_identifier', flat=True)
            ]
        ).annotate(
            recent_access_time=Subquery(recent_activity_qs.values('created_on')[:1])
        ).distinct()

        user_data = [
            {
                'id': user.id,
                'full_name': f"{user.first_name} {user.last_name}".strip(),
                'username': user.username,
                'first_name': user.first_name,
                'email': user.email,
                'phone': user.phone,
                'recent_access_time': user.recent_access_time,
                'groups': [group.name for group in user.groups.all()],
            }
            for user in users
        ]

        return Response({
            'count': users.count(),
            'results': user_data
        })        
        
class EmployeesCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = self.request.user
        queryset = User.objects.filter(is_active=True, is_superuser=False)
        if user.is_superuser or user.has_perm('System.all_data'):
            queryset = queryset.count()
        else:
            queryset = queryset.filter(reporting_to=self.request.user).count()
        return Response({'employees': queryset}, status=status.HTTP_200_OK)

# -------------------- Device & DeviceLog Model Views -------------------- #

class DeviceFilter(FilterSet):
    class Meta:
        model = Device
        fields = ['type',]

class UserDevicesByMe(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DeviceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DeviceFilter
    search_fields = ['name']
    ordering_fields = ['id']

    def get_queryset(self):
        user = self.request.user
        user_type = None
        for model in settings.USER_MODELS:
            model_class = model.get('model')
            if isinstance(model_class, str):
                try:
                    app_label, model_name = model_class.split('.')
                    model_class = apps.get_model(app_label, model_name)
                except (ValueError, LookupError):
                    continue
            if isinstance(user, model_class):
                user_type = model.get('type')
                break
        if user_type == 'User':
            queryset = Device.objects.filter(user_identifier=user.id, user_type='User')
        elif user_type == 'Customer':
            queryset = Device.objects.filter(user_identifier=user.id, user_type='Customer')
        elif user_type == 'DeliveryPerson':
            queryset = Device.objects.filter(user_identifier=user.id, user_type='DeliveryPerson')
        else:
            queryset = Device.objects.none()
        return queryset.order_by('-id')

class UserDevices(generics.RetrieveAPIView):
    serializer_class = DeviceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DeviceFilter
    search_fields = ['name', 'user_identifier', 'user_type']
    ordering_fields = ['id']

class UserDevicesByUser(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DeviceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DeviceFilter
    search_fields = ['name', 'user_identifier', 'user_type']
    ordering_fields = ['id']

    def get_queryset(self, **kwargs):
        return Device.objects.filter(user_identifier=self.kwargs['user_identifier'], user_type=self.kwargs['user_type'], is_deleted=False)

class DeviceLogFilter(FilterSet):
    start_date = DateFilter(field_name='created_on', lookup_expr='gte')
    end_date = DateFilter(field_name='created_on', lookup_expr='lte')
    date_range = DateRangeFilter(field_name='created_on')

    class Meta:
        model = DeviceLog
        fields = ['device', 'login', 'logout', 'start_date', 'end_date']

class DeviceLogs(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DeviceLogSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DeviceLogFilter
    search_fields = ['user_identifier', 'user_type']
    ordering_fields = ['id', 'login', 'device', 'logout']

class DeviceLogByMe(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DeviceLogSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DeviceLogFilter
    search_fields = ['user_identifier', 'user_type']
    ordering_fields = ['id', 'login', 'device', 'logout']

    def get_queryset(self):
        user = self.request.user
        user_type = None
        for model in settings.USER_MODELS:
            model_class = model.get('model')
            if isinstance(model_class, str):
                try:
                    app_label, model_name = model_class.split('.')
                    model_class = apps.get_model(app_label, model_name)
                except (ValueError, LookupError):
                    continue
            if isinstance(user, model_class):
                user_type = model.get('type')
                break
        if user_type == 'User':
            queryset = DeviceLog.objects.filter(user_identifier=user.id, user_type='User')
        elif user_type == 'Customer':
            queryset = DeviceLog.objects.filter(user_identifier=user.id, user_type='Customer')
        elif user_type == 'DeliveryPerson':
            queryset = DeviceLog.objects.filter(user_identifier=user.id, user_type='DeliveryPerson')
        else:
            queryset = DeviceLog.objects.none()
        return queryset.order_by('-id')

class DeviceLogByUser(generics.ListAPIView):
    serializer_class = DeviceLogSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DeviceLogFilter
    search_fields = ['user_identifier', 'user_type']
    ordering_fields = ['id', 'login', 'device', 'logout']

    def get_queryset(self, **kwargs):
        return DeviceLog.objects.filter(user_identifier=self.kwargs['user_identifier'], user_type=self.kwargs['user_type'], is_deleted=False).order_by('-id')

# -------------------- DataPermissions Model Views -------------------- #

class DataPermissionsFilter(FilterSet):
    class Meta:
        model = DataPermissions
        fields = ['group', 'entry', 'view', 'report', 'exclusions', 'type']

class DataPermissionsCreate(generics.CreateAPIView):
    queryset = DataPermissions.objects.filter(is_deleted=False)
    serializer_class = DataPermissionsSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DataPermissionsFilter
    ordering_fields = ['code', 'created_on']
    search_fields = ['code', 'user_type', 'user_identifier', 'model_path']

class DataPermissionsUpdate(generics.UpdateAPIView):
    queryset = DataPermissions.objects.filter(is_deleted=False)
    serializer_class = DataPermissionsSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DataPermissionsFilter
    ordering_fields = ['code', 'created_on']
    search_fields = ['code', 'user_type', 'user_identifier', 'model_path']

class DataPermissionsList(generics.ListAPIView):
    serializer_class = DataPermissionsSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_deleted=False)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = DataPermissionsFilter
    search_fields = ['code', 'user_type', 'user_identifier', 'model_path']
    ordering_fields = ['code']

    def get_queryset(self):
        model_path = self.kwargs.get('model_path')
        data_permissions = DataPermissions.objects.filter(model_path=model_path, is_deleted=False).order_by('-id')
        return data_permissions

class DataPermissionsUpdateView(generics.UpdateAPIView):
    serializer_class = DataPermissionsUpdateSerializer

    def get_queryset(self):
        return DataPermissions.objects.all()

    def update(self, request, *args, **kwargs):
        user_type = self.request.query_params.get("user_type")
        user_identifier = self.request.query_params.get("user_identifier")
        model_path = request.data.get('model_path')
        exclusions = request.data.get('exclusions')
        if user_type is None or user_identifier is None or model_path is None or exclusions is None:
            return Response({"error": "user_type, user_identifier, model_path, and exclusions are required."}, status=status.HTTP_400_BAD_REQUEST)
        result = DataPermissions.objects.filter(user_type=user_type, user_identifier=user_identifier, model_path=model_path).order_by('-id')
        total_records = result.count()
        result.update(exclusions=exclusions)
        return Response({
            "message": f"Updated exclusions for {total_records} records.",
            "total_records_updated": total_records
        }, status=status.HTTP_200_OK)

class DataPermissionsGroupUpdateView(generics.UpdateAPIView):
    serializer_class = DataPermissionsGroupUpdateSerializer

    def get_queryset(self):
        return DataPermissions.objects.filter(is_deleted=False)

    def update(self, request, *args, **kwargs):
        group_id = request.data.get('group_id')
        model_path = request.data.get('model_path')
        exclusions = request.data.get('exclusions')
        if group_id is None or model_path is None or exclusions is None:
            return Response({"error": "model_id, model_path, and exclusions are required."}, status=status.HTTP_400_BAD_REQUEST)
        result = DataPermissions.objects.filter(group_id=group_id, model_path=model_path, is_deleted=False)
        total_records = result.count()
        result.update(exclusions=exclusions)
        return Response({
            "message": f"Updated exclusions for {total_records} records.",
            "total_records_updated": total_records
        }, status=status.HTTP_200_OK)

class DataPermissionsExclusionsRetrieveView(generics.ListAPIView):
    def get_queryset(self):
        user_type = self.request.query_params.get("user_type")
        user_identifier = self.request.query_params.get("user_identifier")
        model_path = self.request.query_params.get("model_path")
        if not user_type or not user_identifier or not model_path:
            return DataPermissions.objects.none()
        return DataPermissions.objects.filter(user_type=user_type, user_identifier=user_identifier, model_path=model_path)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response({"error": "No records found."}, status=status.HTTP_404_NOT_FOUND)
        exclusions_data = queryset.values("exclusions")
        return Response(exclusions_data, status=status.HTTP_200_OK)

class DataPermissionsGroupExclusionsRetrieveView(generics.ListAPIView):
    def get_queryset(self):
        group_id = self.kwargs.get("group_id")
        model_path = self.kwargs.get("model_path")
        if not group_id or not model_path:
            return DataPermissions.objects.none()
        return DataPermissions.objects.filter(group_id=group_id, model_path=model_path, is_deleted=False)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response({"error": "No records found."}, status=status.HTTP_404_NOT_FOUND)
        exclusions_data = queryset.values("exclusions").distinct()
        return Response(exclusions_data, status=status.HTTP_200_OK)

class DataPermissionDeleteView(generics.DestroyAPIView):
    serializer_class = DataPermissionsSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_deleted=False)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()

# -------------------- ContentTypeDetail Model Views -------------------- #

class ContentTypeDetailFilter(FilterSet):
    class Meta:
        model = ContentTypeDetail
        fields = ['contenttype', 'show_in_data_permissions', 'hide']

class ContentTypeDetailList(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)
    queryset = ContentTypeDetail.objects.filter(show_in_data_permissions=True)
    serializer_class = AllContentTypesSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ContentTypeDetailFilter
    ordering_fields = ['code', 'created_on']
    search_fields = ['code', 'name']

class AuthorizationContentTypeDetailList(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)
    queryset = ContentTypeDetail.objects.filter(show_in_authorization=True)
    serializer_class = AllContentTypesSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ContentTypeDetailFilter
    ordering_fields = ['created_on']
    search_fields = ['name']
    
    
class ContentTypeMini(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = ContentType.objects.all()
    serializer_class = AllContentTypeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['app_label', 'model']

# -------------------- Masters (Dynamic Model) Views -------------------- #

class MastersDetailList(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]
    serializer_class = DynamicIDNameSerializer

    def get_queryset(self):
        app_label = self.kwargs.get("app_label")
        model = self.kwargs.get("model_name")
        try:
            model_class = apps.get_model(app_label, model)
            f_id = model_class._meta.get_field('id')
            has_uuid = isinstance(f_id, models.UUIDField)
            has_name = model_has_field(model_class, 'name')
            data_field = "name" if has_name else 'code'
            keys = ["id", data_field]
            self.filterset_fields = keys
            self.search_fields = [data_field]
            if model_has_field(model_class, 'is_deleted'):
                return model_class.objects.filter(is_deleted=False).values(*keys)
            else:
                return model_class.objects.values(*keys)
        except LookupError:
            return []

    # def list(self, request, *args, **kwargs):
    #     app_label = self.kwargs.get("app_label")
    #     model = self.kwargs.get("model_name")
    #     try:
    #         model_class = apps.get_model(app_label, model)
    #         f_id = model_class._meta.get_field('id')
    #         has_uuid = isinstance(f_id, models.UUIDField)
    #         has_name = model_has_field(model_class, 'name')
    #         data_field = "name" if has_name else "code"
    #         keys = ["id", data_field]
    #         self.filterset_fields = keys
    #         self.search_fields = [data_field]
    #         if model_has_field(model_class, "is_deleted"):
    #             queryset = list(model_class.objects.filter(is_deleted=False).values(*keys))
    #         else:
    #             queryset = list(model_class.objects.values(*keys))
    #     except Exception:
    #         return Response({"count": 0, "results": []})
    #     queryset = self.filter_queryset(queryset)
    #     page = self.paginate_queryset(queryset)
    #     if page is not None:
    #         queryset = page
    #     if not has_name:
    #         for item in queryset:
    #             item["name"] = item.pop("code")
    #     return Response({"count": len(queryset), "results": queryset})

# -------------------- Group, Permission, DjangoApp Views -------------------- #

class GroupList(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

class GroupDetails(generics.RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    def destroy(self, request, *args, **kwargs):
        group = self.get_object()
        assigned_users_count = group.user_set.count()
        if assigned_users_count > 0:
            return Response(
                {
                    "message": (
                        f'Cannot delete group "{group.name}" because {assigned_users_count} user(s) '
                        "are still assigned to this group."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        group_name = group.name
        group.delete()
        return Response(
            {"message": f'Group "{group_name}" deleted successfully.'},
            status=status.HTTP_200_OK
        )

class GroupPermissionAdd(generics.UpdateAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupMini2Serializer

    def put(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.permissions.add(request.data['permission_id'])
        return Response({}, status=status.HTTP_200_OK)

class GroupPermissionRemove(generics.UpdateAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupMini2Serializer

    def put(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.permissions.remove(request.data['permission_id'])
        return Response({}, status=status.HTTP_200_OK)

class UserGroupList(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserGroupSerializer

class PermissionList(generics.ListAPIView):
    queryset = Permission.objects.all()
    serializer_class = PermissionJoinSerializer

class DjangoAppPermissionList(generics.ListAPIView):
    permission_classes = [GetPermission('auth.add_group')]
    serializer_class = DjangoAppSerializer
    pagination_class = None
    
    def get_queryset(self):
        queryset = DjangoApp.objects.filter(hide=False)
        # Check if any records have sequence values
        has_sequence = queryset.exclude(sequence__isnull=True).exclude(sequence=0).exists()
        if has_sequence:
            return queryset.order_by('sequence', 'name')
        else:
            return queryset.order_by('name')

class ContentTypeList(generics.ListAPIView):
    queryset = ContentType.objects.all()
    serializer_class = ContentTypeSerializer
    permission_lables = {
        "add_village": "Add",
        "change_village": "Update",
        "delete_village": "Delete",
        "view_village": "View",
    }

    def get(self, request, *args, **kwargs):
        if request.user.is_superuser:
            qs = ContentType.objects.filter(Q(~Q(app_label__in=['admin', 'contenttypes', 'sessions', 'token_blacklist', 'System']) & ~Q(model__in=['country', 'district', 'village', ])))
        else:
            qs = ContentType.objects.filter(Q(~Q(app_label__in=['admin', 'contenttypes', 'sessions', 'token_blacklist']) & ~Q(model__in=['country', 'district', 'village', ])))
        serializer = ContentTypeSerializer(instance=qs, many=True)
        data = serializer.data
        return Response({"data": data, "permission_lables": self.permission_lables}, status=status.HTTP_200_OK)

# -------------------- Authorization & AuthorizationHistory Model Views -------------------- #

class AuthorizationDefinitionFilter(FilterSet):
    start_date = DateFilter(field_name='created_on', lookup_expr='gte')
    end_date = DateFilter(field_name='created_on', lookup_expr='lte')

    class Meta:
        model = AuthorizationDefinition
        fields = ['start_date', 'end_date', 'screen']

class AuthorizationDefinitionList(generics.ListAPIView):
    serializer_class = AuthorizationDefinitionSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_deleted=False).order_by('-id')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = AuthorizationDefinitionFilter
    search_fields = ['code', 'level', 'screen__model']
    ordering_fields = ['code']

class AuthorizationDefinitionCreate(generics.CreateAPIView):
    serializer_class = AuthorizationDefinitionSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_deleted=False).order_by('-id')

    def _validate_level_authorizations(self, level_authorizations):
        errors = []
        for idx, level_auth in enumerate(level_authorizations or []):
            level_num = level_auth.get('level')
            auth_type = level_auth.get('type')
            user_identifier = level_auth.get('user_identifier')
            user_type = level_auth.get('user_type')
            group_id = level_auth.get('group_id')

            if level_num is None:
                errors.append({'index': idx, 'level': ['Level is required.']})
                continue

            if auth_type == 1:
                level_errors = {}
                if not user_identifier:
                    level_errors['user_identifier'] = ['User is required.']
                if not user_type:
                    level_errors['user_type'] = ['User type is required.']
                if level_errors:
                    level_errors['level'] = level_num
                    errors.append(level_errors)
            elif auth_type == 2:
                if not group_id:
                    errors.append({'level': level_num, 'group_id': ['Group is required.']})

        if errors:
            raise ValidationError({'level_authorizations': errors})

    def perform_create(self, serializer):
        auth_def = serializer.save()
        
        # Create Authorization records from request data
        level_authorizations = self.request.data.get('level_authorizations', [])
        self._validate_level_authorizations(level_authorizations)
        for level_auth in level_authorizations:
            Authorization.objects.create(
                authorization_definition=auth_def,
                type=level_auth.get('type'),
                user_identifier=level_auth.get('user_identifier'),
                user_type=level_auth.get('user_type'),
                group_id=level_auth.get('group_id'),
                screen=auth_def.screen,
                level=level_auth.get('level'),
                send_email=level_auth.get('send_email', False),
                send_sms=level_auth.get('send_sms', False),
                send_notification=level_auth.get('send_notification', False)
            )

class AuthorizationDefinitionDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AuthorizationDefinitionSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_deleted=False)

    def _validate_level_authorizations(self, level_authorizations):
        errors = []
        for idx, level_auth in enumerate(level_authorizations or []):
            level_num = level_auth.get('level')
            auth_type = level_auth.get('type')
            user_identifier = level_auth.get('user_identifier')
            user_type = level_auth.get('user_type')
            group_id = level_auth.get('group_id')

            if level_num is None:
                errors.append({'index': idx, 'level': ['Level is required.']})
                continue

            if auth_type == 1:
                level_errors = {}
                if not user_identifier:
                    level_errors['user_identifier'] = ['User is required.']
                if not user_type:
                    level_errors['user_type'] = ['User type is required.']
                if level_errors:
                    level_errors['level'] = level_num
                    errors.append(level_errors)
            elif auth_type == 2:
                if not group_id:
                    errors.append({'level': level_num, 'group_id': ['Group is required.']})

        if errors:
            raise ValidationError({'level_authorizations': errors})

    def perform_update(self, serializer):
        auth_def = serializer.save()
        
        # Handle level_authorizations update
        level_authorizations = self.request.data.get('level_authorizations', [])
        self._validate_level_authorizations(level_authorizations)
        existing_levels = {auth.level: auth for auth in auth_def.level_authorizations.filter(is_deleted=False)}
        
        # Track which levels are in the request
        requested_levels = set()
        
        for level_auth in level_authorizations:
            level_num = level_auth.get('level')
            requested_levels.add(level_num)
            
            if level_num in existing_levels:
                # Update existing
                auth = existing_levels[level_num]
                auth.type = level_auth.get('type', auth.type)
                auth.user_identifier = level_auth.get('user_identifier', auth.user_identifier)
                auth.user_type = level_auth.get('user_type', auth.user_type)
                auth.group_id = level_auth.get('group_id', auth.group_id)
                auth.send_email = level_auth.get('send_email', auth.send_email)
                auth.send_sms = level_auth.get('send_sms', auth.send_sms)
                auth.send_notification = level_auth.get('send_notification', auth.send_notification)
                auth.save()
            else:
                # Create new
                Authorization.objects.create(
                    authorization_definition=auth_def,
                    type=level_auth.get('type'),
                    user_identifier=level_auth.get('user_identifier'),
                    user_type=level_auth.get('user_type'),
                    group_id=level_auth.get('group_id'),
                    screen=auth_def.screen,
                    level=level_num,
                    send_email=level_auth.get('send_email', False),
                    send_sms=level_auth.get('send_sms', False),
                    send_notification=level_auth.get('send_notification', False)
                )
        
        # Delete levels not in request
        for level_num, auth in existing_levels.items():
            if level_num not in requested_levels:
                auth.is_deleted = True
                auth.save()

    def perform_destroy(self, instance):
        from django.db import transaction
        from django.apps import apps
        from django.utils import timezone
        from .models import Authorization, AuthorizationHistory
 
        with transaction.atomic():
            instance.is_deleted = True
            instance.status = False
            instance.save(update_fields=['is_deleted', 'status'])
 
            Authorization.objects.filter(
                screen=instance.screen,
                level=instance.level,
                is_deleted=False
            ).update(is_deleted=True)
 
            AuthorizationHistory.objects.filter(
                screen=instance.screen,
                authorized_level=instance.level,
                is_deleted=False
            ).update(is_deleted=True)
           
            # Auto-approve pending records if no auth definitions remain
            if not AuthorizationDefinition.objects.filter(screen=instance.screen, is_deleted=False).exists():
                try:
                    model_class = apps.get_model(instance.screen.app_label, instance.screen.model)
                    user = self.request.user
                    model_class.objects.filter(authorized_status=1, is_deleted=False).update(
                        authorized_status=2,
                        authorized_by_type=user.__class__.__name__,
                        authorized_by_identifier=user.id,
                        authorized_on=timezone.now()
                    )
                except Exception:
                    pass
 
class AuthorizationFilter(FilterSet):
    class Meta:
        model = Authorization
        fields = ['group', 'screen', 'type', 'level']

class AuthorizationCreate(generics.CreateAPIView):
    queryset = Authorization.objects.filter(is_deleted=False)
    serializer_class = AuthorizationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AuthorizationFilter
    ordering_fields = ['code', 'created_on']
    search_fields = ['user_identifier', 'user_type', 'code', 'group__name']

    def perform_create(self, serializer):
        serializer.save()

class AuthorizationDetails(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AuthorizationSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_deleted=False)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AuthorizationFilter
    ordering_fields = ['code', 'created_on']
    search_fields = ['user_identifier', 'user_type', 'code', 'group__name']

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        from django.apps import apps
        from django.utils import timezone
       
        instance.is_deleted = True
        instance.save()
       
        # Auto-approve pending records if no authorizations remain for this screen
        if not Authorization.objects.filter(screen=instance.screen, is_deleted=False).exists():
            try:
                model_class = apps.get_model(instance.screen.app_label, instance.screen.model)
                user = self.request.user
                model_class.objects.filter(authorized_status=1, is_deleted=False).update(
                    authorized_status=2,
                    authorized_by_type=user.__class__.__name__,
                    authorized_by_identifier=user.id,
                    authorized_on=timezone.now()
                )
            except Exception:
                pass

class AuthorizationList(generics.ListAPIView):
    serializer_class = AuthorizationSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_deleted=False)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AuthorizationFilter
    search_fields = ['user_identifier', 'user_type', 'code', 'group__name']
    ordering_fields = ['code']

class AuthorizationHistoryFilter(FilterSet):
    class Meta:
        model = AuthorizationHistory
        fields = ['authorized_status', 'screen', 'authorized_level']

class AuthorizationHistoryView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AuthorizationHistorySerializer
    model = serializer_class.Meta.model
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AuthorizationHistoryFilter
    search_fields = ['description', 'authorized_by_identifier', 'authorized_by_type']

    def get_queryset(self):
        model_path = self.kwargs.get('model_path')
        instance_id = self.kwargs.get('instance_id')
        
        try:
            app_label, model_name = model_path.split('.')
            app_label_key = app_label.strip().lower()
            model_key = model_name.strip().lower()
            
            # Map frontend app labels to actual Django app labels
            app_label_map = {
                ('sales', 'salesorder'): 'Sales',
                ('sales', 'invoice'): 'Invoice',
                ('delivery', 'dispatchplan'): 'Dispatch',
                ('dispatch', 'dispatchplan'): 'Dispatch',
                ('delivery', 'proofofdelivery'): 'Delivery',
                ('masters', 'scheme'): 'Masters',
                ('masters', 'pricebookdocument'): 'Masters',
                ('invoice', 'invoice'): 'Invoice',
            }
            
            # Get the actual Django app label
            actual_app_label = app_label_map.get((app_label_key, model_key), app_label)
            
            # Use case-insensitive ContentType lookup
            content_type = ContentType.objects.get(app_label__iexact=actual_app_label, model__iexact=model_key)
        except (ValueError, ContentType.DoesNotExist):
            return AuthorizationHistory.objects.none()
        
        # Filter by screen, instance_id, and exclude deleted records
        active_q = Q(is_deleted=False) | Q(is_deleted__isnull=True)
        queryset = AuthorizationHistory.objects.filter(
            screen=content_type,
            instance_id=str(instance_id)
        ).filter(active_q).order_by('authorized_level', 'authorized_on')
        
        return queryset

class CheckAuthorizationView(generics.CreateAPIView):
    serializer_class = CheckAuthorizationHistorySerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_deleted=False)

    def create(self, request, *args, **kwargs):
        serializer = CheckAuthorizationHistorySerializer(data=request.data, context={'request': request, 'kwargs': kwargs})
        serializer.is_valid(raise_exception=True)
        return Response({}, status=status.HTTP_200_OK)
    
class CheckBulkAuthorizationView(generics.CreateAPIView):
    serializer_class = CheckBulkAuthorizationHistorySerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_deleted=False)

    def create(self, request, *args, **kwargs):
        serializer = CheckBulkAuthorizationHistorySerializer(data=request.data, context={'request': request, 'kwargs': kwargs})
        serializer.is_valid(raise_exception=True)
        return Response({}, status=status.HTTP_200_OK)


class CanAuthorizeView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, app_label, model_name, instance_id):
        try:
            user = request.user
            
            # Map frontend app labels to actual Django app labels
            app_label_map = {
                ('sales', 'salesorder'): 'Sales',
                ('sales', 'invoice'): 'Invoice',
                ('delivery', 'dispatchplan'): 'Dispatch',
                ('delivery', 'proofofdelivery'): 'Delivery',
                ('masters', 'scheme'): 'Masters',
                ('masters', 'pricebookdocument'): 'Masters',
            }
            
            # Get the actual Django app label
            actual_app_label = app_label_map.get((app_label.lower(), model_name.lower()))
            
            try:
                if actual_app_label:
                    model_class = apps.get_model(actual_app_label, model_name)
                else:
                    try:
                        model_class = apps.get_model(app_label, model_name)
                    except LookupError:
                        model_class = apps.get_model(app_label.capitalize(), model_name)
                
                content_type = ContentType.objects.get_for_model(model_class)
                instance = model_class.objects.get(id=instance_id)
            except (LookupError, model_class.DoesNotExist):
                return Response({"can_authorize": False}, status=status.HTTP_404_NOT_FOUND)
            
            if user.is_superuser:
                return Response({"can_authorize": True}, status=status.HTTP_200_OK)
            
            # Check if rejected
            if instance.authorized_status == 3:
                return Response({"can_authorize": False}, status=status.HTTP_200_OK)

            # Draft records are outside authorization workflow.
            if instance.authorized_status == 0:
                return Response({"can_authorize": False}, status=status.HTTP_200_OK)
            
            authorization_obj = _get_user_authorization_for_screen(user, content_type)
            
            if not authorization_obj:
                return Response({"can_authorize": False}, status=status.HTTP_200_OK)
            
            if instance.authorized_level == authorization_obj.level - 1:
                return Response({"can_authorize": True}, status=status.HTTP_200_OK)
            
            return Response({"can_authorize": False}, status=status.HTTP_200_OK)
        except Exception as e:
            # Log error but return False instead of crashing
            return Response({"can_authorize": False}, status=status.HTTP_200_OK)


class PendingApproversView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, app_label, model_name, instance_id):
        # Map frontend app labels to actual Django app labels
        app_label_map = {
            ('sales', 'salesorder'): 'Sales',
            ('sales', 'invoice'): 'Invoice',
            ('delivery', 'dispatchplan'): 'Dispatch',
            ('delivery', 'proofofdelivery'): 'Delivery',
            ('masters', 'scheme'): 'Masters',
            ('masters', 'pricebookdocument'): 'Masters',
        }
        
        # Get the actual Django app label
        actual_app_label = app_label_map.get((app_label.lower(), model_name.lower()))
        
        try:
            # Try mapped app label first
            if actual_app_label:
                model_class = apps.get_model(actual_app_label, model_name)
            else:
                # Try to get model with the provided app_label first
                try:
                    model_class = apps.get_model(app_label, model_name)
                except LookupError:
                    # If not found, try with capitalized app_label (e.g., 'sales' -> 'Sales')
                    model_class = apps.get_model(app_label.capitalize(), model_name)
        except LookupError:
            return Response({"level": None, "approvers": []}, status=status.HTTP_404_NOT_FOUND)

        try:
            # Always use get_for_model to get the correct ContentType
            instance = model_class.objects.get(id=instance_id)
        except model_class.DoesNotExist:
            return Response({"level": None, "approvers": []}, status=status.HTTP_404_NOT_FOUND)

        try:
            from Core.Users.serializers import get_pending_approvers_payload
            payload = get_pending_approvers_payload(instance)
            return Response(payload, status=status.HTTP_200_OK)
        except Exception as e:
            import traceback
            return Response({"level": None, "approvers": []}, status=status.HTTP_200_OK)

class BulkAuthorizationView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Authorization.objects.none()  # Required for ListAPIView
    serializer_class = AuthorizationSerializer  # Any serializer, not used in POST

    def get_queryset(self):
        # This only matters for GET requests, not POST
        return Authorization.objects.none()

    def post(self, request, app_label, model_name):
        try:
            # Map frontend app labels to actual Django app labels
            app_label_map = {
                ('sales', 'salesorder'): 'Sales',
                ('sales', 'invoice'): 'Invoice',
                ('delivery', 'dispatchplan'): 'Dispatch',
                ('delivery', 'proofofdelivery'): 'Delivery',
                ('masters', 'scheme'): 'Masters',
                ('masters', 'pricebookdocument'): 'Masters',
            }
            
            # Get the actual Django app label
            actual_app_label = app_label_map.get((app_label.lower(), model_name.lower()), app_label)
            
            # Get the model class using ContentType lookup
            content_type = ContentType.objects.get(app_label__iexact=actual_app_label, model=model_name.lower())
            model_class = content_type.model_class()
        except ContentType.DoesNotExist:
            return Response(
                {"error": "Invalid app_label or model_name"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get request data
        # instances_data = request.data.get('instances', [])
        # if not instances_data:
        #     return Response(
        #         {"error": "No instances provided"},
        #         status=status.HTTP_400_BAD_REQUEST
        #     )

        # Get current user info
        user = request.user
        user_type = user.__class__.__name__
        user_identifier = str(user.id)

        # Check if user has authorization permission for this screen
        authorization_obj = _get_user_authorization_for_screen(user, content_type)
 
 
        if not authorization_obj and not user.is_superuser:
            return Response({"error": "No Authorization Permission"}, status=status.HTTP_200_OK)
        
        instances_data = request.data.get('instances', [])
        if not instances_data:
            return Response(
                {"error": "No instances provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        results = []

        with transaction.atomic():
            for instance_data in instances_data:
                instance_id = instance_data.get("instance_id")
                authorized_status = instance_data.get("authorized_status")
                description = instance_data.get("description", "")

                if not instance_id or authorized_status not in [1, 2, 3]:
                    results.append({
                        "instance_id": instance_id,
                        "authorized_status": None,
                        "description": "Invalid data provided",
                        "success": False,
                    })
                    continue

                try:
                    instance = model_class.objects.get(id=instance_id)

                    # Create authorization history
                    AuthorizationHistory.objects.create(
                        screen=content_type,
                        instance_id=str(instance_id),
                        authorized_level=authorization_obj.level if authorization_obj else 1,
                        authorized_status=authorized_status,
                        description=description,
                        authorized_by_identifier=user_identifier,
                        authorized_by_type=user_type,
                    )

                    # Update instance fields if applicable
                    if hasattr(instance, "current_authorized_status"):
                        instance.current_authorized_status = authorized_status
                        instance.current_authorized_level = authorization_obj.level if authorization_obj else 1
                        instance.current_authorized_by_type = user_type
                        instance.current_authorized_by_identifier = user_identifier

                        is_final_approval = False
                        if authorized_status == 2:  # Approved
                            from Core.Users.models import AuthorizationDefinition
                            auth_def = AuthorizationDefinition.objects.filter(
                                screen=content_type,
                            ).filter(_active_soft_delete_q()).filter(
                                Q(status=True),
                                Q(effective_from__lte=now().date()) | Q(effective_from__isnull=True)
                            ).order_by('-effective_from', '-created_on').first()
 
                            if user.is_superuser or (auth_def and (authorization_obj.level if authorization_obj else 1) >= auth_def.level):
                                # Final approval - mark as fully approved
                                instance.authorized_status = 2
                                instance.authorized_level = authorization_obj.level if authorization_obj else 1
                                instance.authorized_by_type = user_type
                                instance.authorized_by_identifier = user_identifier
                                is_final_approval = True
                            else:
                                # Intermediate approval - move to next level
                                instance.authorized_level = authorization_obj.level if authorization_obj else 1

                        elif authorized_status == 3:  # Rejected
                            instance.authorized_status = 3
                            instance.authorized_level = authorization_obj.level if authorization_obj else 1
                            instance.authorized_by_type = user_type
                            instance.authorized_by_identifier = user_identifier

                        # Keep transaction status aligned with authorization state for models
                        # that use DRAFT/PENDING/CONFIRMED progression.
                        if hasattr(instance, "status"):
                            try:
                                status_field = instance._meta.get_field("status")
                                valid_statuses = {choice[0] for choice in getattr(status_field, "choices", [])}
                            except Exception:
                                valid_statuses = set()

                            current_status = str(getattr(instance, "status", "") or "").upper()
                            if current_status != 'DRAFT' and 'PENDING' in valid_statuses and 'CONFIRMED' in valid_statuses:
                                target_status = 'CONFIRMED' if (authorized_status == 2 and is_final_approval) else 'PENDING'
                                if current_status != target_status:
                                    instance.status = target_status

                        instance.save()

                    results.append({
                        "instance_id": instance_id,
                        "authorized_status": authorized_status,
                        "description": description,
                        "success": True,
                    })

                except model_class.DoesNotExist:
                    results.append({
                        "instance_id": instance_id,
                        "authorized_status": None,
                        "description": "Instance not found",
                        "success": False,
                    })
                except Exception as e:
                    results.append({
                        "instance_id": instance_id,
                        "authorized_status": None,
                        "description": f"Error: {str(e)}",
                        "success": False,
                    })

        return Response(results, status=status.HTTP_200_OK)
    
class AuthorizationHistoryCreate(generics.CreateAPIView):
    serializer_class = AuthorizedHistorySerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_deleted=False).order_by('-created_on')

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(authorized_by_identifier=user.id, authorized_by_type=type(user).__name__)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request, 'kwargs': kwargs})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class InstanceAuthorizationHistoryView(generics.RetrieveAPIView):
    serializer_class = InstanceAuthorizationHistorySerializer
    model = serializer_class.Meta.model
    filter_backends = [DjangoFilterBackend, filters.SearchFilter,filters.OrderingFilter]
    search_fields = ['description', 'authorized_by_identifier', 'authorized_by_type']
    queryset = model.objects.all()
 
    def get_queryset(self):
        model_path = self.kwargs.get('model_path')  # format: app_label.model_name
 
        try:
            app_label, model_name = model_path.split('.')
            app_label_key = app_label.strip().lower()
            model_key = model_name.strip().lower()
            
            # Map frontend app labels to actual Django app labels
            app_label_map = {
                ('sales', 'salesorder'): 'Sales',
                ('sales', 'invoice'): 'Invoice',
                ('delivery', 'dispatchplan'): 'Dispatch',
                ('dispatch', 'dispatchplan'): 'Dispatch',
                ('delivery', 'proofofdelivery'): 'Delivery',
                ('masters', 'scheme'): 'Masters',
                ('masters', 'pricebookdocument'): 'Masters',
                ('invoice', 'invoice'): 'Invoice',
            }
            
            # Get the actual Django app label
            actual_app_label = app_label_map.get((app_label_key, model_key), app_label)
            
            content_type = ContentType.objects.get(app_label__iexact=actual_app_label, model__iexact=model_key)
            model_class = content_type.model_class()
            queryset = model_class.objects.all()
 
            return queryset
 
        except (ValueError, ContentType.DoesNotExist):
            raise NotFound("Instance not found")


# -------------------- Assignee, AssigneeDefnition, AssigneeByPass Model Views -------------------- #

class AssigneeDefnitionFilter(FilterSet):
    start_date = DateFilter(field_name='created_on', lookup_expr='gte')
    end_date = DateFilter(field_name='created_on', lookup_expr='lte')

    class Meta:
        model = AssigneeDefnition
        fields = ['start_date', 'end_date', 'screen', 'apply_type']

class AssigneeDefnitionList(generics.ListAPIView):
    serializer_class = AssigneeDefnitionSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_deleted=False).order_by('-id')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = AssigneeDefnitionFilter
    search_fields = ['code', 'level']
    ordering_fields = ['code']

class AssigneeDefnitionCreate(generics.CreateAPIView):
    serializer_class = AssigneeDefnitionSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_deleted=False).order_by('-id')

    def perform_create(self, serializer):
        serializer.save()

class AssigneeDefnitionDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AssigneeDefnitionSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_deleted=False)

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()

class AssigneeUserTypesAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, app_label, model_name):
        if not model_name or not app_label:
            return Response({'error': 'Invalid or missing Model Name and App Label'}, status=status.HTTP_400_BAD_REQUEST)
        assignee = AssigneeDefnition.objects.filter(screen__app_label=app_label, screen__model=model_name.lower()).first()
        if not assignee:
            return Response({'error': 'Assignee definition not found for this screen'}, status=status.HTTP_404_NOT_FOUND)
        
        if not assignee:
            return Response({"count": 0, "results": []}, status=status.HTTP_200_OK)

        user_types = assignee.user_types or []

        type_name_map = {
            entry["type"]: entry["name"] for entry in getattr(settings, "USER_MODELS", [])
        }

        data = [
            {
                "user_type": ut,
                "user_type_name": type_name_map.get(ut, ut)
            }
            for ut in user_types
        ]
        return Response(data, status=status.HTTP_200_OK)

class AssigneeFilter(FilterSet):
    instance_id = django_filters.CharFilter(field_name='instance_id', lookup_expr='icontains')
    model_path = django_filters.CharFilter(method='filter_by_model_path')

    class Meta:
        model = Assignee
        fields = ['screen', 'instance_id']

    def filter_by_model_path(self, queryset, name, value):
        try:
            content_type = ContentType.objects.get(model=value.split('.')[-1].lower(), app_label=value.split('.')[0])
            return queryset.filter(screen=content_type)
        except ContentType.DoesNotExist:
            return queryset.none()

class AssigneeCreate(generics.CreateAPIView):
    queryset = Assignee.objects.filter(is_deleted=False)
    serializer_class = AssigneeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AssigneeFilter
    ordering_fields = ['code', 'created_on']
    search_fields = ['code', 'user_identifier', 'user_type', 'instance_id']

    def perform_create(self, serializer):
        serializer.save()

class AssigneeDetails(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AssigneeSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_deleted=False)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AssigneeFilter
    ordering_fields = ['code', 'created_on']
    search_fields = ['code', 'user_identifier', 'user_type', 'instance_id']

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()

class AssigneeList(generics.ListAPIView):
    serializer_class = AssigneeSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_deleted=False)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AssigneeFilter
    search_fields = ['code', 'user_type', 'user_identifier']
    ordering_fields = ['code']

class CheckAddAssignView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, model_path, *args, **kwargs):
        try:
            app_label, model_name = model_path.split('.')
            model_name = model_name.lower()
            asd_odj = AssigneeDefnition.objects.filter(
                screen__app_label=app_label,
                screen__model=model_name,
                is_deleted=False
            ).first()
            if asd_odj:
                if request.user.has_perm(f"{app_label}.add_assignee_{model_name}"):
                    return Response({"has_permission": True}, status=status.HTTP_200_OK)
                else:
                    return Response({"has_permission": False})
            else:
                return Response({"has_permission": False, "detail": "Assignee definition not found."}, status=status.HTTP_404_NOT_FOUND)
        except (ValueError, ContentType.DoesNotExist):
            return Response({"has_permission": False})

class AssigneeByPassFilter(FilterSet):
    class Meta:
        model = AssigneeByPass
        fields = ['type', 'group']

class AssigneeByPassCreate(generics.CreateAPIView):
    queryset = AssigneeByPass.objects.filter(is_deleted=False)
    serializer_class = AssigneeByPassSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AssigneeByPassFilter
    ordering_fields = ['code', 'created_on']
    search_fields = ['code', 'user__username']

    def perform_create(self, serializer):
        serializer.save()

class AssigneeByPassDetails(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AssigneeByPassSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_deleted=False)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AssigneeByPassFilter
    ordering_fields = ['code', 'created_on']
    search_fields = ['code', 'user__username']

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()

class AssigneeByPassList(generics.ListAPIView):
    serializer_class = AssigneeByPassSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.filter(is_deleted=False)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AssigneeByPassFilter
    search_fields = ['user__username', 'code']
    ordering_fields = ['code']

# -------------------- UserPreferences Model Views -------------------- #

class UserPreferencesAPIView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        user = self.request.user
        user_type= user.__class__.__name__
        user_identifier = user.id

        preferences = request.data.get("preferences")
        if preferences is None:
            return Response({"error": "Missing user or preferences"}, status=status.HTTP_400_BAD_REQUEST)
        preferences_json = json.dumps(preferences)
        user_preferences, created = UserPreferences.objects.update_or_create(
            user_identifier=user_identifier,
            user_type=user_type,
            defaults={"preferences": preferences_json}
        )
        return Response(
            {
                "message": "Preferences saved successfully",
                "created": created,
                "data": {
                    "preferences": json.loads(user_preferences.preferences),
                }
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )

    def get(self, request, user_id=None, user_type=None):
        if user_id:
            try:
                user_preferences = UserPreferences.objects.get(user_identifier=user_id, user_type=user_type)
                return Response(
                    {
                        "user": str(user_preferences.user_identifier),
                        "preferences": json.loads(user_preferences.preferences),
                    },
                    status=status.HTTP_200_OK
                )
            except UserPreferences.DoesNotExist:
                return Response({"error": "Preferences not found"}, status=status.HTTP_404_NOT_FOUND)
        user_preferences = UserPreferences.objects.all()
        data = [
            {
                "user": str(pref.user_identifier) if pref.user_identifier else None,
                "preferences": json.loads(pref.preferences) if pref.preferences else {},
            }
            for pref in user_preferences
        ]
        return Response(data, status=status.HTTP_200_OK)


class UserPreferencesByRequestUser(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user = self.request.user
        user_type= user.__class__.__name__
        user_identifier = user.id

        if user:
            try:
                user_preferences = UserPreferences.objects.get(user_type=user_type, user_identifier= user_identifier)
                return Response(
                    {
                        "user": str(user_preferences.user_identifier),
                        "preferences": json.loads(user_preferences.preferences),
                    },
                    status=status.HTTP_200_OK
                )
            except UserPreferences.DoesNotExist:
                return Response({"error": "Preferences not found"}, status=status.HTTP_404_NOT_FOUND)
            

class GetAuthorizationStatus(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
 
    def get_queryset(self):
        app_label = self.kwargs.get('app_label')
        model_name = self.kwargs.get('model_name')
       
        if app_label == 'undefined':
            raise NotFound(detail="Invalid format provided for App Label", code=404)
        if model_name == 'undefined':
            raise NotFound(detail="Invalid format provided for Model Name", code=404)
 
        # Map frontend app labels to actual Django app labels
        app_label_map = {
            ('sales', 'salesorder'): 'Sales',
            ('sales', 'invoice'): 'Invoice',
            ('delivery', 'dispatchplan'): 'Dispatch',
            ('delivery', 'proofofdelivery'): 'Delivery',
            ('masters', 'scheme'): 'Masters',
            ('masters', 'pricebookdocument'): 'Masters',
        }
        
        # Get the actual Django app label
        actual_app_label = app_label_map.get((app_label.lower(), model_name.lower()), app_label)
 
        try:
            # Use ContentType with mapped app label
            content_type = ContentType.objects.get(app_label__iexact=actual_app_label, model=model_name.lower())
            model_class = content_type.model_class()
        except ContentType.DoesNotExist:
            raise ValidationError("Invalid app_label or model_name.")
 
        self.queryset = model_class.objects.filter(is_deleted=False)
        return super().get_queryset()
 
    def get(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
        except Exception as e:
            return Response({
                "Pending": 0,
                "Approved": 0,
                "Rejected": 0,
                "Skipped": 0,
            }, status=status.HTTP_200_OK)
            
        user = request.user
        app_label = self.kwargs.get('app_label')
        model_name = self.kwargs.get('model_name')
        
        # Map frontend app labels to actual Django app labels
        app_label_map = {
            ('sales', 'salesorder'): 'Sales',
            ('sales', 'invoice'): 'Invoice',
            ('delivery', 'dispatchplan'): 'Dispatch',
            ('delivery', 'proofofdelivery'): 'Delivery',
            ('masters', 'scheme'): 'Masters',
            ('masters', 'pricebookdocument'): 'Masters',
        }
        
        # Get the actual Django app label
        actual_app_label = app_label_map.get((app_label.lower(), model_name.lower()), app_label)
 
        if not queryset.exists():
            return Response({
                "Pending": 0,
                "Approved": 0,
                "Rejected": 0,
                "Skipped": 0,
            }, status=status.HTTP_200_OK)
        
        # Get user's authorization level
        try:
            content_type = ContentType.objects.get(app_label__iexact=actual_app_label, model=model_name.lower())
            model_class = content_type.model_class()
            
            # Superuser sees all pending records
            if user.is_superuser:
                pending_qs = queryset.filter(authorized_status=1)
                if model_has_field(model_class, 'status'):
                    pending_qs = pending_qs.exclude(status='DRAFT')
                pending_count = pending_qs.count()
            else:
                authorization_obj = _get_user_authorization_for_screen(user, content_type)
                
                if authorization_obj:
                    user_auth_level = authorization_obj.level
                    
                    # Get auth definition separately to avoid complex query
                    auth_def = authorization_obj.authorization_definition
                    
                    # Build filter for pending records
                    pending_filter = Q(
                        authorized_status=1,
                        authorized_level=user_auth_level - 1
                    )
                    
                    # Add company/location filters if specified
                    if auth_def and not auth_def.has_all_companies:
                        # Get company IDs from the M2M relationship
                        company_ids = auth_def.companies.values_list('id', flat=True)
                        if company_ids:
                            if hasattr(model_class, 'company'):
                                pending_filter &= Q(company_id__in=company_ids)
                            elif hasattr(model_class, 'companies'):
                                pending_filter &= Q(companies__id__in=company_ids)
                    
                    if auth_def and not auth_def.has_all_locations:
                        # Get location IDs from the M2M relationship
                        location_ids = auth_def.locations.values_list('id', flat=True)
                        if location_ids and hasattr(model_class, 'location'):
                            pending_filter &= Q(location_id__in=location_ids)
                    
                    pending_qs = queryset.filter(pending_filter)
                    if model_has_field(model_class, 'status'):
                        pending_qs = pending_qs.exclude(status='DRAFT')
                    pending_count = pending_qs.count()
                else:
                    pending_count = 0
        except Exception as e:
            pending_count = 0
 
        status_counts = {
            "Pending": pending_count,
            "Approved": queryset.filter(authorized_status=2).count(),
            "Rejected": queryset.filter(authorized_status=3).count(),
            "Skipped": queryset.filter(authorized_status=4).count(),
        }
 
        return Response(status_counts, status=status.HTTP_200_OK)
    

class UserTypesPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100        
        
class UserTypesListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = UserTypesPagination

    def get(self, request, app_label, model_name):
        if not model_name or not app_label:
            return Response({'error': 'Invalid or missing Model Name and App Label'}, status=status.HTTP_400_BAD_REQUEST)

        # Step 1: Get UserType object via ContentType match
        user_type_obj = UserType.objects.filter(
            screen__app_label=app_label,
            screen__model=model_name.lower(),
            is_deleted=False
        ).first()
        if not user_type_obj:
            return Response({"count": 0, "results": []}, status=status.HTTP_200_OK)

        user_types = user_type_obj.user_types or []

        # Optional: Map type → name using settings
        type_name_map = {
            entry["type"]: entry["name"] for entry in getattr(settings, "USER_MODELS", [])
        }

        data = [
            {
                "user_type": ut,
                "user_type_name": type_name_map.get(ut, ut)
            }
            for ut in user_types
        ]

        return Response({"count": len(data), "results": data}, status=status.HTTP_200_OK)


class LocationsByCompanyAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, company_id):
        from Masters.models import Location
        locations = Location.objects.filter(companies__id=company_id, is_deleted=False).values('id', 'name').distinct()
        return Response(list(locations), status=status.HTTP_200_OK)


class UsersByCompanyLocationAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        company_id = request.query_params.get('company')
        location_id = request.query_params.get('location')
        include_all = request.query_params.get('all')
        search = request.query_params.get('search')

        base_qs = User.objects.filter(
            Q(channel_partner_type='STAFF') | Q(channel_partner_type__isnull=True),
            is_active=True
        )

        if include_all in ('1', 'true', 'True', 'yes', 'YES'):
            users = base_qs
        else:
            if not company_id and not location_id:
                return Response(
                    {'error': 'company and/or location parameters are required (or use all=1)'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            users = base_qs
            if company_id:
                users = users.filter(Q(companies__id=company_id) | Q(has_all_companies=True))
            if location_id:
                users = users.filter(Q(locations__id=location_id) | Q(has_all_locations=True))

        if search:
            users = users.filter(
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )

        users = users.distinct().order_by('username')
        
        # Apply logged-in user's company/location filter
        from utils import apply_company_location_filter_for_users
        users = apply_company_location_filter_for_users(users, request.user)
        
        users = users.values('id', 'username', 'first_name', 'last_name', 'email')
        return Response(list(users), status=status.HTTP_200_OK)


class PendingAuthorizationsView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = pagination.PageNumberPagination
    
    def get_serializer_class(self):
        app_label = self.kwargs.get('app_label')
        model_name = self.kwargs.get('model_name')
        
        # Map models to their list serializers
        # Note: app_label here refers to what the frontend passes, not necessarily the Django app
        serializer_map = {
            ('sales', 'salesorder'): 'Sales.serializers.SalesOrderListSerializer',
            ('sales', 'invoice'): 'Invoice.serializers.InvoiceListSerializer',
            ('delivery', 'dispatchplan'): 'Dispatch.serializers.DispatchPlanListSerializer',
            ('delivery', 'proofofdelivery'): 'Delivery.serializers.ProofOfDeliveryListSerializer',
            ('masters', 'scheme'): 'Masters.serializers.SchemeSerializer',
            ('masters', 'pricebookdocument'): 'Masters.serializers.PriceBookDocumentSerializer',
        }
        
        serializer_path = serializer_map.get((app_label.lower(), model_name.lower()))
        if serializer_path:
            module_path, class_name = serializer_path.rsplit('.', 1)
            module = __import__(module_path, fromlist=[class_name])
            return getattr(module, class_name)
        
        # Fallback to a generic serializer
        from rest_framework import serializers
        
        # Try to get model with case-insensitive fallback
        try:
            try:
                model = apps.get_model(app_label, model_name)
            except LookupError:
                model = apps.get_model(app_label.capitalize(), model_name)
        except LookupError:
            return None
        

    def get_queryset(self):
        app_label = self.kwargs.get('app_label')
        model_name = self.kwargs.get('model_name')
        user = self.request.user
        
        # Map frontend app labels to actual Django app labels
        app_label_map = {
            ('sales', 'salesorder'): 'Sales',
            ('sales', 'invoice'): 'Invoice',
            ('delivery', 'dispatchplan'): 'Dispatch',
            ('delivery', 'proofofdelivery'): 'Delivery',
            ('masters', 'scheme'): 'Masters',
            ('masters', 'pricebookdocument'): 'Masters',
        }
        
        # Get the actual Django app label
        actual_app_label = app_label_map.get((app_label.lower(), model_name.lower()))
        
        # Try to get model with mapped or provided app_label
        try:
            if actual_app_label:
                model_class = apps.get_model(actual_app_label, model_name)
            else:
                # Fallback: try with provided or capitalized app_label
                try:
                    model_class = apps.get_model(app_label, model_name)
                except LookupError:
                    model_class = apps.get_model(app_label.capitalize(), model_name)
        except LookupError:
            return []
        
        # Get content type from model class
        try:
            content_type = ContentType.objects.get_for_model(model_class)
        except Exception:
            return model_class.objects.none()
        
        # Superuser can approve any pending record at any level
        if user.is_superuser:
            queryset = model_class.objects.filter(
                authorized_status=1,
                is_deleted=False
            ).order_by('-created_on')
            if model_has_field(model_class, 'status'):
                queryset = queryset.exclude(status='DRAFT')
            return queryset
        
        # Get user's authorization level
        authorization_obj = _get_user_authorization_for_screen(user, content_type)
        
        if not authorization_obj:
            return model_class.objects.none()
        user_auth_level = authorization_obj.level
        
        # Get auth definition separately
        auth_def = authorization_obj.authorization_definition
        
        # Build filter for pending records
        filters = Q(
            authorized_status=1,
            authorized_level=user_auth_level - 1,
            is_deleted=False
        ) & ~Q(status='DRAFT')
        
        # Add company/location filters if specified in auth definition
        if auth_def and not auth_def.has_all_companies:
            company_ids = auth_def.companies.values_list('id', flat=True)
            if company_ids:
                if hasattr(model_class, 'company'):
                    filters &= Q(company_id__in=company_ids)
                elif hasattr(model_class, 'companies'):
                    filters &= Q(companies__id__in=company_ids)
        
        if auth_def and not auth_def.has_all_locations:
            location_ids = auth_def.locations.values_list('id', flat=True)
            if location_ids and hasattr(model_class, 'location'):
                filters &= Q(location_id__in=location_ids)
        
        queryset = model_class.objects.filter(filters).order_by('-created_on')
        
        # Apply user's company/location filter on top of authorization definition filters
        from utils import apply_company_location_filter
        if hasattr(model_class, 'company'):
            company_field = 'company'
        elif hasattr(model_class, 'companies'):
            company_field = 'companies'
        else:
            company_field = None
        location_field = 'location' if hasattr(model_class, 'location') else None
        if company_field or location_field:
            queryset = apply_company_location_filter(
                queryset, user,
                company_field=company_field,
                location_field=location_field
            )
        
        return queryset
