from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import Lead, LeadStatusHistory, LeadFollowUp, LeadCrossCheck
from .serializers import (
    LeadSerializer, LeadStatusHistorySerializer, LeadFollowUpSerializer,
    LeadCrossCheckSerializer, LEAD_SOURCE_CHOICES_LIST, LEAD_STATUS_CHOICES_LIST, FOLLOW_UP_TYPE_CHOICES_LIST
)


class LeadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Lead management with Cross Lead Check functionality
    """
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'lead_source', 'assigned_employee']
    search_fields = ['name', 'mobile', 'email', 'code']
    ordering_fields = ['created_on', 'status']
    ordering = ['-created_on']
    
    def perform_create(self, serializer):
        # Let serializer handle created_by/modified_by
        serializer.save()
    
    def perform_update(self, serializer):
        # Store previous status for history tracking
        instance = self.get_object()
        instance._previous_status = instance.status
        # Let serializer handle modified_by
        serializer.save()
    
    @action(detail=False, methods=['post'])
    def cross_check(self, request):
        """
        Cross Lead Check - Check for duplicate leads based on mobile, alternate_number, email
        """
        mobile = request.data.get('mobile', '').strip()
        alternate_number = request.data.get('alternate_number', '').strip()
        email = request.data.get('email', '').strip()
        
        if not any([mobile, alternate_number, email]):
            return Response(
                {'has_duplicate': False, 'duplicates': [], 'message': 'No fields provided for check'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Build query for duplicates
        query = Lead.objects.filter(status__in=['NEW_LEAD', 'CONTACT_ATTEMPTED', 'CONNECTED', 'INTERESTED'])
        
        from django.db.models import Q
        filters = Q()
        
        if mobile:
            filters = Q(mobile=mobile)
        if alternate_number:
            if filters:
                filters = filters | Q(alternate_number=alternate_number)
            else:
                filters = Q(alternate_number=alternate_number)
        if email:
            if filters:
                filters = filters | Q(email__iexact=email)
            else:
                filters = Q(email__iexact=email)
        
        if not filters:
            return Response({
                'has_duplicates': False,
                'duplicates': [],
                'message': 'No search criteria provided'
            })
        
        duplicates = query.filter(filters).distinct()
        
        if duplicates.exists():
            # Format duplicates for frontend
            dup_list = []
            for dup in duplicates:
                # Determine which field matched
                match_field = 'unknown'
                match_value = ''
                if mobile and dup.mobile == mobile:
                    match_field = 'mobile'
                    match_value = mobile
                elif alternate_number and dup.alternate_number == alternate_number:
                    match_field = 'alternate_number'
                    match_value = alternate_number
                elif email and dup.email and dup.email.lower() == email.lower():
                    match_field = 'email'
                    match_value = email

                last_fu = dup.follow_ups.order_by('-follow_up_date').values_list('follow_up_date', flat=True).first()

                dup_list.append({
                    'lead': {
                        'id': str(dup.id),
                        'code': dup.code,
                        'name': dup.name,
                        'status': dup.get_status_display(),
                        'last_follow_up_date': last_fu.isoformat() if last_fu else None,
                        'assigned_employee': {
                            'name': f"{dup.assigned_employee.first_name} {dup.assigned_employee.last_name}".strip() or dup.assigned_employee.username if dup.assigned_employee else None
                        } if dup.assigned_employee else None
                    },
                    'match_field': match_field,
                    'match_value': match_value
                })
            
            return Response({
                'has_duplicates': True,
                'duplicates': dup_list,
                'message': f'Found {duplicates.count()} duplicate lead(s)'
            })
        
        return Response({
            'has_duplicates': False,
            'duplicates': [],
            'message': 'No duplicates found'
        })
    
    @action(detail=True, methods=['get'])
    def status_history(self, request, pk=None):
        """Get status history for a lead"""
        lead = self.get_object()
        history = lead.status_history.all()
        serializer = LeadStatusHistorySerializer(history, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def choices(self, request):
        """Get choices for lead source and status"""
        return Response({
            'lead_sources': LEAD_SOURCE_CHOICES_LIST,
            'lead_statuses': LEAD_STATUS_CHOICES_LIST,
            'follow_up_types': FOLLOW_UP_TYPE_CHOICES_LIST
        })


class LeadFollowUpViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Lead Follow-ups
    """
    queryset = LeadFollowUp.objects.all()
    serializer_class = LeadFollowUpSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['lead', 'follow_up_type']
    ordering_fields = ['follow_up_date', 'next_follow_up_date']
    ordering = ['-follow_up_date']
    
    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(created_by=user)
    
    @action(detail=False, methods=['get'])
    def due_today(self, request):
        """Get follow-ups due today"""
        from django.utils import timezone
        today = timezone.now().date()
        followups = LeadFollowUp.objects.filter(next_follow_up_date=today)
        serializer = LeadFollowUpSerializer(followups, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue follow-ups"""
        from django.utils import timezone
        today = timezone.now().date()
        followups = LeadFollowUp.objects.filter(
            next_follow_up_date__lt=today
        ).exclude(lead__status__in=['LOST', 'REGISTRATION', 'BOOKING'])
        serializer = LeadFollowUpSerializer(followups, many=True)
        return Response(serializer.data)
