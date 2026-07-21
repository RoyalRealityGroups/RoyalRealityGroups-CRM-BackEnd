from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as django_filters
from rest_framework import filters
from django.utils import timezone

from .models import Lead, LeadStatusHistory, LeadFollowUp, LeadCrossCheck
from .serializers import (
    LeadSerializer, LeadStatusHistorySerializer, LeadFollowUpSerializer,
    LeadCrossCheckSerializer,
    LEAD_SOURCE_CHOICES_LIST, LEAD_STATUS_CHOICES_LIST,
    FOLLOW_UP_TYPE_CHOICES_LIST,
)


class LeadFilter(django_filters.FilterSet):
    from_date = django_filters.DateFilter(field_name='created_on', lookup_expr='date__gte')
    to_date = django_filters.DateFilter(field_name='created_on', lookup_expr='date__lte')

    class Meta:
        model = Lead
        fields = ['status', 'lead_source', 'assigned_employee', 'from_date', 'to_date']


class LeadViewSet(viewsets.ModelViewSet):
    """ViewSet for Lead management - Module 2"""
    queryset = Lead.objects.select_related(
        'assigned_employee', 'interested_project'
    ).filter(is_deleted=False)
    serializer_class = LeadSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = LeadFilter
    search_fields = ['name', 'mobile', 'email', 'code']
    ordering_fields = ['created_on', 'status', 'name']
    ordering = ['-created_on']

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        instance = self.get_object()
        instance._previous_status = instance.status
        serializer.save()

    @action(detail=False, methods=['post'])
    def cross_check(self, request):
        """Module 3: Cross Lead Check"""
        mobile = request.data.get('mobile', '').strip()
        alternate_number = request.data.get('alternate_number', '').strip()
        email = request.data.get('email', '').strip()

        if not any([mobile, alternate_number, email]):
            return Response(
                {'has_duplicates': False, 'duplicates': [], 'message': 'No fields provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from django.db.models import Q
        dup_q = Q()
        if mobile:
            dup_q |= Q(mobile=mobile)
        if alternate_number:
            dup_q |= Q(alternate_number=alternate_number)
        if email:
            dup_q |= Q(email__iexact=email)

        duplicates = Lead.objects.filter(dup_q).filter(is_deleted=False).distinct()

        if duplicates.exists():
            dup_list = []
            for dup in duplicates:
                match_field = 'unknown'
                match_value = ''
                if mobile and dup.mobile == mobile:
                    match_field, match_value = 'mobile', mobile
                elif alternate_number and dup.alternate_number == alternate_number:
                    match_field, match_value = 'alternate_number', alternate_number
                elif email and dup.email and dup.email.lower() == email.lower():
                    match_field, match_value = 'email', email

                last_fu = dup.follow_ups.order_by('-follow_up_date').values_list('follow_up_date', flat=True).first()
                emp = dup.assigned_employee
                emp_name = (
                    f"{emp.first_name} {emp.last_name}".strip() or emp.username
                ) if emp else None

                dup_list.append({
                    'lead': {
                        'id': str(dup.id),
                        'code': dup.code,
                        'name': dup.name,
                        'status': dup.get_status_display(),
                        'last_follow_up_date': last_fu.isoformat() if last_fu else None,
                        'assigned_employee': {'name': emp_name} if emp_name else None,
                    },
                    'match_field': match_field,
                    'match_value': match_value,
                })

            return Response({
                'has_duplicates': True,
                'duplicates': dup_list,
                'message': f'Found {duplicates.count()} duplicate lead(s)',
            })

        return Response({'has_duplicates': False, 'duplicates': [], 'message': 'No duplicates found'})

    @action(detail=True, methods=['get'])
    def status_history(self, request, pk=None):
        """Get status change history for a lead"""
        lead = self.get_object()
        history = lead.status_history.all()
        serializer = LeadStatusHistorySerializer(history, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update lead status and record history"""
        lead = self.get_object()
        new_status = request.data.get('status')
        remarks = request.data.get('remarks', '')

        if not new_status:
            return Response({'error': 'status is required'}, status=status.HTTP_400_BAD_REQUEST)

        old_status = lead.status
        lead.status = new_status
        lead.save(update_fields=['status'])

        LeadStatusHistory.objects.create(
            lead=lead,
            from_status=old_status,
            to_status=new_status,
            changed_by=request.user,
            remarks=remarks,
        )

        return Response(LeadSerializer(lead, context={'request': request}).data)

    @action(detail=False, methods=['get'])
    def choices(self, request):
        """Get all dropdown choices"""
        return Response({
            'lead_sources': LEAD_SOURCE_CHOICES_LIST,
            'lead_statuses': LEAD_STATUS_CHOICES_LIST,
            'follow_up_types': FOLLOW_UP_TYPE_CHOICES_LIST,
        })

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Lead statistics for dashboard"""
        today = timezone.now().date()
        qs = Lead.objects.filter(is_deleted=False)

        return Response({
            'total': qs.count(),
            'today': qs.filter(created_on__date=today).count(),
            'new': qs.filter(status='NEW_LEAD').count(),
            'site_visit_scheduled': qs.filter(status='SITE_VISIT_SCHEDULED').count(),
            'booking': qs.filter(status='BOOKING').count(),
            'registration': qs.filter(status='REGISTRATION').count(),
            'lost': qs.filter(status='LOST').count(),
            'by_source': list(
                qs.values('lead_source').annotate(
                    count=__import__('django.db.models', fromlist=['Count']).Count('id')
                ).order_by('-count')
            ),
        })


class FollowUpFilter(django_filters.FilterSet):
    from_date = django_filters.DateFilter(field_name='follow_up_date', lookup_expr='gte')
    to_date = django_filters.DateFilter(field_name='follow_up_date', lookup_expr='lte')

    class Meta:
        model = LeadFollowUp
        fields = ['lead', 'follow_up_type', 'from_date', 'to_date']


class LeadFollowUpViewSet(viewsets.ModelViewSet):
    """ViewSet for Lead Follow-ups - Module 4"""
    queryset = LeadFollowUp.objects.select_related('lead', 'created_by').filter(lead__is_deleted=False)
    serializer_class = LeadFollowUpSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = FollowUpFilter
    search_fields = ['lead__name', 'lead__mobile', 'lead__code', 'discussion_notes']
    ordering_fields = ['follow_up_date', 'next_follow_up_date']
    ordering = ['-follow_up_date']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def due_today(self, request):
        """Get follow-ups due today"""
        today = timezone.now().date()
        followups = self.get_queryset().filter(next_follow_up_date=today)
        serializer = LeadFollowUpSerializer(followups, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue follow-ups"""
        today = timezone.now().date()
        followups = self.get_queryset().filter(
            next_follow_up_date__lt=today
        ).exclude(lead__status__in=['LOST', 'REGISTRATION'])
        serializer = LeadFollowUpSerializer(followups, many=True)
        return Response(serializer.data)
