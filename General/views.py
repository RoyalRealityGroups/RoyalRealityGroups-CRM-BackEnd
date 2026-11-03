from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

from .models import GeneralSettings, ThemeSettings
from .serializers import GeneralSettingsSerializer, ThemeSettingsSerializer


class GeneralSettingsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def _has_view_access(self, request):
        """All authenticated users can view general settings."""
        user = request.user
        return bool(user and user.is_authenticated)

    def _has_update_access(self, request):
        """Only superusers can modify general settings."""
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_superuser or user.has_perm('General.modify_general_settings'))
        )

    def get(self, request):
        if not self._has_view_access(request):
            return Response({'detail': 'You do not have permission to view general settings.'}, status=status.HTTP_403_FORBIDDEN)

        settings_obj = GeneralSettings.get_solo()
        serializer = GeneralSettingsSerializer(settings_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        if not self._has_update_access(request):
            return Response({'detail': 'You do not have permission to update general settings.'}, status=status.HTTP_403_FORBIDDEN)

        settings_obj = GeneralSettings.get_solo()

        # Handle logo removal
        if 'company_logo' in request.data and (request.data['company_logo'] is None or request.data['company_logo'] == 'null'):
            settings_obj.company_logo = None
            settings_obj.save(update_fields=['company_logo'])
            data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
            data.pop('company_logo', None)
            if not data:
                return Response(GeneralSettingsSerializer(settings_obj).data, status=status.HTTP_200_OK)
            serializer = GeneralSettingsSerializer(settings_obj, data=data, partial=True)
        else:
            serializer = GeneralSettingsSerializer(settings_obj, data=request.data, partial=True)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


# Default theme values — used by the "Reset to defaults" action.
THEME_DEFAULTS = {
    'primary_color': '#4F46E5',
    'secondary_color': '#10B981',
    'background_color': '#F8FAFC',
    'paper_color': '#FFFFFF',
    'text_primary_color': '#0F172A',
    'text_secondary_color': '#475569',
    'success_color': '#10B981',
    'error_color': '#EF4444',
    'warning_color': '#F59E0B',
    'info_color': '#06B6D4',
    'heading_font': 'Outfit',
    'body_font': 'Plus Jakarta Sans',
    'border_radius': 10,
}


class ThemeSettingsView(APIView):
    """
    App-wide appearance / theme settings.

    GET   — PUBLIC (AllowAny) so the theme can load before the user logs in.
    PATCH — admin / superuser only.
    """
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def _has_update_access(self, request):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_superuser or getattr(user, 'is_admin', False)
                 or user.has_perm('General.modify_general_settings'))
        )

    def get(self, request):
        theme = ThemeSettings.get_solo()
        return Response(ThemeSettingsSerializer(theme).data, status=status.HTTP_200_OK)

    def patch(self, request):
        if not self._has_update_access(request):
            return Response(
                {'detail': 'You do not have permission to update theme settings.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        theme = ThemeSettings.get_solo()
        serializer = ThemeSettingsSerializer(theme, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Reset the theme to factory defaults (admin only)."""
        if not self._has_update_access(request):
            return Response(
                {'detail': 'You do not have permission to reset theme settings.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if request.data.get('action') != 'reset':
            return Response({'detail': 'Unsupported action.'}, status=status.HTTP_400_BAD_REQUEST)
        theme = ThemeSettings.get_solo()
        for field, value in THEME_DEFAULTS.items():
            setattr(theme, field, value)
        theme.save()
        return Response(ThemeSettingsSerializer(theme).data, status=status.HTTP_200_OK)
