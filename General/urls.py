from django.urls import path

from .views import GeneralSettingsView, ThemeSettingsView


urlpatterns = [
    path('general-settings/', GeneralSettingsView.as_view()),
    path('theme-settings/', ThemeSettingsView.as_view()),
]
