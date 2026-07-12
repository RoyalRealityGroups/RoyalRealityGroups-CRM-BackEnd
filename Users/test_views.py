from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.contrib.auth import get_user_model
from .serializers import UserSerializer

User = get_user_model()

class TestUserSerializerView(APIView):
    """Test endpoint to debug user serializer output"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            serializer = UserSerializer(user, context={'request': request})
            return Response({
                'user_data': serializer.data,
                'retailer_field': serializer.data.get('retailer'),
                'retailer_name_field': serializer.data.get('retailer_name'),
                'channel_partner_type': serializer.data.get('channel_partner_type'),
                'raw_retailer_id': str(user.retailer.id) if user.retailer else None,
                'raw_retailer_name': user.retailer.name if user.retailer else None,
            })
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)