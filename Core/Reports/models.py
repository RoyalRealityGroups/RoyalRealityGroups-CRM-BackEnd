from django.contrib.contenttypes.models import ContentType
from django.db import models
from Core.Reports.services import extract_variables_from_template
from Core.Users.models import BaseModel, CodeModel, CoreModel

# Create your models here.


FREQUENCY_CHOICES = (
    (1, 'Day'),
    (2, 'Week'),
    (3, 'Month'),
    (4, 'Year'),
    (5, 'Custom'),
)


FILEFORMAT_CHOICES = (
    (0, 'CSV'),
    (1, 'XLS'),
    (2, 'XLSX'),
    (3, 'TSV'),
    (4, 'ODS'),
    (5, 'JSON'),
    (6, 'YML'),
    (7, 'HTML'),
)


class ScheduledEmail(CodeModel):

    startdate = models.DateField(null=True, blank=True)
    time = models.DateTimeField(null=True, blank=True)
    frequency = models.SmallIntegerField(choices=FREQUENCY_CHOICES, null=True, blank=False, default=1, )
    email = models.EmailField(max_length=255, db_index=True, blank=True, null=True)
    reportname = models.CharField( max_length=150, blank=True)
    fileformat = models.SmallIntegerField(choices=FILEFORMAT_CHOICES, null=True, blank=False, default=0, )
    filters = models.TextField(max_length=300, null = True, blank= True)
    last_run = models.DateTimeField(null=True, blank=True)
    repeatdays = models.IntegerField(null=True, blank=False, default=1, )

    
    CODE_PREFIX = 'SCE'


class ReportRequest(CoreModel):
   
    unique_id=models.CharField(blank=True, max_length=30, null=True)
    report_id=models.CharField(blank=True, max_length=30, null=True)
    temp_file_path = models.CharField(blank=True, max_length=500, null=True)
    file_name = models.CharField(blank=True, max_length=500, null=True)
    content_type = models.CharField(blank=True, max_length=500, null=True)
    file = models.FileField(upload_to="reports/",  null=True, blank=True)
    status = models.SmallIntegerField(blank=True, choices=[(1, 'Pending'), (2, 'Complete')], default=1, null=True)

    CODE_PREFIX = 'RR'
    
    __str__ = lambda self: str(self.code)



class ImportRequest(CodeModel):

    unique_id= models.CharField(blank=True, max_length=30, null=True)
    content= models.TextField(blank=True, null=True)
    status_code = models.SmallIntegerField(blank=True, null=True)
    status = models.SmallIntegerField(blank=True, choices=[(1, 'Pending'), (2, 'Complete'), (3, 'Failed')], default=1, null=True)
    
    # Additional fields for better history tracking
    screen_name = models.CharField(max_length=100, blank=True, null=True, help_text='Name of the model/screen being imported')
    file_name = models.CharField(max_length=255, blank=True, null=True, help_text='Original uploaded file name')
    total_records = models.IntegerField(blank=True, null=True, default=0, help_text='Total records in file')
    new_records = models.IntegerField(blank=True, null=True, default=0, help_text='New records created')
    updated_records = models.IntegerField(blank=True, null=True, default=0, help_text='Existing records updated')
    error_records = models.IntegerField(blank=True, null=True, default=0, help_text='Records with errors')
    is_dryrun = models.BooleanField(default=False, blank=True, null=True, help_text='True if this was a validation/preview only')

    CODE_PREFIX = 'IR'
    
    __str__ = lambda self: str(self.code)


class PdfTemplate(BaseModel):
    name = models.CharField(blank=True, max_length=100, null=True)
    screen = models.ForeignKey(ContentType, related_name='pdf_templates', on_delete=models.RESTRICT, null=True)
    screen_name = models.CharField(max_length=100, null=True, blank=True, )
    template_data = models.JSONField(null = True, blank= True)
    variables_data = models.JSONField( null=True, blank=True, )
    is_active = models.BooleanField(default=False, blank=True, null=True)

    __str__ = lambda self: str(self.screen_name)


    def save(self, *args, **kwargs):
        if self.template_data:
            self.variables_data = extract_variables_from_template(self.template_data)
        super().save(*args, **kwargs)