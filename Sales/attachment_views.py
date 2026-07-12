from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.views import APIView
from .attachment_models import SalesOrderAttachment
from .attachment_serializers import SalesOrderAttachmentSerializer
from utils import apply_company_location_filter


class SalesOrderAttachmentMixin:
    """Mixin to handle attachments for sales orders"""
    
    def handle_attachments(self, instance, request):
        """Process and save attachments from request"""
        # Only process if FILES are present (multipart/form-data)
        if not request.FILES:
            return
            
        # Get all files from the request
        files = request.FILES.getlist('attachments')
        descriptions = request.data.getlist('descriptions', []) if hasattr(request.data, 'getlist') else []
        
        for idx, file in enumerate(files):
            description = descriptions[idx] if idx < len(descriptions) else ''
            SalesOrderAttachment.objects.create(
                sales_order=instance,
                file=file,
                original_filename=file.name,
                description=description
            )


class SalesOrderAttachmentListView(APIView):
    """View for listing sales order attachments"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, pk):
        from .models import SalesOrder
        try:
            qs = SalesOrder.filtered_objects.get_qs(user=request.user)
            qs = apply_company_location_filter(qs, request.user, company_field='company')
            sales_order = qs.get(pk=pk)
            attachments = SalesOrderAttachment.objects.filter(
                sales_order=sales_order,
                is_deleted=False
            )
            serializer = SalesOrderAttachmentSerializer(attachments, many=True, context={'request': request})
            return Response(serializer.data)
        except SalesOrder.DoesNotExist:
            return Response({'error': 'Sales Order not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SalesOrderAttachmentUploadView(APIView):
    """View for uploading sales order attachments"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, pk):
        from .models import SalesOrder
        try:
            qs = SalesOrder.filtered_objects.get_qs(user=request.user)
            qs = apply_company_location_filter(qs, request.user, company_field='company')
            sales_order = qs.get(pk=pk)
            file = request.FILES.get('file')
            description = request.data.get('description', '')
            
            if not file:
                return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Create new attachment
            attachment = SalesOrderAttachment.objects.create(
                sales_order=sales_order,
                file=file,
                original_filename=file.name,
                description=description
            )
            
            serializer = SalesOrderAttachmentSerializer(attachment, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except SalesOrder.DoesNotExist:
            return Response({'error': 'Sales Order not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SalesOrderAttachmentDeleteView(APIView):
    """View for deleting sales order attachments"""
    permission_classes = [permissions.AllowAny]
    
    def delete(self, request, pk, attachment_id):
        from .models import SalesOrder
        try:
            qs = SalesOrder.filtered_objects.get_qs(user=request.user)
            qs = apply_company_location_filter(qs, request.user, company_field='company')
            sales_order = qs.get(pk=pk)
            
            attachment = SalesOrderAttachment.objects.get(
                id=attachment_id,
                sales_order=sales_order
            )
            attachment.is_deleted = True
            attachment.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except SalesOrder.DoesNotExist:
            return Response({'error': 'Sales Order not found'}, status=status.HTTP_404_NOT_FOUND)
        except SalesOrderAttachment.DoesNotExist:
            return Response({'error': 'Attachment not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
