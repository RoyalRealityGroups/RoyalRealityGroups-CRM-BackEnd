from rest_framework import serializers

from .models import GeneralSettings


class GeneralSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneralSettings
        fields = (
            "id",
            "company_scoped_item_enforcement",
            "allow_multiple_schemes",
        )
        read_only_fields = ("id",)
