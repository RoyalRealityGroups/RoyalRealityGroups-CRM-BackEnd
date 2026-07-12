# from rest_framework.views import APIView
# from Masters.models import *
# from rest_framework.response import Response

# from thirdparty.serializers import SyncLogSerializers, SyncTriggerListSerializers, SyncTriggerSerializers
# from thirdparty.services import is_focus_data_syncing, start_focus_data_sync
# from .FocusAPI import *
# from rest_framework import status

# from rest_framework import generics,permissions


# from rest_framework import filters, status
# from rest_framework.response import Response
# from django_filters.rest_framework import DjangoFilterBackend, FilterSet



# class FocusDataSync(generics.GenericAPIView):
#     permission_classes = [permissions.IsAuthenticated]
 
#     def get(self, request, *args, **kwargs):

#         start_focus_data_sync()
       
#         return Response({'message':  'Focus Data Sync Started.' }, status=status.HTTP_200_OK)
    



# class FocusDataSyncStatus(APIView):
#     permission_classes = [permissions.IsAuthenticated]

 
#     def get(self,request):
#         is_focus_data_sync =  is_focus_data_syncing()
#         msg = 'Focus Data Sync Completed' if not is_focus_data_sync else 'Focus Data Sync Running'
 
#         return  Response({'message': msg, 'status': is_focus_data_sync}, status=status.HTTP_200_OK)
 



# class SyncTriggerFilter(FilterSet):

#     class Meta:
#         model = SyncTrigger
#         fields = ['sync_type', 'sync_from']


# class SyncTriggerList(generics.ListAPIView):
#     permission_classes = [permissions.IsAuthenticated]
#     serializer_class = SyncTriggerListSerializers
#     model = serializer_class.Meta.model
#     queryset = model.objects.filter().order_by('-created_on')
#     filter_backends = [filters.SearchFilter, DjangoFilterBackend,]
#     filterset_class = SyncTriggerFilter
#     search_fields = []


# class SyncTriggerDetails(generics.RetrieveDestroyAPIView):
#     permission_classes = [permissions.IsAuthenticated]
#     serializer_class = SyncTriggerSerializers
#     model = serializer_class.Meta.model
#     queryset = model.objects.filter().order_by('-created_on')
#     filter_backends = [filters.SearchFilter, DjangoFilterBackend,]
#     filterset_class = SyncTriggerFilter
#     search_fields = []


# class SyncLogFilter(FilterSet):

#     class Meta:
#         model = SyncLog
#         fields = ['sync_trigger']


# class SyncLogList(generics.ListAPIView):
#     permission_classes = [permissions.IsAuthenticated]
#     serializer_class = SyncLogSerializers
#     model = serializer_class.Meta.model
#     queryset = model.objects.filter().order_by('-created_on')
#     filter_backends = [filters.SearchFilter, DjangoFilterBackend,]
#     filterset_class = SyncLogFilter
#     search_fields = []
