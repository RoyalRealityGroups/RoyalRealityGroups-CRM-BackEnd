from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.views import APIView
from django.contrib.contenttypes.models import ContentType
from .attachment_models import ChannelPartnerAttachment
from .attachment_serializers import ChannelPartnerAttachmentSerializer


class ChannelPartnerAttachmentMixin:
    """Mixin to handle attachments for channel partners"""
    
    def handle_attachments(self, instance, request):
        """Process and save attachments from request"""
        # Only process if FILES are present (multipart/form-data)
        if not request.FILES:
            return
            
        attachment_types = ['aadhar', 'pan', 'agreement', 'shop_picture', 'cancelled_cheque', 'owner_picture']
        
        for att_type in attachment_types:
            file = request.FILES.get(att_type)
            if file:
                # Delete existing attachment of same type
                ChannelPartnerAttachment.objects.filter(
                    content_type=ContentType.objects.get_for_model(instance),
                    object_id=str(instance.id),
                    attachment_type=att_type.upper()
                ).delete()
                
                # Create new attachment
                ChannelPartnerAttachment.objects.create(
                    content_object=instance,
                    attachment_type=att_type.upper(),
                    file=file,
                    original_filename=file.name
                )
        
        # Handle multiple "other" attachments
        other_files = request.FILES.getlist('other') if hasattr(request.FILES, 'getlist') else []
        other_descriptions = request.data.getlist('other_descriptions', []) if hasattr(request.data, 'getlist') else []
        
        for idx, file in enumerate(other_files):
            description = other_descriptions[idx] if idx < len(other_descriptions) else ''
            ChannelPartnerAttachment.objects.create(
                content_object=instance,
                attachment_type='OTHER',
                file=file,
                original_filename=file.name,
                description=description
            )


class AttachmentListView(APIView):
    """Base view for listing attachments"""
    model = None
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, pk):
        try:
            instance = self.model.objects.get(pk=pk)
            content_type = ContentType.objects.get_for_model(instance)
            attachments = ChannelPartnerAttachment.objects.filter(
                content_type=content_type,
                object_id=str(instance.id),
                is_deleted=False
            )
            serializer = ChannelPartnerAttachmentSerializer(attachments, many=True, context={'request': request})
            return Response(serializer.data)
        except self.model.DoesNotExist:
            return Response({'error': 'Object not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AttachmentUploadView(APIView):
    """Base view for uploading attachments"""
    model = None
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        try:
            instance = self.model.objects.get(pk=pk)
            file = request.FILES.get('file')
            attachment_type = request.data.get('attachment_type')
            description = request.data.get('description', '')
            
            if not file:
                return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
            
            if not attachment_type:
                return Response({'error': 'Attachment type is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            # For non-OTHER types, delete existing attachment
            if attachment_type != 'OTHER':
                ChannelPartnerAttachment.objects.filter(
                    content_type=ContentType.objects.get_for_model(instance),
                    object_id=str(instance.id),
                    attachment_type=attachment_type
                ).delete()
            
            # Create new attachment
            attachment = ChannelPartnerAttachment.objects.create(
                content_object=instance,
                attachment_type=attachment_type,
                file=file,
                original_filename=file.name,
                description=description
            )
            
            serializer = ChannelPartnerAttachmentSerializer(attachment, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except self.model.DoesNotExist:
            return Response({'error': 'Object not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AttachmentDeleteView(APIView):
    """Base view for deleting attachments"""
    model = None
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request, pk, attachment_id):
        try:
            instance = self.model.objects.get(pk=pk)
            content_type = ContentType.objects.get_for_model(instance)
            
            attachment = ChannelPartnerAttachment.objects.get(
                id=attachment_id,
                content_type=content_type,
                object_id=str(instance.id)
            )
            attachment.is_deleted = True
            attachment.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except self.model.DoesNotExist:
            return Response({'error': 'Object not found'}, status=status.HTTP_404_NOT_FOUND)
        except ChannelPartnerAttachment.DoesNotExist:
            return Response({'error': 'Attachment not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
