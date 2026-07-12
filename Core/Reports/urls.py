from . import views
from . import generic_import_export_view
from django.urls import include, path


urlpatterns = [
    path('generic_import/<str:dryrun>', generic_import_export_view.GenericImportView.as_view(), name='GenericImport'), # dryrun ='dryrun' or 'process'
    path('generic_import_models/', generic_import_export_view.GenericImportModelsView.as_view(), name='GenericImportModels'),
    path('generic_export_models/', generic_import_export_view.GenericExportModelsView.as_view(), name='GenericExportModels'), 
    
    path('generic_export/', generic_import_export_view.GenericExportView.as_view(), name='GenericExport'),
    path('generic_import_2/<str:dryrun>/', generic_import_export_view.ImportView.as_view()),
    
    path('generic_export/status/<request_id>/', generic_import_export_view.CheckExportView.as_view()),
    path('generic_export/download/<request_id>/', generic_import_export_view.DownloadExportView.as_view()),
    
    path('generic_import/status/<request_id>/', generic_import_export_view.CheckImportView.as_view()),
    # path('upload/<str:filename>/', importviews.FileUploadView.as_view()),

    path('scheduledemail/', views.ScheduledEmailList.as_view()),
    path("ScheduledEmail/<str:pk>", views.ScheduledEmailDetail.as_view()),

    path('pdf_templates/list/', views.PdfTemplateListCreate.as_view()),
    path('pdf_templates/details/<str:pk>/', views.PdfTemplateDetails.as_view()),

    path('pdf_templates/<str:app_label>/<str:model_name>/', views.PdfTemplateListByModel.as_view(), name='pdf-template-list-by-model'),
    path('pdf_data/<str:pk>/<str:instance_id>/', views.PdfTemplateData.as_view(), name='pdf-template-detail'),
    
    path('reportrequest/list/<str:report_id>/', views.ReportRequestList.as_view(), name='reportrequest-list'),
    path('reportrequest/<str:pk>/', views.ReportRequestDetail.as_view(), name='reportrequest-detail'),

]
