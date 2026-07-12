from Users.models import User
from Users.serializers import UserMiniSerializer
from .models import *
from rest_framework import serializers



class SyncLogSerializers(serializers.ModelSerializer):

    class Meta:
        model = SyncLog
        fields = ['id','log','created_on']

        
class SyncTriggerSerializers(serializers.ModelSerializer):

    sync_type = serializers.ChoiceField(choices=SyncTrigger.SYNC_TYPE_STATUS_CHOICES, )
    sync_type_name = serializers.SerializerMethodField()

    sync_from = serializers.ChoiceField(choices=SyncTrigger.SYNC_TYPE_STATUS_CHOICES, )
    sync_from_name = serializers.SerializerMethodField()

    sync_log_items = SyncLogSerializers(many=True)

    def get_sync_type_name(self, obj):
        return obj.get_sync_type_display()
    
    def get_sync_from_name(self, obj):
        return obj.get_sync_from_display()

    class Meta:
        model = SyncTrigger
        fields = ['id','sync_type','sync_type_name','sync_from','sync_from_name','sync_log_items','created_on']

    
class SyncTriggerListSerializers(serializers.ModelSerializer):

    sync_type = serializers.ChoiceField(choices=SyncTrigger.SYNC_TYPE_STATUS_CHOICES, )
    sync_type_name = serializers.SerializerMethodField()

    sync_from = serializers.ChoiceField(choices=SyncTrigger.SYNC_TYPE_STATUS_CHOICES, )
    sync_from_name = serializers.SerializerMethodField()

    def get_sync_type_name(self, obj):
        return obj.get_sync_type_display()
    
    def get_sync_from_name(self, obj):
        return obj.get_sync_from_display()

    class Meta:
        model = SyncTrigger
        fields = ['id','sync_type','sync_type_name','sync_from','sync_from_name','created_on']
