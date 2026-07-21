from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.utils import timezone
from django.db.models import Sum, Count

from .models import Booking, BookingStatusHistory
from .serializers import BookingSerializer, BookingStatusHistorySerializer, BOOKING_STATUS_LIST


class BookingViewSet(viewsets.ModelViewSet):
    """Module 8 - Booking Management"""
    queryset = Booking.objects.select_related(
        'lead', 'project', 'plot', 'flat', 'sales_executive'
    ).filter(is_deleted=False)
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'status', 'sales_executive', 'unit_type']
    search_fields = ['customer_name', 'customer_mobile', 'code', 'unit_number']
    ordering_fields = ['booking_date', 'created_on', 'booking_amount']
    ordering = ['-booking_date']

    def get_queryset(self):
        qs = super().get_queryset()
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        if from_date:
            qs = qs.filter(booking_date__gte=from_date)
        if to_date:
            qs = qs.filter(booking_date__lte=to_date)
        return qs

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update booking status and record history"""
        booking = self.get_object()
        new_status = request.data.get('status')
        remarks = request.data.get('remarks', '')

        if not new_status:
            return Response({'error': 'status is required'}, status=status.HTTP_400_BAD_REQUEST)

        old_status = booking.status
        booking.status = new_status

        if new_status == 'CANCELLED':
            booking.cancellation_reason = request.data.get('cancellation_reason', '')
            booking.cancelled_date = timezone.now().date()
            # Free up inventory
            try:
                if booking.plot:
                    booking.plot.status = 'AVAILABLE'
                    booking.plot.save(update_fields=['status'])
                elif booking.flat:
                    booking.flat.status = 'AVAILABLE'
                    booking.flat.save(update_fields=['status'])
            except Exception:
                pass
        elif new_status == 'REGISTERED':
            # Mark inventory as Registered
            try:
                if booking.plot:
                    booking.plot.status = 'REGISTERED'
                    booking.plot.save(update_fields=['status'])
                elif booking.flat:
                    booking.flat.status = 'REGISTERED'
                    booking.flat.save(update_fields=['status'])
            except Exception:
                pass
            # Update lead status
            if booking.lead:
                booking.lead.status = 'REGISTRATION'
                booking.lead.save(update_fields=['status'])

        booking.save()

        BookingStatusHistory.objects.create(
            booking=booking,
            from_status=old_status,
            to_status=new_status,
            changed_by=request.user,
            remarks=remarks,
        )

        return Response(BookingSerializer(booking, context={'request': request}).data)

    @action(detail=True, methods=['get'])
    def status_history(self, request, pk=None):
        """Get status history for a booking"""
        booking = self.get_object()
        history = booking.status_history.all()
        return Response(BookingStatusHistorySerializer(history, many=True).data)

    @action(detail=False, methods=['get'])
    def choices(self, request):
        return Response({'booking_statuses': BOOKING_STATUS_LIST})

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Booking statistics for dashboard"""
        today = timezone.now().date()
        qs = Booking.objects.filter(is_deleted=False)
        active = qs.exclude(status='CANCELLED')
        return Response({
            'total': qs.count(),
            'booked': qs.filter(status='BOOKED').count(),
            'agreement': qs.filter(status='AGREEMENT').count(),
            'registered': qs.filter(status='REGISTERED').count(),
            'cancelled': qs.filter(status='CANCELLED').count(),
            'this_month': qs.filter(
                booking_date__year=today.year,
                booking_date__month=today.month
            ).count(),
            'total_revenue': float(
                active.aggregate(total=Sum('agreed_price'))['total'] or 0
            ),
            'booking_revenue': float(
                active.aggregate(total=Sum('booking_amount'))['total'] or 0
            ),
        })
