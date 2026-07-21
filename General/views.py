from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

from .models import GeneralSettings
from .serializers import GeneralSettingsSerializer


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
