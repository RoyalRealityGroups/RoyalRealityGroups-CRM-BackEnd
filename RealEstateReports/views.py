"""
Module 11 - Reports Views
Endpoints for Lead, Site Visit, Sales, Revenue, and Employee Performance reports.
All reports support ?period= filter: today, this_week, this_month, last_month, this_year
All list reports support Excel export via ?export=excel
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.http import HttpResponse

from .services import (
    lead_report_by_source,
    lead_report_by_employee,
    lead_report_by_project,
    lead_report_by_status,
    site_visit_report,
    booking_report,
    revenue_report,
    employee_performance_report,
    registration_report,
    export_to_excel,
    export_to_pdf,
)


def _period(request):
    return request.query_params.get('period', None)


def _project_id(request):
    return request.query_params.get('project', None)


def _employee_id(request):
    return request.query_params.get('employee', None)


def _export_response(request, data, columns, filename, title):
    """Handle export=excel or export=pdf."""
    export_format = request.query_params.get('export')
    if export_format == 'excel':
        try:
            content = export_to_excel(data, columns, title)
            resp = HttpResponse(
                content,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
            resp['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
            return resp
        except ImportError as e:
            return Response({'error': str(e)}, status=status.HTTP_501_NOT_IMPLEMENTED)
    elif export_format == 'pdf':
        try:
            content = export_to_pdf(data, columns, title)
            resp = HttpResponse(content, content_type='application/pdf')
            resp['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
            return resp
        except ImportError as e:
            return Response({'error': str(e)}, status=status.HTTP_501_NOT_IMPLEMENTED)
    return None


# ============================================================================
# LEAD REPORTS
# ============================================================================

class LeadReportBySourceView(APIView):
    """Lead report grouped by source (Website, Facebook, etc.)"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = lead_report_by_source(
            period=_period(request),
            project_id=_project_id(request),
        )
        columns = [
            {'key': 'lead_source', 'label': 'Lead Source'},
            {'key': 'count', 'label': 'Count'},
        ]
        export = _export_response(request, data['data'], columns, 'lead_report_by_source', 'Lead Report - Source Wise')
        if export:
            return export
        return Response(data)


class LeadReportByEmployeeView(APIView):
    """Lead report grouped by assigned employee"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = lead_report_by_employee(
            period=_period(request),
            project_id=_project_id(request),
        )
        columns = [
            {'key': 'employee_name', 'label': 'Employee'},
            {'key': 'count', 'label': 'Leads'},
        ]
        export = _export_response(request, data['data'], columns, 'lead_report_by_employee', 'Lead Report - Employee Wise')
        if export:
            return export
        return Response(data)


class LeadReportByProjectView(APIView):
    """Lead report grouped by interested project"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = lead_report_by_project(period=_period(request))
        columns = [
            {'key': 'project_name', 'label': 'Project'},
            {'key': 'count', 'label': 'Leads'},
        ]
        export = _export_response(request, data['data'], columns, 'lead_report_by_project', 'Lead Report - Project Wise')
        if export:
            return export
        return Response(data)


class LeadReportByStatusView(APIView):
    """Lead report grouped by status"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = lead_report_by_status(period=_period(request))
        columns = [
            {'key': 'status', 'label': 'Status'},
            {'key': 'count', 'label': 'Count'},
        ]
        export = _export_response(request, data['data'], columns, 'lead_report_by_status', 'Lead Report - Status Wise')
        if export:
            return export
        return Response(data)


# ============================================================================
# SITE VISIT REPORTS
# ============================================================================

class SiteVisitReportView(APIView):
    """Site visit summary — daily / weekly / monthly"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        period = _period(request) or 'this_month'
        data = site_visit_report(
            period=period,
            project_id=_project_id(request),
            employee_id=_employee_id(request),
        )
        columns = [
            {'key': 'employee_name', 'label': 'Employee'},
            {'key': 'count', 'label': 'Site Visits'},
        ]
        export = _export_response(request, data['by_employee'], columns, 'site_visit_report', 'Site Visit Report')
        if export:
            return export
        return Response(data)


# ============================================================================
# SALES / BOOKING REPORTS
# ============================================================================

class BookingReportView(APIView):
    """Booking report with revenue"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = booking_report(
            period=_period(request),
            project_id=_project_id(request),
            employee_id=_employee_id(request),
        )
        columns = [
            {'key': 'project_name', 'label': 'Project'},
            {'key': 'count', 'label': 'Bookings'},
            {'key': 'revenue', 'label': 'Revenue (₹)'},
        ]
        export = _export_response(request, data['by_project'], columns, 'booking_report', 'Booking Report')
        if export:
            return export
        return Response(data)


class RevenueReportView(APIView):
    """Monthly revenue report"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        period = _period(request) or 'this_year'
        data = revenue_report(period=period)
        columns = [
            {'key': 'month', 'label': 'Month'},
            {'key': 'bookings', 'label': 'Bookings'},
            {'key': 'revenue', 'label': 'Revenue (₹)'},
        ]
        export = _export_response(request, data['monthly'], columns, 'revenue_report', 'Revenue Report')
        if export:
            return export
        return Response(data)


class RegistrationReportView(APIView):
    """Registration report — bookings that reached REGISTERED status"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = registration_report(
            period=_period(request),
            project_id=_project_id(request),
        )
        columns = [
            {'key': 'project_name', 'label': 'Project'},
            {'key': 'count', 'label': 'Registrations'},
            {'key': 'revenue', 'label': 'Revenue (₹)'},
        ]
        export = _export_response(request, data['by_project'], columns, 'registration_report', 'Registration Report')
        if export:
            return export
        return Response(data)


# ============================================================================
# EMPLOYEE PERFORMANCE REPORT
# ============================================================================

class EmployeePerformanceReportView(APIView):
    """Per-employee performance: leads, site visits, bookings, registrations"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        period = _period(request) or 'this_month'
        data = employee_performance_report(period=period)
        columns = [
            {'key': 'employee_name', 'label': 'Employee'},
            {'key': 'designation', 'label': 'Designation'},
            {'key': 'leads', 'label': 'Leads'},
            {'key': 'site_visits', 'label': 'Site Visits'},
            {'key': 'bookings', 'label': 'Bookings'},
            {'key': 'registrations', 'label': 'Registrations'},
        ]
        export = _export_response(request, data, columns, 'employee_performance', 'Employee Performance Report')
        if export:
            return export
        return Response({'period': period, 'data': data})


# ============================================================================
# COMBINED DASHBOARD SUMMARY (used by Module 12)
# ============================================================================

class DashboardSummaryView(APIView):
    """
    Module 12 - Dashboard KPIs.
    Returns data for both Team Leader and Director dashboards.

    Data scoping:
      - Superuser / staff: sees ALL data
      - Regular user (e.g. sales executive): sees only their OWN data
    """
    permission_classes = [permissions.IsAuthenticated]

    def _is_admin(self, user):
        """Check if user should see all data — superuser or staff only."""
        return user.is_superuser or user.is_staff

    def _scope_leads(self, qs, user):
        if self._is_admin(user):
            return qs
        return qs.filter(assigned_employee=user)

    def _scope_site_visits(self, qs, user):
        if self._is_admin(user):
            return qs
        return qs.filter(assigned_employee=user)

    def _scope_bookings(self, qs, user):
        if self._is_admin(user):
            return qs
        return qs.filter(sales_executive=user)

    def _scope_call_logs(self, qs, user):
        if self._is_admin(user):
            return qs
        return qs.filter(called_by=user)

    def get(self, request):
        from django.utils import timezone
        from Lead.models import Lead, CallLog
        from SiteVisit.models import SiteVisit
        from Booking.models import Booking
        from Users.models import User
        from django.db.models import Sum, Count
        from django.db.models import Q as models_Q
        from django.db.models.functions import TruncHour

        today = timezone.now().date()
        user = request.user
        is_admin = self._is_admin(user)

        # Base querysets (soft-delete aware)
        lead_qs = self._scope_leads(Lead.objects.filter(is_deleted=False), user)
        sv_qs = self._scope_site_visits(SiteVisit.objects.filter(is_deleted=False), user)
        bkg_qs = self._scope_bookings(Booking.objects.filter(is_deleted=False), user)
        active_bkg = bkg_qs.exclude(status='CANCELLED')
        call_qs = self._scope_call_logs(CallLog.objects.all(), user)

        # ---- TODAY'S INSIGHTS (summary for the card) ----
        today_calls = call_qs.filter(called_at__date=today).count()
        today_leads = lead_qs.filter(created_on__date=today).count()
        today_followups_done = 0
        try:
            from Lead.models import LeadFollowUp
            fu_qs = LeadFollowUp.objects.filter(lead__is_deleted=False, follow_up_date=today)
            if not is_admin:
                fu_qs = fu_qs.filter(models_Q(created_by=user) | models_Q(lead__assigned_employee=user))
            today_followups_done = fu_qs.count()
        except Exception:
            pass

        todays_insights = {
            'calls': today_calls,
            'leads_entered': today_leads,
            'follow_ups': today_followups_done,
            'site_visits': sv_qs.filter(visit_date=today).count(),
        }

        # ---- CALLING TREND (hourly for today, 0-23) ----
        today_calls_qs = call_qs.filter(called_at__date=today)
        hourly_data = list(
            today_calls_qs
            .annotate(hour=TruncHour('called_at'))
            .values('hour')
            .annotate(count=Count('id'))
            .order_by('hour')
        )
        # Build full 24-hour array
        hourly_map = {row['hour'].hour: row['count'] for row in hourly_data}
        calling_trend = [
            {'hour': h, 'label': f"{h:02d}:00", 'calls': hourly_map.get(h, 0)}
            for h in range(24)
        ]

        # ---- EMPLOYEE PERFORMANCE TABLE (with calls) ----
        if is_admin:
            employees = User.objects.filter(is_active=True, is_superuser=False)[:20]
        else:
            # Non-admin sees only themselves
            employees = User.objects.filter(id=user.id)

        all_leads = Lead.objects.filter(is_deleted=False)
        all_sv = SiteVisit.objects.filter(is_deleted=False)
        all_bkg = Booking.objects.filter(is_deleted=False)
        all_calls = CallLog.objects.all()

        employee_performance = []
        for emp in employees:
            leads = all_leads.filter(assigned_employee=emp).count()
            visits = all_sv.filter(assigned_employee=emp).count()
            bookings = all_bkg.exclude(status='CANCELLED').filter(sales_executive=emp).count()
            registrations = all_bkg.filter(sales_executive=emp, status='REGISTERED').count()
            calls = all_calls.filter(called_by=emp).count()
            today_emp_calls = all_calls.filter(called_by=emp, called_at__date=today).count()
            if leads > 0 or visits > 0 or bookings > 0 or calls > 0:
                employee_performance.append({
                    'employee_id': str(emp.id),
                    'employee_name': f"{emp.first_name} {emp.last_name}".strip() or emp.username,
                    'designation': getattr(emp, 'designation', None),
                    'leads': leads,
                    'site_visits': visits,
                    'bookings': bookings,
                    'registrations': registrations,
                    'calls_total': calls,
                    'calls_today': today_emp_calls,
                })
        employee_performance.sort(key=lambda x: x['calls_today'], reverse=True)

        # ---- PROJECT PERFORMANCE ----
        project_performance = list(
            active_bkg.values('project__id', 'project__name')
            .annotate(
                bookings=Count('id'),
                revenue=Sum('agreed_price'),
                registrations=Count('id', filter=models_Q(status='REGISTERED')),
            )
            .order_by('-bookings')[:10]
        )
        for row in project_performance:
            row['project_id'] = str(row.pop('project__id', '') or '')
            row['project_name'] = row.pop('project__name', '') or ''
            row['revenue'] = float(row['revenue'] or 0)

        # ---- LEAD PIPELINE ----
        lead_pipeline = list(
            lead_qs.filter(status__in=['ONGOING', 'LIVE', 'DEAD'])
            .values('status')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        # ---- SITE VISITS SUMMARY ----
        site_visits_summary = {
            'total': sv_qs.count(),
            'today': sv_qs.filter(visit_date=today).count(),
            'completed': sv_qs.filter(status='COMPLETED').count(),
            'scheduled': sv_qs.filter(status='SCHEDULED').count(),
        }

        return Response({
            'todays_insights': todays_insights,
            'leads': {
                'total': lead_qs.count(),
                'today': today_leads,
                'this_month': lead_qs.filter(
                    created_on__year=today.year,
                    created_on__month=today.month
                ).count(),
            },
            'calling_trend': calling_trend,
            'lead_pipeline': lead_pipeline,
            'site_visits': site_visits_summary,
            'bookings': {
                'total': active_bkg.count(),
            },
            'employee_performance': employee_performance[:10],
            'project_performance': project_performance,
            'is_admin_view': is_admin,
        })


class TodaysInsightsDetailView(APIView):
    """
    Detailed view for Today's Insights card.
    Returns granular breakdown: calls by type, leads entered, follow-ups done,
    conversions, hourly call distribution, and per-lead call details.

    Data scoping: same as DashboardSummaryView.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from django.utils import timezone
        from Lead.models import Lead, CallLog, LeadFollowUp
        from SiteVisit.models import SiteVisit
        from Booking.models import Booking
        from django.db.models import Count, Sum, Avg, Q as models_Q
        from django.db.models.functions import TruncHour

        today = timezone.now().date()
        now = timezone.now()
        user = request.user
        is_admin = user.is_superuser or user.is_staff

        # --- Scoped querysets ---
        if is_admin:
            call_qs = CallLog.objects.filter(called_at__date=today)
            lead_qs = Lead.objects.filter(is_deleted=False, created_on__date=today)
            fu_qs = LeadFollowUp.objects.filter(lead__is_deleted=False, follow_up_date=today)
            sv_qs = SiteVisit.objects.filter(is_deleted=False, visit_date=today)
            bkg_qs = Booking.objects.filter(is_deleted=False, booking_date=today)
        else:
            call_qs = CallLog.objects.filter(called_at__date=today, called_by=user)
            lead_qs = Lead.objects.filter(is_deleted=False, created_on__date=today, assigned_employee=user)
            fu_qs = LeadFollowUp.objects.filter(
                lead__is_deleted=False, follow_up_date=today
            ).filter(models_Q(created_by=user) | models_Q(lead__assigned_employee=user))
            sv_qs = SiteVisit.objects.filter(is_deleted=False, visit_date=today, assigned_employee=user)
            bkg_qs = Booking.objects.filter(is_deleted=False, booking_date=today, sales_executive=user)

        # --- Call summary ---
        calls_by_type = list(
            call_qs.values('call_type').annotate(count=Count('id')).order_by('-count')
        )
        total_calls = call_qs.count()
        total_duration = call_qs.aggregate(total=Sum('duration_secs'))['total'] or 0
        avg_duration = call_qs.aggregate(avg=Avg('duration_secs'))['avg'] or 0

        # --- Hourly distribution ---
        hourly_data = list(
            call_qs.annotate(hour=TruncHour('called_at'))
            .values('hour')
            .annotate(count=Count('id'))
            .order_by('hour')
        )
        hourly_map = {row['hour'].hour: row['count'] for row in hourly_data}
        hourly_distribution = [
            {'hour': h, 'label': f"{h:02d}:00", 'calls': hourly_map.get(h, 0)}
            for h in range(24)
        ]

        # --- Peak hour ---
        peak_hour = max(hourly_distribution, key=lambda x: x['calls']) if total_calls > 0 else None

        # --- Leads entered today ---
        leads_entered = lead_qs.count()
        leads_by_source = list(
            lead_qs.values('lead_source').annotate(count=Count('id')).order_by('-count')
        )

        # --- Follow-ups ---
        followups_done = fu_qs.count()
        followups_by_type = list(
            fu_qs.values('follow_up_type').annotate(count=Count('id')).order_by('-count')
        )

        # --- Site visits today ---
        site_visits_today = sv_qs.count()
        sv_completed = sv_qs.filter(status='COMPLETED').count()

        # --- Bookings today ---
        bookings_today = bkg_qs.exclude(status='CANCELLED').count()

        # --- Recent calls (last 20) ---
        recent_calls = list(
            call_qs.order_by('-called_at')[:20].values(
                'id', 'phone_number', 'call_type', 'duration_secs', 'called_at',
                'lead__name', 'lead__id', 'called_by__first_name', 'called_by__last_name',
                'called_by__username',
            )
        )
        for c in recent_calls:
            name = f"{c.pop('called_by__first_name', '') or ''} {c.pop('called_by__last_name', '') or ''}".strip()
            c['called_by_name'] = name or c.pop('called_by__username', 'Unknown')
            if 'called_by__username' in c:
                del c['called_by__username']
            c['lead_name'] = c.pop('lead__name', None)
            c['lead_id'] = str(c.pop('lead__id', '') or '') if c.get('lead__id') else None

        return Response({
            'server_now': now.isoformat(),
            'is_admin_view': is_admin,
            'summary': {
                'total_calls': total_calls,
                'total_duration_secs': total_duration,
                'avg_duration_secs': round(avg_duration, 1),
                'leads_entered': leads_entered,
                'follow_ups_done': followups_done,
                'site_visits': site_visits_today,
                'site_visits_completed': sv_completed,
                'bookings': bookings_today,
                'peak_hour': peak_hour,
            },
            'calls_by_type': calls_by_type,
            'leads_by_source': leads_by_source,
            'followups_by_type': followups_by_type,
            'hourly_distribution': hourly_distribution,
            'recent_calls': recent_calls,
        })
