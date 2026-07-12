from django.urls import path

from .views import GeneralSettingsView


urlpatterns = [
    path('general-settings/', GeneralSettingsView.as_view()),
]
