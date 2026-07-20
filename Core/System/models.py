from django.db import models
from django.conf import settings

from Core.Core.utils.utils import CompressImage
# from Common.middleware import ErrorMiddleware

from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill

from django.http import FileResponse
from django.shortcuts import get_object_or_404

 
from django.db import models
from django.contrib.auth.models import  Group

from django.contrib.contenttypes.models import ContentType

from Core.Users.models import BaseModel, CodeModel, CoreModel

# Import filter models
from .filter_models import SavedFilter, FilterPreset


class Menu(CodeModel):

    name = models.CharField(max_length=100, unique=True)
    
    CODE_PREFIX = 'MENU'

    __str__ = lambda self: str(self.name)



class Submenu(CodeModel):
    
    name = models.CharField(max_length=100, unique=True)
    sequence = models.IntegerField(default=100,null=True, blank=True)
    icon = models.CharField(max_length=30,null=True, blank=True)
    click = models.CharField(max_length=50, null=True, blank=True)
    menu = models.ForeignKey('System.Menu', related_name='submenus', on_delete=models.RESTRICT, null=True)
    submenu = models.ForeignKey('System.Submenu', related_name='submenus', on_delete=models.RESTRICT, null=True, blank=True)
    
    CODE_PREFIX = 'SBM'

    __str__ = lambda self: str(self.name)


    


        
class Menuitem(CodeModel):
    
    name = models.CharField(max_length=100,null=True, blank=True)
    icon = models.CharField(max_length=30,null=True, blank=True)
    link = models.CharField(max_length=50,null=True, blank=True)
    sequence = models.IntegerField(default=100,null=True, blank=True)
    click = models.CharField(max_length=50, null=True, blank=True)
    menu = models.ForeignKey('System.Menu', related_name='menuitems', on_delete=models.RESTRICT, null=True)
    submenu = models.ForeignKey('System.Submenu', related_name='menuitems', on_delete=models.RESTRICT, null=True, blank=True)
    permission = models.ForeignKey('auth.Permission', related_name='menuitems', on_delete=models.RESTRICT, null=True)
    description = models.TextField(default='', blank=True, null=True)
    
    CODE_PREFIX = 'MIM'

    __str__ = lambda self: str(self.name)



        
NOTE_TYPES_CHOICES = (
    ( 1 , "Message"),
)        
SEEN_CHOICES = (
    ( 0 , "Unseen"),
    ( 1 , "Seen"),
)

MESSAGE_PRIORITY_CHOICES = (
    ( 1 , "Low"),
    ( 2 , "Medium"),
    ( 3 , "High"),
)

NOTIFICATION_TYPE_CHOICES = (
    ( 1 , "Notification"),
    ( 2 , "Remainder"),
    ( 3 , "Alert"),
)

class Notification(BaseModel):
    
    subject = models.CharField(max_length=200,null=True, blank=True)
    body = models.TextField(null=True, blank=True)
    type = models.CharField(max_length=25,null=True, blank=True)
    ref = models.CharField(max_length=200,null=True, blank=True)
    message_priority = models.SmallIntegerField(default=1, choices= MESSAGE_PRIORITY_CHOICES, null=True, blank=True)
    notification_type = models.SmallIntegerField(default=1, choices= NOTIFICATION_TYPE_CHOICES, null=True, blank=True)
    web_navigation_url = models.CharField(max_length=255, null=True, blank=True)
    mobile_navigation_url = models.CharField(max_length=255, null=True, blank=True)
    

    __str__ = lambda self: str(self.id)




class NotificationUsers(BaseModel):

    user_identifier = models.CharField(max_length=255, null=True, blank=True)
    user_type = models.CharField(max_length=15, null=True, blank=True)
    notification = models.ForeignKey(Notification, related_name='notificationusers', on_delete=models.RESTRICT, null=True)
    seen = models.SmallIntegerField(default=0, choices= SEEN_CHOICES, null=True, blank=True)
    seen_time = models.DateTimeField(null=True, blank=True)


        
class Backup(CodeModel):

    name = models.CharField(max_length=100, unique=True)
    
    CODE_PREFIX = 'BAKUP'

    __str__ = lambda self: str(self.name)

        


class Restore(CodeModel):
    
    name = models.CharField(max_length=100, unique=True)
    
    CODE_PREFIX = 'RESTR'


    __str__ = lambda self: str(self.name)

        
class Download(BaseModel):

    __str__ = lambda self: str(self.id)


    def get(self, request, pk):
        instance = get_object_or_404(self.model, pk=pk)
        file_path = instance.file_field.path  # Assuming you have a FileField in your model

        # You can customize the response headers if needed
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Disposition'] = f'attachment; filename="{instance.file_field.name}"'
        return response


class Attachment(BaseModel):

    file = models.FileField(upload_to="attachments/", null=True, blank=True)
    file_thumbnail = ImageSpecField(source='file', processors=[ResizeToFill(150, 150)], format='JPEG', options={'quality': 60})
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file =  CompressImage(self.file)
        super(Attachment, self).save(*args, **kwargs)


    def __str__(self):
        return self.file.path if self.file else ""



class Formula(BaseModel):

    name = models.CharField(max_length=100, null=True, blank=True, )
    formula = models.CharField(max_length=200, null=True, blank=True,)
    

    __str__ = lambda self: str(self.name)

        


class FormulaVariables(CodeModel):

    name = models.CharField(max_length=30, default=0, null=True, blank=True)
    description = models.TextField(default='', blank=True, null=True)
    active = models.BooleanField(default=True, blank=True, )
    formula = models.ForeignKey(Formula, related_name='formulavariables', on_delete=models.RESTRICT, null=True, blank=True)

    CODE_PREFIX = 'FRMV'

    
    __str__ = lambda self: str(self.name)



class FormulaUpdate(BaseModel):

    formula = models.ForeignKey(Formula, related_name='formula_updates', on_delete=models.RESTRICT, null=True, blank=True)
    formula_txt = models.CharField(max_length=200, null=True, blank=True,)
    

    __str__ = lambda self: str(self.formula_txt)



ACTION_TYPES_CHOICES = (
    ( 1 , "Create"),
    ( 2 , "Update"),
    ( 3 , "Delete"),
)

class ActivityLog(BaseModel):
    
    user_type = models.CharField(max_length=15, null=True, blank=True)
    user_identifier = models.CharField(max_length=255, null=True, blank=True)
    type = models.SmallIntegerField(default=1, choices= ACTION_TYPES_CHOICES, blank=True, null=True, )
    screen = models.ForeignKey(ContentType, related_name='activity_logs', on_delete=models.RESTRICT, null=True)
    screen_name = models.CharField(max_length=100, null=True, blank=True, )
    instance_id = models.CharField(max_length=50, null=True, blank=True)
    instance_code = models.CharField(max_length=50, null=True, blank=True, )
    data = models.JSONField( null=True, blank=True, )

    __str__ = lambda self: str(self.screen_name)





class Error(BaseModel):

    errorcode = models.CharField(max_length=50, null=True, blank=True, )
    requestbody = models.TextField( null=True, blank=True, )
    responsecontent = models.TextField( null=True, blank=True, ) 
    error_url = models.URLField(max_length=200,  null=True, blank=True,)


    __str__ = lambda self: str(self.errorcode)



class Setting(BaseModel):
    preferences_code = models.CharField(max_length=50, null=True, blank=True, )
    preferences = models.TextField(default='', blank=True, null=True)
    
    class Meta:
        permissions = (
            ("can_view_current_logged_users", "Can View Current Logged Users"),
            ("can_view_audit_logs", "Can View Audit Logs"),
            ("view_import", "Can View Import"),
            ("view_export", "Can View Export "),
            ("view_report", "Can View Reports "),
            ("view_masters", "Can View Masters"),
            
        )


VERIFICATION_TYPES_CHOICES = (
    ( 1 , "SMS"),
    ( 2 , "Email"),
)

class TemporaryVerification(BaseModel):
    type = models.SmallIntegerField(default=1, choices= VERIFICATION_TYPES_CHOICES, blank=True, null=True, )
    mobile = models.CharField(max_length=15, db_index=True, blank=True)
    email = models.EmailField(max_length=255, db_index=True, blank=True, null=True)
    otp = models.CharField(max_length=6, blank=True, null=True)
    is_phone_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)

    __str__ = lambda self: str(self.mobile)



ACTION_TYPES_CHOICES = (
    ( 1 , "Create"),
    ( 2 , "Update"),
    ( 3 , "Delete"),
)
 

    
class RecentActivity(BaseModel):
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='recentactivities', on_delete=models.RESTRICT, null=True)
    user_type = models.CharField(max_length=100, null=True, blank=True, db_index=True,)
    user_identifier = models.CharField(max_length=255, null=True, blank=True, db_index=True,)
    menuitem = models.ForeignKey('System.Menuitem', related_name='recentactivities', on_delete=models.RESTRICT, null=True)
    
    # __str__ = lambda self: str(self.recentactivity)
    def __str__(self):
     return f"{self.menuitem}"


class Template(CoreModel):
    name = models.CharField(max_length=100, null=True, blank=True,unique=True )
    message = models.TextField(default='', blank=True, null=True)#help_text="Message template for the alert, use {instance.field_name} for dynamic values"
    # msg_variables = models.TextField(default='', blank=True, null=True) #help_text="map of the variables in the template to the model fields, e.g., {'name': 'name', 'age': 'age'}"
    screen = models.ForeignKey(ContentType, related_name='templates', on_delete=models.RESTRICT, null=True, blank=True)
    is_active = models.BooleanField(default=True, blank=True, )
    
    CODE_PREFIX = 'TEMP'

    def __str__(self):
        return self.name

 
class AlertConfig(CoreModel):

    CREATE = 1
    UPDATE = 2
    DELETE = 3
    AUTH_APPROVED= 4
    AUTH_REJECTED = 5
    ASSIGNIE_ADD = 6
    ASSIGNIE_REMOVED = 7

    EVENT_CHOICES = [ # temprary to build the events afgter appiulcation devlop we customised events can develop
        (CREATE, 'Create'),
        (UPDATE, 'Update'),
        (DELETE,'Delete'),
        (AUTH_APPROVED,'Approved'),
        (AUTH_REJECTED,'Rejected'),
        (ASSIGNIE_ADD,'AddAssignee'),
        (ASSIGNIE_REMOVED,'RemoveAssignee'),
    ]

    CREATEDBY = 1
    GROUP = 2
    USER = 3
    VARIABLE = 4
    VALUE = 5

    SENDER_TYPE_CHOICES = [
        (CREATEDBY, 'CreatedBy'),
        (GROUP, 'Group'),
        (USER, 'User'),
        (VARIABLE, 'Variable'),
        (VALUE, 'Value'),
    ]

    SMS = 1
    EMAIL = 2
    NOTIFICATION = 3

    TYPE_CHOICES = [
        (SMS, 'SMS'),
        (EMAIL, 'Email'),
        (NOTIFICATION, 'Notification'),
    ]
    
    MINUTES = 1
    HOURS = 2
    DAYS = 3
    WEEKS = 4
    
    REPEAT_CHOICES = [
       (MINUTES, 'Minutes'),
        (HOURS, 'Hours'),
        (DAYS, 'Days'),
        (WEEKS, 'Weeks'),
    ]
    
    LOW = 1
    MEDIUM =2
    HIGH = 3
 
    MESSAGE_PRIORITY_CHOICES = [
        ( LOW , "Low"),
        ( MEDIUM , "Medium"),
        ( HIGH , "High"),
    ]
    
    NOTIFICATION = 1
    REMAINDER = 2
    ALERT = 3
 
    NOTIFICATION_TYPE_CHOICES = [
        ( NOTIFICATION , "Notification"),
        ( REMAINDER , "Remainder"),
        ( ALERT , "Alert"),
    ]

    id = models.AutoField(primary_key=True, auto_created=True)
    screen = models.ForeignKey(ContentType, related_name='alertconfigs', on_delete=models.RESTRICT, null=True, blank=True)
    event_type = models.SmallIntegerField(choices=EVENT_CHOICES,null=True, blank=True,)
    sender_type = models.SmallIntegerField(choices=SENDER_TYPE_CHOICES, blank=True, null=True) # like user
    type = models.SmallIntegerField( choices=TYPE_CHOICES,null=True, blank=True)
    gateway = models.CharField(max_length=255,null=True, blank=True)
    send_to_groups = models.ManyToManyField(Group, blank=True, related_name='alertconfigs')
    # send_to_users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, null=True, related_name='alertconfigs',)
    value = models.CharField(max_length=255,null=True, blank=True) #email/phone
    variable = models.CharField(max_length=255,null=True, blank=True) #model variable
    attachment_variable = models.CharField(max_length=255, null=True, blank=True) #model variable for attachment
    template = models.ForeignKey(Template, related_name='alertconfigs', on_delete=models.RESTRICT, null=True, blank=True)
    subject_template = models.ForeignKey(Template, related_name='alertconfigs_sub', on_delete=models.RESTRICT, null=True, blank=True)
    message_priority = models.SmallIntegerField(default=1, choices= MESSAGE_PRIORITY_CHOICES, null=True, blank=True)
    notification_type = models.SmallIntegerField(default=1, choices= NOTIFICATION_TYPE_CHOICES, null=True, blank=True)
    web_navigation_url = models.ForeignKey(Template, related_name='alertconfigs_web_url', on_delete=models.RESTRICT, null=True, blank=True) #model variable for web navigation URL
    mobile_navigation_url = models.ForeignKey(Template, related_name='alertconfigs_mob_url', on_delete=models.RESTRICT, null=True, blank=True) #model variable for mobile navigation URL
    repeat_interval = models.IntegerField(null=True, blank=True, ) #help_text="Repeat every X units"
    frequency = models.SmallIntegerField(choices=REPEAT_CHOICES, blank=True, null=True)
    start_time = models.DateTimeField(null=True, blank=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    send_doc = models.BooleanField(default=False) # whether to send pdf against the model instance and screen
    is_scheduled = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_attachment = models.BooleanField(default=False) # whether to send document present in the model

    CODE_PREFIX = 'ALC'

    def __str__(self):
        return f"{self.screen} - {self.event_type}"

class AlertConfigUsers(CoreModel):
    alert = models.ForeignKey(AlertConfig, related_name='alert_users', on_delete=models.RESTRICT, null=True, blank=True)
    user_type = models.CharField(max_length=100, null=True, blank=True, db_index=True,)
    user_identifier = models.CharField(max_length=255, null=True, blank=True, db_index=True,)
    
    CODE_PREFIX = 'ALCU'
    
    def __str__(self):
        return f"{self.id}"

class Announcements(CoreModel):
    
    subject = models.CharField(max_length=200,null=True, blank=True)
    body = models.TextField(null=True, blank=True)

    CODE_PREFIX = 'ANM'

    def __str__(self):
        return self.subject or "No Subject"


class TaskScheduler(CoreModel):
    
    MINUTES = 1
    HOURS = 2
    DAILY = 3
    WEEKLY = 4
    MONTHLY = 5
    YEARLY = 6
    CUSTOM = 7
    ONETIME = 8

    FREQUENCY_CHOICES = [
        (MINUTES, 'Minutes'),
        (HOURS, 'Hours'),
        (DAILY, 'Daily'),
        (WEEKLY, 'Weekly'),
        (MONTHLY, 'Monthly'),
        (YEARLY, 'Yearly'),
        (CUSTOM, 'Custom'),
        (ONETIME, 'One-time'),
    ]

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    function_path = models.CharField(max_length=500,blank=True, null=True)  # e.g. "myapp.tasks.cleanup_task" if command start with(command:)
    
    frequency = models.SmallIntegerField(choices=FREQUENCY_CHOICES, default=ONETIME)
    repeat_interval = models.IntegerField(default=0,blank=True, null=True)
    custom_interval = models.DurationField(blank=True, null=True)  # If CUSTOM
    start_time = models.DateTimeField(blank=True, null=True)
    next_run = models.DateTimeField(blank=True, null=True)
    retry_count = models.IntegerField(default=0)
    retry_interval = models.DurationField(blank=True, null=True, help_text="Retry interval (timedelta)")
    max_execution_time = models.IntegerField(default=300,blank=True, null=True)  # in seconds, like "kill time"
    allow_parallel = models.BooleanField(default=False)  # whether multiple runs allowed in parallel
    last_run = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    CODE_PREFIX = "TSH"

    def __str__(self):
        return self.name

class TaskExecutionLog(BaseModel):
    task = models.ForeignKey(TaskScheduler, related_name='execution_logs', on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=[('success', 'Success'), ('failed', 'Failed'), ('killed', 'Killed')], default='success')
    detail = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.task.name} executed at {self.start_time}"


# ============================================================================
# SMTP CONFIGURATION
# ============================================================================

class SMTPConfig(BaseModel):
    """
    Stores SMTP credentials for sending emails.
    Only one active configuration is used at a time.
    """
    name = models.CharField(max_length=100, help_text='Configuration name (e.g. "Gmail", "SendGrid")')
    host = models.CharField(max_length=255, help_text='SMTP server host (e.g. smtp.gmail.com)')
    port = models.PositiveIntegerField(default=587, help_text='SMTP port (587 for TLS, 465 for SSL)')
    username = models.CharField(max_length=255, help_text='SMTP username / email')
    password = models.CharField(max_length=255, help_text='SMTP password / app password')
    use_tls = models.BooleanField(default=True, help_text='Use TLS encryption')
    use_ssl = models.BooleanField(default=False, help_text='Use SSL encryption')
    from_email = models.EmailField(help_text='Default "From" email address')
    from_name = models.CharField(max_length=100, blank=True, null=True, help_text='Display name for sender')
    is_active = models.BooleanField(default=True, help_text='Active configuration (only one should be active)')

    class Meta:
        verbose_name = 'SMTP Configuration'
        verbose_name_plural = 'SMTP Configurations'
        ordering = ['-is_active', '-created_on']

    def __str__(self):
        return f"{self.name} ({self.host}:{self.port}) {'✓' if self.is_active else '✗'}"

    def save(self, *args, **kwargs):
        # Ensure only one active config
        if self.is_active:
            SMTPConfig.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)
