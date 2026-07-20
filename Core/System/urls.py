from . import views
from django.urls import path , include

from rest_framework import routers


urlpatterns = [
    path('user_menu/', views.UserMenuList.as_view()),
    path('user_menu/<int:pk>', views.UserMenuDetail.as_view()),
    path('user_menu/<str:code>', views.UserMenuDetailByCode.as_view()),
    path('menu/', views.MenuList.as_view()),
    path("menu/<int:pk>", views.MenuDetail.as_view()),
    path('submenu/', views.SubmenuList.as_view()),
    path("submenu/<int:pk>", views.SubmenuDetail.as_view()),
    path('menuitem/', views.MenuitemList.as_view()),
    path('menuitems/searchlist/', views.MenuitemList2.as_view(),), # global search
    path("menuitem/<int:pk>", views.MenuitemDetail.as_view()),
    path('Notification/', views.NotificationList.as_view()),
    path('Notification/Clear/<str:pk>/', views.NotificationClear.as_view()),
    path('Notification/ClearAll/', views.NotificationClearAll.as_view(),),
    path('Database/DoBackup', views.BackupNow.as_view()),
    path('Database/Backup', views.BackupList.as_view()),
    path('Database/downloadBackup/<int:pk>', views.BackupValidation.as_view()),
    path('Database/DoRestore/<int:pk>', views.RestoreNow.as_view()),
    path('Database/Restore', views.RestoreList.as_view()),

    path('RestoreById/<id>', views.RestoreById),
    path('DownloadById/<id>', views.DownloadById),
    
    path('Database/Reset/<str:dryrun>', views.ResetDatabase.as_view()),
    path('attachment/', views.AttachmentCreate.as_view()),
    path("attachment/<int:pk>", views.AttachmentDetail.as_view()),

    # path('formula/', views.FormulaList.as_view()),
    # path('allformuls/', views.AllFormulasList.as_view()), # with out pagination api
    # path("formula/<int:pk>", views.FormulaDetail.as_view()),
    # path('formulaexecuter/', views.FormulaExecuter.as_view()),
    # path('formulavalidator/', views.FormulaValidator.as_view()),
    # path('formulaupdate/<int:pk>', views.FormulaUpdateList.as_view()),


    path('dynamicsettings/', views.DynamicSettings.as_view({'get': 'get','post':"bulk"})),
    path('dynamicsettings/<str:section__name>', views.DynamicSettings.as_view({'get': 'retrieve', 'put': 'update',  'patch': 'partial_update' })),

    # path('variables/', views.FormulaVariablesList.as_view()),
    # path("variables/<int:pk>", views.FormulaVariablesDetail.as_view()),



    path('activitylog/', views.ActivityLogList.as_view()), #activity log
    path("activitylog/<str:pk>", views.ActivityLogDetail.as_view()),
    path('mini/activitylog/', views.ActivityLogMini.as_view()),
    path('activitylog/user/<str:pk>', views.ActivityLogByUser.as_view()),
    path('activitylog/user/', views.ActivityLogByUserListView.as_view()),


    path('auditlog/', views.AuditLogList.as_view()), #audit log

    path('sms/', views.SmsList.as_view()),
    path('error/', views.ErrorList.as_view()),
    
    path('maintenance/', views.Maintenance_On.as_view()),
    path('maintenance_off/', views.Maintenance_Off.as_view()),
    
    path('io_login/', views.IO_LogIn.as_view()),
    path('io_logout/', views.IO_LogOut.as_view()),

    path('temp_otp/request/', views.TemporaryOTPRequestView.as_view()),
    path('temp_otp/verify/', views.TemporaryVerifyOTPView.as_view()),
    path('temp_otp/resend/', views.TemporaryOTPResendView.as_view()),

    path('customer/otp/request/', views.TemporaryOTPRequestView.as_view()),

    path("globalvariables/sync/jsondata/", views.SyncJsonDataView.as_view()),


    path('recentactivity/', views.RecentActivityList.as_view()), #actvity log

    path('settings/preferences/<str:preferences_code>/', views.SettingAPIView.as_view(), name='get_setting'), #get
    path('settings/preferences/', views.SettingAPIView.as_view(), name='create_setting'),  # POST


    path('template/', views.TemplateList.as_view()),
    path('template/<str:pk>', views.TemplateDetail.as_view()),
    path('template/mini/', views.TemplateMini.as_view()),
    path('templates/status/<str:template_id>/', views.TemplateStatusUpdateView.as_view(), name='template-status-update'),

    path('alertconfigs/create/', views.AlertConfigCreate.as_view()),
    path('alertconfigs/', views.AlertConfigList.as_view()),
    path('alertconfigs/<int:pk>', views.AlertConfigDetail.as_view()),


    path('annoncements/create/', views.AnnouncementCreate.as_view()),
    path('annoncements/', views.AnnouncementsList.as_view()),
    path('annoncements/<str:pk>', views.AnnouncementDetail.as_view()),

    # path('api/unified-filter/', views.UnifiedFilterAPIView, name='unified-filter'),

    # path('api/available-filters/',views.AvailableFiltersAPIView.as_view(), name='available-filters'),
    
    path('task-scheduler-list/', views.TaskSchedulerList.as_view(), name='task_scheduler_list'),
    path('task-scheduler-create/', views.TaskSchedulerCreate.as_view(), name='task_scheduler_create'),
    path('task-scheduler-detail/<str:pk>/', views.TaskSchedulerDetail.as_view(), name='task_scheduler_detail'),

    path('thread/list-active-threads/', views.ActiveThreadsListAPIView.as_view(), name='list-active-threads'),
    path('thread/start/<str:task_id>/', views.StartTaskAPIView.as_view(), name='start-task'),
    path('thread/stop/<str:task_id>/', views.StopTaskAPIView.as_view(), name='stop-task'),
    path('threads/status/', views.TaskStatusAPIView.as_view(), name='task-status'),
    path('thread/kill-expired/', views.KillExpiredThreadsAPIView.as_view(), name='kill-expired-threads'),

    # Advanced Filtering - Saved Filters
    path('saved-filters/', views.SavedFilterListCreate.as_view(), name='saved-filters-list-create'),
    path('saved-filters/<int:pk>/', views.SavedFilterDetail.as_view(), name='saved-filter-detail'),
    path('saved-filters/<int:pk>/apply/', views.apply_saved_filter, name='apply-saved-filter'),
    
    # Advanced Filtering - Filter Presets
    path('filter-presets/', views.FilterPresetList.as_view(), name='filter-presets-list'),
    path('filter-presets/<int:pk>/', views.FilterPresetDetail.as_view(), name='filter-preset-detail'),
]
