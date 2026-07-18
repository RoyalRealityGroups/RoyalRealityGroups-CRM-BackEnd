from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import Document
from .serializers import DocumentSerializer, DOCUMENT_TYPE_LIST, LINKED_TO_LIST


class DocumentViewSet(viewsets.ModelViewSet):
    """Module 9 - Document Management"""
    queryset = Document.objects.select_related(
        'project', 'lead', 'booking'
    ).filter(is_deleted=False)
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['document_type', 'linked_to', 'project', 'lead', 'booking', 'is_public']
    search_fields = ['title', 'code', 'original_filename']
    ordering_fields = ['created_on', 'title', 'document_type']
    ordering = ['-created_on']

    @action(detail=False, methods=['get'])
    def choices(self, request):
        return Response({
            'document_types': DOCUMENT_TYPE_LIST,
            'linked_to_options': LINKED_TO_LIST,
        })

    @action(detail=False, methods=['get'])
    def by_project(self, request):
        """Get all documents for a specific project"""
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response({'error': 'project_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        docs = self.get_queryset().filter(project_id=project_id)
        return Response(DocumentSerializer(docs, many=True, context={'request': request}).data)

    @action(detail=False, methods=['get'])
    def by_lead(self, request):
        """Get all documents for a specific lead"""
        lead_id = request.query_params.get('lead_id')
        if not lead_id:
            return Response({'error': 'lead_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        docs = self.get_queryset().filter(lead_id=lead_id)
        return Response(DocumentSerializer(docs, many=True, context={'request': request}).data)

    @action(detail=False, methods=['get'])
    def by_booking(self, request):
        """Get all documents for a specific booking"""
        booking_id = request.query_params.get('booking_id')
        if not booking_id:
            return Response({'error': 'booking_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        docs = self.get_queryset().filter(booking_id=booking_id)
        return Response(DocumentSerializer(docs, many=True, context={'request': request}).data)
