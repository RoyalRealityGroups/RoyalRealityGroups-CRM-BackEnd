from rest_framework import serializers
from .attachment_models import SalesOrderAttachment


class SalesOrderAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for Sales Order Attachments"""
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = SalesOrderAttachment
        fields = (
            'id', 
            'sales_order', 
            'file', 
            'file_url',
            'original_filename', 
            'description',
            'created_on', 
            'modified_on'
        )
        read_only_fields = ('id', 'file_url', 'created_on', 'modified_on')
    
    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and hasattr(obj.file, 'url'):
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
