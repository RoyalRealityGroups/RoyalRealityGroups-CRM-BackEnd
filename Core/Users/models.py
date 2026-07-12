from django.core.cache import cache
import uuid
from django.db import models
from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin)

from django.utils import timezone
from django.contrib.postgres.fields import ArrayField
import datetime

from Core.Core.context.Context import get_user
from Core.Core.permissions.DataPermissions import get_data_permission_functions
from Core.Core.utils.formaters import format_variables


# from Masters.models import Area, City, Location, Zone


LOCATIONTYPE_CHOICES = (
    (1, "Location"),
    (2, "Area"),
    (3, "City"),
    (4, "Zone"),
)


class CoreUserManager(BaseUserManager):

    def create_user(self, username, password=None, **kwargs):
        if username is None:
            raise TypeError('Users should have a username')

        user = self.model(**kwargs, username=username, )
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, password=None, **kwargs):
        if password is None:
            raise TypeError('Password should not be none')

        user = self.create_user(username, password)
        user.is_superuser = True
        user.is_staff = True
        user.save()
        return user


DEVICE_ACCESS_CHOICES = (
    (1, 'Only Mobile'),
    (2, 'Only Web'),
    (3, 'Both'),
    (4, 'None'),

)

GENDER_CHOICES = (
    (1, 'Male'),
    (2, 'Female'),
    (3, 'Others')
)


class CoreUser(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profilepicture = models.ImageField(upload_to='profilepicture', default='', null=True, blank=True)
    username = models.CharField(max_length=255, unique=True, db_index=True)
    email = models.EmailField(max_length=255, db_index=True, blank=True, null=True)
    password = models.CharField(max_length=128, blank=True, null=True)
    phone = models.CharField(max_length=15, db_index=True, blank=True, null=True,)
    otp = models.CharField(max_length=6, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    gender = models.SmallIntegerField(choices=GENDER_CHOICES, blank=True, null=True)
    device_access = models.SmallIntegerField(choices=DEVICE_ACCESS_CHOICES, blank=True, null=True, default=1,)
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=datetime.datetime.now, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    receive_email = models.BooleanField(default=True)
    receive_sms = models.BooleanField(default=True)
    receive_notification = models.BooleanField(default=True)

    # created_by = models.ForeignKey(
    #     settings.AUTH_USER_MODEL,
    #     related_name='userscreated',
    #     on_delete=models.RESTRICT,
    #     null=True,
    # )
    # modified_by = models.ForeignKey(
    #     settings.AUTH_USER_MODEL,
    #     related_name='usersupdated',
    #     on_delete=models.RESTRICT,
    #     null=True,
    # )
    created_by_type = models.CharField(max_length=100, null=True, blank=True, db_index=True,)
    created_by_identifier = models.CharField(max_length=255, null=True, blank=True, db_index=True,)

    modified_by_type = models.CharField(max_length=100, null=True, blank=True, db_index=True,)
    modified_by_identifier = models.CharField(max_length=255, null=True, blank=True, db_index=True,)

    erp_id = models.IntegerField(blank=True, null=True, default=None)
    erp_code = models.CharField(max_length=30, null=True, blank=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    objects = CoreUserManager()

    def __str__(self):
        return str(self.username)

    class Meta:
        abstract = True


class Groupdetails(models.Model):
    group = models.OneToOneField(Group, related_name='groupdetails', on_delete=models.CASCADE, null=True)
    user_type = models.CharField(max_length=15, null=True, blank=True)
    reporting_to = models.ForeignKey(Group, related_name='reportingby', on_delete=models.RESTRICT, null=True)
    static = models.BooleanField(default=False)

    def __str__(self):
        return self.group.name + " details"


class DjangoApp(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    app_label = models.CharField(max_length=100, unique=True, null=True, blank=True)
    hide = models.BooleanField(default=False)
    sequence = models.IntegerField(default=0, null=True, blank=True)

    def __str__(self): return str(self.name)


class ContentTypeDetail(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)  # name of the model
    contenttype = models.OneToOneField(
        ContentType,
        related_name='contenttypedetails',
        on_delete=models.CASCADE,
        null=True)
    app = models.ForeignKey(DjangoApp, related_name='contenttypedetails', on_delete=models.RESTRICT, null=True)
    hide = models.BooleanField(default=True)
    show_in_data_permissions = models.BooleanField(default=False, null=True, blank=True)
    show_in_authorization = models.BooleanField(default=False, null=True, blank=True)
    show_in_assignee = models.BooleanField(default=True, null=True, blank=True)
    release = models.BooleanField(default=False)

    def __str__(self): return str(self.name)


class PermissionDetail(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)  # name of the permission
    permission = models.OneToOneField(Permission, related_name='permissiondetails', on_delete=models.CASCADE, null=True)
    hide = models.BooleanField(default=True)
    release = models.BooleanField(default=False)

    def __str__(self): return str(self.name)


class SequenceCode(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    sequence = models.IntegerField(default=0, null=True, blank=True)
    prefix = models.CharField(max_length=100, null=True, blank=True)
    objects = models.Manager()

    def __str__(self): return str(self.name)


class CodeTemplate(models.Model):
    screen = models.ForeignKey(ContentType, related_name='code_templates', on_delete=models.CASCADE, null=True)
    # model_name = models.CharField(max_length=100, unique=True)
    template = models.CharField(max_length=200, blank=True, null=True)
    objects = models.Manager()

    def __str__(self):
        if self.screen:
            return f"{self.screen.model} Template"
        return "None"


def set_financial_year():
    financial_year = cache.get("financial_year")

    if financial_year:
        return financial_year
    else:
        try:
            today = datetime.datetime.now()
            # Financial year starts from April 1st
            if today.month >= 4:
                fy_start = today.year
                fy_end = today.year + 1
            else:
                fy_start = today.year - 1
                fy_end = today.year
            financial_year = f"{str(fy_start)[-2:]}-{str(fy_end)[-2:]}"
            cache.set("financial_year", financial_year, timeout=settings.CACHE_TIME_OUT_ONE_MONTH)
            return financial_year
        except Exception as e:
            return f"Error setting financial year: {e}"


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    erp_id = models.IntegerField(blank=True, null=True, default=None)
    erp_code = models.CharField(max_length=30, null=True, blank=True)
    created_by_type = models.CharField(max_length=100, null=True, blank=True, db_index=True,)
    created_by_identifier = models.CharField(max_length=255, null=True, blank=True, db_index=True,)
    created_on = models.DateTimeField(auto_now_add=True, blank=True)
    modified_by_type = models.CharField(max_length=100, null=True, blank=True, db_index=True,)
    modified_by_identifier = models.CharField(max_length=255, null=True, blank=True, db_index=True,)
    modified_on = models.DateTimeField(blank=True, null=True, auto_now=True)
    is_deleted = models.BooleanField(blank=True, default=False, null=True)

    def save(self, *args, **kwargs):
        user = get_user()

        if user and not user.is_anonymous:
            user_type = user.__class__.__name__
            user_identifier = str(user.id)

            if self._state.adding or self.id is None:
                self.created_by_type = user_type
                self.created_by_identifier = user_identifier
            else:
                self.modified_by_type = user_type
                self.modified_by_identifier = user_identifier

        super().save(*args, **kwargs)

    class Meta:
        abstract = True


def getcode(model, instance=None):
    model_name = model.__name__
    app_label = model._meta.app_label
    prefix = model.CODE_PREFIX
    try:
        sequence_code, sc = SequenceCode.objects.get_or_create(name=model_name)
        sequence = sequence_code.sequence + 1
        SequenceCode.objects.filter(name=model_name).update(sequence=sequence)
    except BaseException:
        sequence = 1

    try:

        template_obj = CodeTemplate.objects.filter(screen__app_label=app_label, screen__model=model_name.lower()).last()
        body_template = template_obj.template

    except BaseException:
        body_template = f"{prefix}-((sequence))"

    context = {
        "instance": instance,
        "financial_year": set_financial_year(),
        "sequence": str(sequence),
        "model_name": model_name,
    }

    final_body = format_variables(body_template, context)

    return f"{final_body}"


class CodeMixModel(BaseModel):
    # Allow null/blank to ease backfilling legacy rows; save() will populate when missing.
    code = models.CharField(max_length=255, unique=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        if (self.code == "" or self.code is None):
            self.code = getcode(self.__class__, self)
        super().save(*args, **kwargs)

    class Meta:
        abstract = True


TYPE_CHOICES = (
    (1, 'User'),
    (2, 'Group')
)


class DataPermissions(models.Model):

    id = models.AutoField(primary_key=True, auto_created=True)
    type = models.SmallIntegerField(choices=TYPE_CHOICES, blank=True, null=True)
    user_identifier = models.CharField(max_length=255, null=True, blank=True)
    user_type = models.CharField(max_length=15, null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, blank=True, null=True)
    model_path = models.CharField(max_length=255, blank=True, null=True)
    instance_id = models.CharField(max_length=255, blank=True, null=True)
    exclusions = models.BooleanField(default=False, blank=True, null=True)
    entry = models.BooleanField(default=False, blank=True, null=True)
    view = models.BooleanField(default=False, blank=True, null=True)
    report = models.BooleanField(default=False, blank=True, null=True)
    is_deleted = models.BooleanField(default=False, blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='datapermissions_create',
        on_delete=models.RESTRICT,
        null=True)
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='datapermissions_update',
        on_delete=models.RESTRICT,
        null=True)


class AssigneeDefnition(CodeMixModel):
    AND = 1
    OR = 2

    APPLY_TYPE_CHOICES = (
        (AND, 'Assignee And Data Permissions'),
        (OR, 'Assignee Or Data Permissions')
    )

    user_types = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    screen = models.ForeignKey(ContentType, related_name='assignee_defnitions', on_delete=models.CASCADE, null=True)
    apply_type = models.SmallIntegerField(choices=APPLY_TYPE_CHOICES, blank=True, null=True, default=1,)
    required_authorization = models.BooleanField(default=False, blank=True, null=True)

    CODE_PREFIX = 'ASGD'

    def __str__(self):
        screen_name = self.screen.model if self.screen else "Unknown Screen"
        return f"Assignee Definition for {screen_name}"


class AssigneeByPass(CodeMixModel):
    USER = 1
    GROUP = 2

    TYPE_CHOICES = [
        (USER, 'User'),
        (GROUP, 'Group')
    ]

    type = models.SmallIntegerField(choices=TYPE_CHOICES, blank=True, null=True)
    user_identifier = models.CharField(max_length=255, null=True, blank=True)
    user_type = models.CharField(max_length=15, null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='assigneebypass', blank=True, null=True)
    screen = models.ForeignKey(ContentType, related_name='assigneebypass', on_delete=models.CASCADE, null=True)

    CODE_PREFIX = 'ASBP'

    def __str__(self):
        if self.type == self.USER and self.user_identifier:
            return f"AssigneeByPass for User: {self.user_identifier}"
        elif self.type == self.GROUP and self.group:
            return f"AssigneeByPass for Group: {self.group.name}"
        return "AssigneeByPass (Unassigned)"


class AuthorizationDefinition(CodeMixModel):
    authorization_name = models.CharField(max_length=255, null=True, blank=True)
    effective_from = models.DateField(null=True, blank=True)
    companies = models.ManyToManyField('Masters.Company', blank=True, related_name='authorization_definitions')
    has_all_companies = models.BooleanField(default=False)
    locations = models.ManyToManyField('Masters.Location', blank=True, related_name='authorization_definitions')
    has_all_locations = models.BooleanField(default=False)
    status = models.BooleanField(default=True)
    auto_approve_creator_level = models.BooleanField(default=False)
    screen = models.ForeignKey(
        ContentType,
        related_name='authorization_defnitions',
        on_delete=models.CASCADE,
        null=True)
    level = models.IntegerField(null=True, blank=True, default=None, verbose_name="Final Level")
    send_email = models.BooleanField(default=False, blank=True, null=True)
    send_sms = models.BooleanField(default=False, blank=True, null=True)
    send_notification = models.BooleanField(default=False, blank=True, null=True)
    objects = models.Manager()

    CODE_PREFIX = 'AD'

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['screen'],
                condition=models.Q(
                    status=True,
                    has_all_companies=True,
                    has_all_locations=True,
                    is_deleted=False,
                ),
                name='unique_active_global_authorization'
            )
        ]

    def __str__(self):
        return f"{self.authorization_name or 'Authorization'} - Level {self.level} for {self.screen}"


class Authorization(CodeMixModel):
    USER = 1
    GROUP = 2

    TYPE_CHOICES = [
        (USER, 'User'),
        (GROUP, 'Group')
    ]

    authorization_definition = models.ForeignKey(
        AuthorizationDefinition,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='level_authorizations')
    type = models.SmallIntegerField(choices=TYPE_CHOICES, blank=True, null=True)
    user_identifier = models.CharField(max_length=255, null=True, blank=True)
    user_type = models.CharField(max_length=15, null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='authorizations', blank=True, null=True)
    screen = models.ForeignKey(ContentType, related_name='authorizations', on_delete=models.CASCADE, null=True)
    level = models.IntegerField(null=True, blank=True, default=None)
    send_email = models.BooleanField(default=False, blank=True, null=True)
    send_sms = models.BooleanField(default=False, blank=True, null=True)
    send_notification = models.BooleanField(default=False, blank=True, null=True)
    objects = models.Manager()

    CODE_PREFIX = 'AUT'


class AuthorizationHistory(CodeMixModel):

    PENDING = 1
    APPROVED = 2
    REJECTED = 3
    AUTHORIZED_STATUS_CHOICES = (
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected')
    )

    screen = models.ForeignKey(ContentType, related_name='authorization_history', on_delete=models.CASCADE, null=True)
    instance_id = models.CharField(max_length=255, blank=True, null=True)
    authorized_level = models.SmallIntegerField(blank=True, null=True, default=None, )
    authorized_status = models.SmallIntegerField(choices=AUTHORIZED_STATUS_CHOICES, blank=True, null=True)
    description = models.TextField(default='', blank=True, null=True)
    authorized_by_identifier = models.CharField(max_length=255, null=True, blank=True)
    authorized_by_type = models.CharField(max_length=15, null=True, blank=True)
    authorized_on = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    objects = models.Manager()

    CODE_PREFIX = 'AUTH'


class Assignee(CodeMixModel):

    user_identifier = models.CharField(max_length=255, null=True, blank=True)
    user_type = models.CharField(max_length=15, null=True, blank=True)
    screen = models.ForeignKey(ContentType, related_name='assignees', on_delete=models.CASCADE, null=True)
    instance_id = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(default='', blank=True, null=True)

    CODE_PREFIX = 'ASG'


get_qs, get_dp_qs = get_data_permission_functions(DataPermissions, AssigneeDefnition, Assignee)


class CoreManager(models.Manager):

    def get_qs(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        screen_type = kwargs.pop('screen_type', 'view')
        if not user:
            raise Exception("'user' must submit in kwargs in queryset.get_qs() function")

        queryset = super().filter(*args, **kwargs)
        queryset = queryset.filter(is_deleted=False)
        if not getattr(user, "is_authenticated", False):
            return queryset.none()

        if not user.is_superuser:
            app_label = self.model._meta.app_label
            model_name = self.model._meta.model_name
            queryset = get_qs(app_label, model_name, queryset, user, screen_type=screen_type)

        return queryset


class ChannelPartnerManager(CoreManager):

    def get_qs(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        screen_type = kwargs.pop('screen_type', 'view')
        if not user:
            raise Exception("'user' must submit in kwargs in queryset.get_qs() function")

        # Start from the base manager queryset (avoid CoreManager.get_qs recursion).
        queryset = super().filter(*args, **kwargs)
        queryset = queryset.filter(is_deleted=False)
        if not getattr(user, "is_authenticated", False):
            return queryset.none()

        if not user.is_superuser:
            # Apply existing data permissions first
            app_label = self.model._meta.app_label
            model_name = self.model._meta.model_name
            queryset = get_qs(app_label, model_name, queryset, user, screen_type=screen_type)

            # Apply channel partner filtering
            queryset = self._apply_channel_partner_filter(queryset, user)

        return queryset

    def _apply_channel_partner_filter(self, queryset, user):
        """Apply channel partner filtering based on user's assignment"""
        # Staff users see all data
        if user.channel_partner_type == 'STAFF':
            return queryset

        model_name = self.model._meta.model_name

        if model_name == 'superstockist':
            return self._filter_superstockist(queryset, user)
        elif model_name == 'distributor':
            return self._filter_distributor(queryset, user)
        elif model_name == 'retailer':
            return self._filter_retailer(queryset, user)
        elif model_name == 'salesorder':
            return self._filter_sales_order(queryset, user)
        elif model_name == 'salesorderitem':
            return self._filter_sales_order_item(queryset, user)
        elif model_name == 'invoice':
            return self._filter_invoice(queryset, user)
        elif model_name == 'proofofdelivery':
            return self._filter_proof_of_delivery(queryset, user)
        elif model_name == 'receipt':
            return self._filter_receipt(queryset, user)
        elif model_name == 'customerledgerentry':
            return self._filter_customer_ledger(queryset, user)

        return queryset

    def _filter_superstockist(self, queryset, user):
        """Filter superstockist records based on user type"""
        if user.channel_partner_type == 'SUPERSTOCKIST':
            if user.superstockist:
                # Only see their own superstockist
                return queryset.filter(id=user.superstockist.id)
            else:
                # Superstockist user without assigned superstockist - no access
                return queryset.none()
        elif user.channel_partner_type in ['DISTRIBUTOR', 'RETAILER']:
            # See no superstockists (they don't manage this level)
            return queryset.none()
        return queryset

    def _filter_distributor(self, queryset, user):
        """Filter distributor records based on user type"""
        if user.channel_partner_type == 'SUPERSTOCKIST':
            if user.superstockist:
                # See distributors under their superstockist
                return queryset.filter(superstockist=user.superstockist)
            else:
                # Superstockist user without assigned superstockist - no access
                return queryset.none()
        elif user.channel_partner_type == 'DISTRIBUTOR':
            if user.distributor:
                # Only see their own distributor
                return queryset.filter(id=user.distributor.id)
            else:
                # Distributor user without assigned distributor - no access
                return queryset.none()
        elif user.channel_partner_type == 'RETAILER':
            # See no distributors (they don't manage this level)
            return queryset.none()
        return queryset

    def _filter_retailer(self, queryset, user):
        """Filter retailer records based on user type"""
        if user.channel_partner_type == 'SUPERSTOCKIST':
            if user.superstockist:
                # See retailers under distributors under their superstockist
                return queryset.filter(distributor__superstockist=user.superstockist)
            else:
                # Superstockist user without assigned superstockist - no access
                return queryset.none()
        elif user.channel_partner_type == 'DISTRIBUTOR':
            if user.distributor:
                # See retailers under their distributor
                return queryset.filter(distributor=user.distributor)
            else:
                # Distributor user without assigned distributor - no access
                return queryset.none()
        elif user.channel_partner_type == 'RETAILER':
            if user.retailer:
                # Only see their own retailer
                return queryset.filter(id=user.retailer.id)
            else:
                # Retailer user without assigned retailer - no access
                return queryset.none()
        return queryset

    def _filter_sales_order(self, queryset, user):
        """Filter sales orders based on user's channel partner assignment"""
        from django.db.models import Q
        
        if user.channel_partner_type == 'SUPERSTOCKIST':
            if user.superstockist:
                # See orders for their superstockist + distributors + retailers under them
                return queryset.filter(
                    Q(superstockist=user.superstockist) |
                    Q(distributor__superstockist=user.superstockist) |
                    Q(retailer__distributor__superstockist=user.superstockist)
                )
            else:
                return queryset.none()
        elif user.channel_partner_type == 'DISTRIBUTOR':
            if user.distributor:
                # See orders for their distributor + retailers under them
                return queryset.filter(
                    Q(distributor=user.distributor) |
                    Q(retailer__distributor=user.distributor)
                )
            else:
                return queryset.none()
        elif user.channel_partner_type == 'RETAILER':
            if user.retailer:
                # Only see orders for their retailer
                return queryset.filter(retailer=user.retailer)
            else:
                return queryset.none()
        return queryset

    def _filter_sales_order_item(self, queryset, user):
        """Filter sales order items based on user's channel partner assignment"""
        from django.db.models import Q
        
        if user.channel_partner_type == 'SUPERSTOCKIST':
            if user.superstockist:
                return queryset.filter(
                    Q(order__superstockist=user.superstockist) |
                    Q(order__distributor__superstockist=user.superstockist) |
                    Q(order__retailer__distributor__superstockist=user.superstockist)
                )
            else:
                return queryset.none()
        elif user.channel_partner_type == 'DISTRIBUTOR':
            if user.distributor:
                return queryset.filter(
                    Q(order__distributor=user.distributor) |
                    Q(order__retailer__distributor=user.distributor)
                )
            else:
                return queryset.none()
        elif user.channel_partner_type == 'RETAILER':
            if user.retailer:
                return queryset.filter(order__retailer=user.retailer)
            else:
                return queryset.none()
        return queryset

    def _filter_invoice(self, queryset, user):
        """Filter invoices based on user's channel partner assignment"""
        from django.db.models import Q
        
        if user.channel_partner_type == 'SUPERSTOCKIST':
            if user.superstockist:
                return queryset.filter(
                    Q(sales_order__superstockist=user.superstockist) |
                    Q(sales_order__distributor__superstockist=user.superstockist) |
                    Q(sales_order__retailer__distributor__superstockist=user.superstockist)
                )
            else:
                return queryset.none()
        elif user.channel_partner_type == 'DISTRIBUTOR':
            if user.distributor:
                return queryset.filter(
                    Q(sales_order__distributor=user.distributor) |
                    Q(sales_order__retailer__distributor=user.distributor)
                )
            else:
                return queryset.none()
        elif user.channel_partner_type == 'RETAILER':
            if user.retailer:
                return queryset.filter(sales_order__retailer=user.retailer)
            else:
                return queryset.none()
        return queryset

    def _filter_proof_of_delivery(self, queryset, user):
        """Filter proof of delivery based on user's channel partner assignment"""
        from django.db.models import Q
        
        if user.channel_partner_type == 'SUPERSTOCKIST':
            if user.superstockist:
                return queryset.filter(
                    Q(sales_order__superstockist=user.superstockist) |
                    Q(sales_order__distributor__superstockist=user.superstockist) |
                    Q(sales_order__retailer__distributor__superstockist=user.superstockist)
                )
            else:
                return queryset.none()
        elif user.channel_partner_type == 'DISTRIBUTOR':
            if user.distributor:
                return queryset.filter(
                    Q(sales_order__distributor=user.distributor) |
                    Q(sales_order__retailer__distributor=user.distributor)
                )
            else:
                return queryset.none()
        elif user.channel_partner_type == 'RETAILER':
            if user.retailer:
                return queryset.filter(sales_order__retailer=user.retailer)
            else:
                return queryset.none()
        return queryset

    def _filter_receipt(self, queryset, user):
        """Filter receipts based on user's channel partner assignment"""
        from django.db.models import Q
        
        if user.channel_partner_type == 'SUPERSTOCKIST':
            if user.superstockist:
                return queryset.filter(
                    Q(superstockist=user.superstockist) |
                    Q(distributor__superstockist=user.superstockist) |
                    Q(retailer__distributor__superstockist=user.superstockist)
                )
            else:
                return queryset.none()
        elif user.channel_partner_type == 'DISTRIBUTOR':
            if user.distributor:
                return queryset.filter(
                    Q(distributor=user.distributor) |
                    Q(retailer__distributor=user.distributor)
                )
            else:
                return queryset.none()
        elif user.channel_partner_type == 'RETAILER':
            if user.retailer:
                return queryset.filter(retailer=user.retailer)
            else:
                return queryset.none()
        return queryset

    def _filter_customer_ledger(self, queryset, user):
        """Filter customer ledger entries by channel partner assignment."""
        from django.db.models import Q

        if user.channel_partner_type == 'SUPERSTOCKIST':
            if user.superstockist:
                return queryset.filter(
                    Q(superstockist=user.superstockist) |
                    Q(distributor__superstockist=user.superstockist) |
                    Q(retailer__distributor__superstockist=user.superstockist)
                )
            else:
                return queryset.none()
        elif user.channel_partner_type == 'DISTRIBUTOR':
            if user.distributor:
                return queryset.filter(
                    Q(distributor=user.distributor) |
                    Q(retailer__distributor=user.distributor)
                )
            else:
                return queryset.none()
        elif user.channel_partner_type == 'RETAILER':
            if user.retailer:
                return queryset.filter(retailer=user.retailer)
            else:
                return queryset.none()
        return queryset


class CodeModel(CodeMixModel):

    objects = CoreManager()

    class Meta:
        abstract = True


class CoreModel(CodeModel):

    PENDING = 1
    APPROVED = 2
    REJECTED = 3

    AUTHORIZED_STATUS_CHOICES = (
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected')
    )

    authorized_level = models.SmallIntegerField(blank=True, null=True, default=0, )
    authorized_by_type = models.CharField(max_length=30, null=True, blank=True)
    authorized_by_identifier = models.CharField(max_length=255, null=True, blank=True)
    authorized_on = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    current_authorized_level = models.SmallIntegerField(blank=True, null=True, default=0, )
    current_authorized_status = models.SmallIntegerField(
        choices=AUTHORIZED_STATUS_CHOICES, blank=True, null=True, default=1)
    current_authorized_by_type = models.CharField(max_length=30, null=True, blank=True)
    current_authorized_by_identifier = models.CharField(max_length=255, null=True, blank=True)
    current_authorized_on = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    authorized_status = models.SmallIntegerField(choices=AUTHORIZED_STATUS_CHOICES, blank=True, null=True, default=1)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        force_authorization_recalc = kwargs.pop('force_authorization_recalc', False)
        model_ct = ContentType.objects.get_for_model(self.__class__)
        company = getattr(self, 'company', None)
        location = getattr(self, 'location', None)
        status_value = str(getattr(self, 'status', '') or '').upper()
        exclude_fields = {
            'created_on',
            'created_by_type',
            'created_by_identifier',
            'modified_on',
            'modified_by_type',
            'modified_by_identifier',
            'authorized_status',
            'authorized_level',
            'authorized_by_type',
            'authorized_by_identifier',
            'authorized_on',
            'current_authorized_status',
            'current_authorized_level',
            'current_authorized_by_type',
            'current_authorized_by_identifier',
            'current_authorized_on',
            'status',
            'approved_by',
            'approved_at',
            'rejection_reason'}

        # Storage for authorization history to create after save
        auth_history_records = []

        try:
            from django.db.models import Q

            auth_def_query = AuthorizationDefinition.objects.filter(
                screen=model_ct,
                status=True,
                is_deleted=False,
                effective_from__lte=timezone.now().date()
            )

            # Check if auth def applies to this record
            if company:
                auth_def_query = auth_def_query.filter(
                    models.Q(has_all_companies=True) | models.Q(companies=company)
                )
            else:
                auth_def_query = auth_def_query.filter(has_all_companies=True)

            if location:
                auth_def_query = auth_def_query.filter(
                    models.Q(has_all_locations=True) | models.Q(locations=location)
                )
            else:
                auth_def_query = auth_def_query.filter(has_all_locations=True)

            authorization_def_obj = auth_def_query.first()

            actor = get_user()
            if actor and getattr(actor, "is_anonymous", False):
                actor = None

            def get_creator_level():
                if not actor or not authorization_def_obj:
                    return None
                user_type = actor.__class__.__name__
                user_identifier = str(actor.id)
                group_ids = []
                try:
                    group_ids = list(actor.groups.only('id').values_list('id', flat=True))
                except Exception:
                    group_ids = []

                levels_qs = Authorization.objects.filter(
                    authorization_definition=authorization_def_obj,
                    screen=model_ct,
                ).filter(
                    Q(type=Authorization.USER, user_type=user_type, user_identifier=user_identifier) |
                    Q(type=Authorization.GROUP, group_id__in=group_ids)
                ).filter(Q(is_deleted=False) | Q(is_deleted__isnull=True))

                if not levels_qs.exists():
                    # Fallback for legacy rows missing authorization_definition
                    levels_qs = Authorization.objects.filter(
                        screen=model_ct,
                    ).filter(
                        Q(type=Authorization.USER, user_type=user_type, user_identifier=user_identifier) |
                        Q(type=Authorization.GROUP, group_id__in=group_ids)
                    ).filter(Q(is_deleted=False) | Q(is_deleted__isnull=True))

                levels = levels_qs.values_list('level', flat=True)
                return max(levels) if levels else None

            def apply_authorization():
                if not authorization_def_obj:
                    self.authorized_status = self.APPROVED
                    self.current_authorized_status = self.APPROVED
                    self.authorized_level = 0
                    self.current_authorized_level = 0
                    self.authorized_by_type = None
                    self.authorized_by_identifier = None
                    self.authorized_on = None
                    self.current_authorized_by_type = None
                    self.current_authorized_by_identifier = None
                    self.current_authorized_on = None
                    return

                if getattr(authorization_def_obj, "auto_approve_creator_level", False):
                    creator_level = get_creator_level()
                    if creator_level:
                        final_level = authorization_def_obj.level or creator_level
                        auto_level = min(creator_level, final_level)

                        self.authorized_level = auto_level
                        self.current_authorized_level = auto_level

                        if auto_level >= final_level:
                            self.authorized_status = self.APPROVED
                            self.current_authorized_status = self.APPROVED
                            self.authorized_by_type = actor.__class__.__name__
                            self.authorized_by_identifier = str(actor.id)
                            self.authorized_on = timezone.now()
                            self.current_authorized_by_type = actor.__class__.__name__
                            self.current_authorized_by_identifier = str(actor.id)
                            self.current_authorized_on = timezone.now()
                        else:
                            self.authorized_status = self.PENDING
                            self.current_authorized_status = self.PENDING
                            self.current_authorized_by_type = actor.__class__.__name__
                            self.current_authorized_by_identifier = str(actor.id)
                            self.current_authorized_on = timezone.now()
                            self.authorized_by_type = None
                            self.authorized_by_identifier = None
                            self.authorized_on = None

                        if auto_level > 0:
                            for level in range(1, auto_level + 1):
                                # Store for creation after save
                                auth_history_records.append({
                                    'screen': model_ct,
                                    'instance_id': str(self.id),  # Will have ID after save
                                    'authorized_level': level,
                                    'authorized_status': self.APPROVED,
                                    'description': "Auto-approved (creator level)",
                                    'authorized_by_type': actor.__class__.__name__,
                                    'authorized_by_identifier': str(actor.id)
                                })
                        return

                self.authorized_status = self.PENDING
                self.current_authorized_status = self.PENDING
                self.authorized_level = 0
                self.current_authorized_level = 0
                self.authorized_by_type = None
                self.authorized_by_identifier = None
                self.authorized_on = None
                self.current_authorized_by_type = None
                self.current_authorized_by_identifier = None
                self.current_authorized_on = None

            def apply_draft_authorization():
                # Draft documents stay in pending state.
                self.authorized_status = self.PENDING
                self.current_authorized_status = self.PENDING
                self.authorized_level = 0
                self.current_authorized_level = 0
                self.authorized_by_type = None
                self.authorized_by_identifier = None
                self.authorized_on = None
                self.current_authorized_by_type = None
                self.current_authorized_by_identifier = None
                self.current_authorized_on = None

            if self._state.adding:
                if status_value == 'DRAFT':
                    apply_draft_authorization()
                else:
                    apply_authorization()
            else:
                try:
                    model_cls = self.__class__.objects.model
                    old_instance = model_cls.objects.get(pk=self.pk)
                    old_status_value = str(getattr(old_instance, 'status', '') or '').upper()
                    moved_out_of_draft = old_status_value == 'DRAFT' and status_value not in ('', 'DRAFT')
                    fields_changed = False
                    for field in model_cls._meta.fields:
                        if field.name not in exclude_fields:
                            if getattr(old_instance, field.name) != getattr(self, field.name):
                                fields_changed = True
                                break
                    if status_value == 'DRAFT':
                        apply_draft_authorization()
                    elif force_authorization_recalc or fields_changed or moved_out_of_draft:
                        apply_authorization()
                except model_cls.DoesNotExist:
                    pass
        except ImportError:
            pass

        # Track if this is a new record before calling super().save()
        is_new_record = self._state.adding

        super().save(*args, **kwargs)

        # Create authorization history records after save (so record has an ID)
        if auth_history_records:
            for record_data in auth_history_records:
                # Update instance_id with actual saved ID
                record_data['instance_id'] = str(self.id)
                AuthorizationHistory.objects.create(**record_data)

        # If this is a new record and no history records were created yet, create an initial one
        if is_new_record and not auth_history_records:
            # Only create if one doesn't already exist
            ct_exists = AuthorizationHistory.objects.filter(
                screen=model_ct,
                instance_id=str(self.id)
            ).exists()

            if not ct_exists:
                AuthorizationHistory.objects.create(
                    screen=model_ct,
                    instance_id=str(self.id),
                    authorized_level=getattr(self, 'authorized_level', 0),
                    authorized_status=getattr(self, 'authorized_status', self.PENDING),
                    description="Document created",
                    authorized_by_type=self.created_by_type,
                    authorized_by_identifier=self.created_by_identifier
                )


class JwtToken(CoreModel):
    user_identifier = models.CharField(max_length=255, null=True, blank=True)
    user_type = models.CharField(max_length=15, null=True, blank=True)
    refresh_token = models.TextField(max_length=255)
    access_token = models.TextField(max_length=255)
    session_data = models.TextField(null=True, blank=True)
    access_expiring_on = models.DateTimeField(blank=True, null=True)
    refresh_expiring_on = models.DateTimeField(blank=True, null=True)

    CODE_PREFIX = 'JWT'

    def __str__(self):
        if self.user_identifier:
            return f"JWT Token for {self.user_identifier} ({self.user_type or 'Unknown'})"
        else:
            return "Unassigned JWT Token"

    # def __str__(self):
    #     if self.user:
    #         return f"{self.user.username}'s JWT Token"
    # #     elif self.organizer:
    # #         return f"{self.organizer.username}'s JWT Token"
    #     else:
    #         return "Unassigned JWT Token"


class Device(CoreModel):
    ANDROID = 1
    IOS = 2
    WEB = 3

    DEVICE_TYPE_CHOICES = (
        (ANDROID, 'Android'),
        (IOS, 'iOS'),
        (WEB, 'Web'),
    )

    name = models.CharField(max_length=100, null=True, blank=True)
    uuid = models.TextField(default='', blank=True, null=True)
    type = models.SmallIntegerField(choices=DEVICE_TYPE_CHOICES, blank=True, null=True, default=1,)
    fcmtoken = models.TextField(default='', blank=True, null=True)
    apntoken = models.TextField(default='', blank=True, null=True)
    accesstoken = models.TextField(default='', blank=True, null=True)
    # user = models.ForeignKey(settings.AUTH_USER_MODEL,
    # related_name='devices', on_delete=models.RESTRICT, null=True)  # User
    # Need to Remove
    user_identifier = models.CharField(max_length=255, null=True, blank=True)
    user_type = models.CharField(max_length=15, null=True, blank=True)
    session = models.TextField(default='', blank=True, null=True)
    socket = models.CharField(max_length=30, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    CODE_PREFIX = 'DEV'

    def __str__(self): return str(self.code)


class DeviceLog(CoreModel):
    # user = models.ForeignKey(
    #     settings.AUTH_USER_MODEL,
    #     related_name='devicelogins',
    #     on_delete=models.RESTRICT,
    #     null=True,
    # )
    user_identifier = models.CharField(max_length=255, null=True, blank=True)
    user_type = models.CharField(max_length=15, null=True, blank=True)
    device = models.ForeignKey(Device, related_name='devicelogs', on_delete=models.RESTRICT, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    login = models.DateTimeField(auto_now_add=True, blank=True)
    logout = models.DateTimeField(null=True, blank=True)

    CODE_PREFIX = 'DLOG'

    def __str__(self): return str(self.code)

    def save(self, *args, **kwargs):
        super(DeviceLog, self).save(*args, **kwargs)


class UserPreferences(BaseModel):
    # user = models.ForeignKey(User, on_delete=models.RESTRICT,related_name='user_preferences',blank=True, null=True)
    user_identifier = models.CharField(max_length=255, null=True, blank=True)
    user_type = models.CharField(max_length=15, null=True, blank=True)
    preferences = models.TextField(default='', blank=True, null=True)


class CodeUserManager(CoreUserManager, CoreManager):
    pass


class CodeUserModel(CoreUser, CodeModel):

    objects = CodeUserManager()

    class Meta:
        abstract = True


class UserType(models.Model):
    user_types = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    screen = models.ForeignKey(ContentType, related_name='usertypes', on_delete=models.CASCADE, null=True)
    is_deleted = models.BooleanField(blank=True, default=False, null=True)
