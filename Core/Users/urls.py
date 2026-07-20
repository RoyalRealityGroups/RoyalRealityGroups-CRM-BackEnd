from . import views
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    # -------------------- Authentication -------------------- #
    path('login/', csrf_exempt(views.LoginAPIView.as_view()), name="login"),
    path('logout/', csrf_exempt(views.LogoutAPIView.as_view()), name="logout"),
    path('token/refresh/', csrf_exempt(views.TokenRefreshView.as_view()), name='token_refresh'),
    path('otprequest/', views.OTPRequestAPIView.as_view(), name="otprequest"),
    # path('resendotp/', views.OTPResendAPIView.as_view(), name="otpresend"),
    path('email-verify/', views.VerifyEmail.as_view(), name="email-verify"),
    path('forgot-password/', csrf_exempt(views.ForgotPasswordAPIView.as_view()), name="forgot-password"),
    path('reset-password-confirm/', csrf_exempt(views.ResetPasswordConfirmView.as_view()), name="reset-password-confirm"),
    path('validate-username/', csrf_exempt(views.ValidateUsernameView.as_view()), name="validate-username"),

    # -------------------- User Management -------------------- #
    path('iamuser/', views.IamUserDetails.as_view(), name='iamuser'),
    path('userinactive/<str:id>', views.UserInActive.as_view()),
    path('useractive/<str:id>', views.UserActive.as_view()),
    path('username/validation/', views.UserNameValidate.as_view()),
    path('useremail/validation/', views.UserEmailValidate.as_view()),
    path('userphone/validation/', views.UserPhoneValidate.as_view()),
    path('validate-current-password/', csrf_exempt(views.ValidateCurrentPasswordView.as_view()), name="validate-current-password"),
    path('changepassword/', views.ChangePasswordView.as_view(), name="changepassword"),
    path('updatepassword/<str:id>', views.UpdatePasswordView.as_view(), name="updatepassword"),
    path('logged_in_users/', views.LoggedInUsersAPIView.as_view(), name='logged_in_users'),

    # -------------------- Groups & Permissions -------------------- #
    path('groups/', views.GroupList.as_view(), name='groups'),
    path('groups/<str:pk>', views.GroupDetails.as_view(), name='groups'),
    # path('groupspermissionadd/<str:pk>', views.GroupPermissionAdd.as_view(), name='groups'),
    # path('groupspermissionrermove/<str:pk>', views.GroupPermissionRemove.as_view(), name='groups'),
    # path('usergroups/', views.UserGroupList.as_view(), name='usergroups'),
    path('permissions/', views.PermissionList.as_view(), name='permissions'),
    path('apps/permissions/', views.DjangoAppPermissionList.as_view(), name='DjangoAppPermissionList'),
    # path('contenttypes/', views.ContentTypeList.as_view(), name='contenttypes'),

    # -------------------- Devices & Device Logs -------------------- #
    path('userdevices/me', views.UserDevicesByMe.as_view()),
    path("userdevices/<str:pk>", views.UserDevices.as_view()),
    path('userdevices/user/<str:user_identifier>/<str:user_type>', views.UserDevicesByUser.as_view()),
    path('devicelog/', views.DeviceLogs.as_view(), name='devicelogall'),
    path('devicelog/me/', views.DeviceLogByMe.as_view(), name='devicelog'),
    path('devicelog/user/<str:user_identifier>/<str:user_type>', views.DeviceLogByUser.as_view()),

    # -------------------- Data Permissions -------------------- #
    path('allcontenttypes/', views.ContentTypeDetailList.as_view(), name='allcontenttypes'),
    path('mini/contenttypes/', views.ContentTypeMini.as_view(), name='mini_contenttypes'),
    path('authorization_contenttypes/', views.AuthorizationContentTypeDetailList.as_view(), name='authorization_contenttypes'),
    path('masterapis/<str:app_label>/<str:model_name>/', views.MastersDetailList.as_view(), name='MastersDetailList'),
    path('datapermissions/create/', views.DataPermissionsCreate.as_view()),
    path('update/datapermissions/<int:pk>', views.DataPermissionsUpdate.as_view()),
    path('datapermissions/list/<str:model_path>/', views.DataPermissionsList.as_view()),
    path('datapermissions/<int:pk>', views.DataPermissionDeleteView.as_view()),
    path('user_permissions/update/', views.DataPermissionsUpdateView.as_view(), name='update-permission'),
    path('group_permissions/exclusions/update/', views.DataPermissionsGroupUpdateView.as_view(), name='update-permission'),
    path('users/permissions/exclusions/', views.DataPermissionsExclusionsRetrieveView.as_view(), name='data-permissions-exclusions'),
    path('groups/permissions/exclusions/<int:group_id>/<str:model_path>/', views.DataPermissionsGroupExclusionsRetrieveView.as_view(), name='group_data-permissions-exclusions'),

    # -------------------- Authorization -------------------- #
    path('authorization_defnitions/create/', views.AuthorizationDefinitionCreate.as_view()),
    path('authorization_defnitions/', views.AuthorizationDefinitionList.as_view()),
    path('authorization_defnitions/<str:pk>', views.AuthorizationDefinitionDetail.as_view()),
    path('authorizations/create/', views.AuthorizationCreate.as_view()),
    path('authorizations/', views.AuthorizationList.as_view()),
    path('authorizations/<str:pk>/', views.AuthorizationDetails.as_view()),
    path('authorization_history/<str:model_path>/<str:instance_id>/', views.AuthorizationHistoryView.as_view(), name='authorization_history'),
    path('check_authorization/<str:app_label>/<str:model_name>/<str:instance_id>/', views.CheckAuthorizationView.as_view(), name='check_authorization'),
    path('check_authorization/<str:app_label>/<str:model_name>/', views.CheckBulkAuthorizationView.as_view(), name='check_authorization'),
    path('can_authorize/<str:app_label>/<str:model_name>/<str:instance_id>/', views.CanAuthorizeView.as_view(), name='can_authorize'),
    path('pending_approvers/<str:app_label>/<str:model_name>/<str:instance_id>/', views.PendingApproversView.as_view(), name='pending_approvers'),
    path('bulk-authorization/<str:app_label>/<str:model_name>/', views.BulkAuthorizationView.as_view()),
    path('authorization/<str:app_label>/<str:model_name>/', views.AuthorizationHistoryCreate.as_view()),
    path('get_authorization_status/<str:app_label>/<str:model_name>/', views.GetAuthorizationStatus.as_view(), name='get_authorization_status'), # Old authorization_counts URL for backward compatibility
    path('authorization_counts/<str:app_label>/<str:model_name>/', views.GetAuthorizationStatus.as_view(), name='authorization_counts'),
    path('pending_authorizations/<str:app_label>/<str:model_name>/', views.PendingAuthorizationsView.as_view(), name='pending_authorizations'),
    path('instance_authorization_history/<str:model_path>/<str:pk>/', views.InstanceAuthorizationHistoryView.as_view(), name='instance_authorization_history'),

    # -------------------- Assignees -------------------- #
    path('assignees/create/', views.AssigneeCreate.as_view()),
    path('assignees/', views.AssigneeList.as_view()),
    path('assignees/<str:pk>/', views.AssigneeDetails.as_view()),
    path('checkaddassign/<str:model_path>/', views.CheckAddAssignView.as_view(), name='check_assignees'),
    path('assignee_defnitions/create/', views.AssigneeDefnitionCreate.as_view()),
    path('assignee_defnitions/', views.AssigneeDefnitionList.as_view()),
    path('assignee_defnitions/<str:pk>', views.AssigneeDefnitionDetail.as_view()),
    path("assignee_def/user_types/<str:app_label>/<str:model_name>/", views.AssigneeUserTypesAPIView.as_view(), name="assignee-user-types"),
    path('assigneesbypass/create/', views.AssigneeByPassCreate.as_view()),
    path('assigneesbypass/', views.AssigneeByPassList.as_view()),
    path('assigneesbypass/<str:pk>/', views.AssigneeByPassDetails.as_view()),

    # -------------------- User Preferences -------------------- #
    path('user_preferences/', views.UserPreferencesAPIView.as_view(), name='userpreferences'),
    path('user_preferencesbyrequestuser/', views.UserPreferencesByRequestUser.as_view(), name='create_userpreferences'),

    # -------------------- Miscellaneous -------------------- #
    # path('mini/reporting_users/', views.ReportingUsersMini.as_view()),


    path('user_types/<str:app_label>/<str:model_name>/', views.UserTypesListAPIView.as_view(), name='usertypes'),
    path('locations-by-company/<str:company_id>/', views.LocationsByCompanyAPIView.as_view(), name='locations_by_company'),
    path('users-by-company-location/', views.UsersByCompanyLocationAPIView.as_view(), name='users_by_company_location'),
]
