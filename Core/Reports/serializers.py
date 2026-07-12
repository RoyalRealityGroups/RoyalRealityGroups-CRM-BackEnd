import os.path
from Core.Reports.models import FILEFORMAT_CHOICES, FREQUENCY_CHOICES, PdfTemplate, ReportRequest, ScheduledEmail

from rest_framework import serializers

from Core.Users.serializers import ContentType2Serializer, CoreUserMiniSerializer


from .import_export_models import *

from django.contrib.contenttypes.models import ContentType


class GenericImportExportSerializer(serializers.Serializer):
    model_name = serializers.CharField(required= True, allow_blank=False )

    class Meta:
        fields = ('model_name', )

class GenericImportSerializer(serializers.Serializer):
    import_file = serializers.FileField(required= True, )
    input_format = serializers.IntegerField(required= True, min_value=0, max_value=5 )

    class Meta:
        fields = ('import_file', 'input_format', )

class GenericConfirmImportSerializer(serializers.Serializer):
    import_file_name = serializers.CharField(required= True,)
    original_file_name = serializers.CharField(required= True,)
    input_format = serializers.IntegerField(required= True, min_value=0, max_value=5 )
    
    def validate_import_file_name(self, value):
        if not value:
            raise serializers.ValidationError("import_file_name required")
        value = os.path.basename(value)
        return value

    class Meta:
        fields = ('import_file_name', 'original_file_name', 'input_format', )



class GenericExportSerializer(serializers.Serializer):
    file_format = serializers.IntegerField(required= True, min_value=0, max_value=5 )
    response_type = serializers.ChoiceField(required=False, choices=((1, 'Generate Report'), (2, 'Email')))
    email = serializers.CharField(required= False, )

    class Meta:
        fields = ('file_format', 'response_type', 'email')


class ScheduledEmailSerializer(serializers.ModelSerializer):
    fileformat = serializers.ChoiceField(choices=FILEFORMAT_CHOICES, required=False, )
    fileformat_name = serializers.SerializerMethodField()
    frequency = serializers.ChoiceField(choices=FREQUENCY_CHOICES, required=False, )
    frequency_name = serializers.SerializerMethodField()
    # created_by = CoreUserMiniSerializer(many=False, read_only=True)

    def get_fileformat_name(self, obj):
        return obj.get_fileformat_display()

    def get_frequency_name(self, obj):
        return obj.get_frequency_display()


    class Meta:
        model = ScheduledEmail
        read_only_fields = ['code', 'createdon', 'state']
        fields = ('id', 'code', 'startdate', 'time', 'frequency', 'frequency_name', 'email', 'reportname',
                  'fileformat', 'fileformat_name', 'filters', 'last_run', 'repeatdays', 
                  'created_on', 'modified_on')



    def validate(self, attrs):
        startdate = attrs.get('startdate', '')
        time=attrs.get('time', '')
        frequency=attrs.get('frequency', '')
        fileformat=attrs.get('fileformat', '')
        reportname=attrs.get('reportname', '')
        repeatdays=attrs.get('repeatdays', '')

        if startdate == None:
            raise serializers.ValidationError("startdate is required")
        if time == None:
            raise serializers.ValidationError("time is required")
        if frequency == None:
            raise serializers.ValidationError("frequency is required")
        if fileformat == None:
            raise serializers.ValidationError("fileformat is required")
        if reportname == None:
            raise serializers.ValidationError("reportname is required")

        return super().validate(attrs)
    
    def create(self, validated_data):
        obj = super().create(validated_data)
        return obj
    

class PdfTemplateListCreateSerializer(serializers.ModelSerializer):

    screen = ContentType2Serializer(many=False, read_only=True)
    screen_id = serializers.PrimaryKeyRelatedField(
        write_only=True, required=False, source='screen',
        queryset=ContentType.objects.filter() #is_superuser=False
    )

    class Meta:
        model = PdfTemplate
        fields = ('id', 'name', 'screen', 'screen_id', 'screen_name', 'template_data', 'is_active')


    
class PdfTemplateSerializer(serializers.ModelSerializer):

    class Meta:
        model = PdfTemplate
        fields = ('id', 'name', 'screen', 'screen_name', 'is_active')

    
class PdfTemplateDataSerializer(serializers.ModelSerializer):        

    class Meta:
        model = PdfTemplate
        fields = ('id', 'name', 'screen', 'screen_name', 'template_data', 'is_active')

    # def to_representation(self, instance):
    #     representation = super().to_representation(instance)
    #     try:
    #         # raw_data = json.loads(instance.data)
    #         # formatted_string = format_variables(json.dumps(raw_data), context={})
    #         representation['template_data'] = json.loads(instance.template_data)
    #     except Exception as e:
    #         representation['template_data'] = {}
    #     return representation
    
class ReportRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportRequest
        read_only_fields = ['id', 'code', 'status', 'file_name', 'content_type']
        fields = [
            'id','code','report_id', 'unique_id','temp_file_path','file','file_name', 'content_type','status',
        ]