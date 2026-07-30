from django.urls import path
from . import views

urlpatterns = [
    path('', views.ProjectList.as_view()),
    path('export/', views.ProjectExportView.as_view(), name='project-export'),
    path('choices/', views.ProjectChoices.as_view()),
    path('mini/', views.ProjectMini.as_view()),
    path('<str:pk>/', views.ProjectDetail.as_view()),
    path('<str:project_id>/images/', views.ProjectImageList.as_view()),
    path('<str:project_id>/images/upload/', views.ProjectImageUpload.as_view()),
    path('images/<str:pk>/', views.ProjectImageDetail.as_view()),
]
