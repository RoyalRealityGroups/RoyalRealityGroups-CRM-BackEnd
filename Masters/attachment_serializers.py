from rest_framework import serializers
from .attachment_models import ChannelPartnerAttachment


class ChannelPartnerAttachmentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ChannelPartnerAttachment
        fields = ('id', 'attachment_type', 'file', 'file_url', 'original_filename', 'description', 'created_on')
        read_only_fields = ('id', 'created_on')
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None
