from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import GeneralSettings
from .serializers import GeneralSettingsSerializer


class GeneralSettingsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

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
        serializer = GeneralSettingsSerializer(settings_obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
