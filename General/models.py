from django.db import models

# Create your models here.


class ImportPermission(models.Model):
    """
    Model to hold custom permissions for Import module.
    This model won't store data, just provides ContentType for permissions.
    """
    
    class Meta:
        verbose_name = "Import Permission"
        verbose_name_plural = "Import Permissions"
        default_permissions = ()  # Don't create default add/change/delete/view permissions
        permissions = [
            ('view_import_data', 'Can view import data'),
            ('view_import_history', 'Can view import history'),
            ('view_general_settings', 'Can view general settings'),
            ('modify_general_settings', 'Can modify general settings'),
        ]


class GeneralSettings(models.Model):
    """
    Global application settings controlled from General Settings screen.
    Singleton model (single row) accessed via get_solo().
    """

    company_scoped_item_enforcement = models.BooleanField(
        default=False,
        help_text='When enabled, item must belong to selected company in sales flows',
    )
    allow_multiple_schemes = models.BooleanField(
        default=True,
        help_text='When disabled, only one scheme can be selected per sales order',
    )

    class Meta:
        verbose_name = "General Settings"
        verbose_name_plural = "General Settings"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={
                "company_scoped_item_enforcement": False,
                "allow_multiple_schemes": True,
            },
        )
        return obj

    @classmethod
    def is_company_scoped_item_enforcement_enabled(cls) -> bool:
        return bool(cls.get_solo().company_scoped_item_enforcement)

    @classmethod
    def is_allow_multiple_schemes_enabled(cls) -> bool:
        return bool(cls.get_solo().allow_multiple_schemes)
