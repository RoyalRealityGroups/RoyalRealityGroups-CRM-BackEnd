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


def _count_calls_on_date(call_qs, target_date):
    """
    Count the ACTUAL number of calls made on ``target_date``.

    CallLog collapses repeated calls to the same number by the same user into a
    single row (``call_count`` incremented, each timestamp appended to the
    ``call_times`` JSON list as 'DD-MM-YYYY HH:MM:SS' in IST). A plain row count
    (``.count()``) therefore undercounts: the 2nd, 3rd ... call to a number on the
    same day never creates a new row, so the card stops increasing.

    This counts every individual call by inspecting ``call_times``:
      - For each row, count how many of its ``call_times`` entries fall on
        ``target_date``.
      - Rows with an empty ``call_times`` (legacy data created before the field
        existed) fall back to their ``called_at`` date.
    """
    date_prefix = target_date.strftime('%d-%m-%Y')
    total = 0
    for times, called_at in call_qs.values_list('call_times', 'called_at'):
        if times:
            total += sum(1 for t in times if isinstance(t, str) and t.startswith(date_prefix))
        elif called_at and called_at.date() == target_date:
            # Legacy row without recorded call_times — count the single call.
            total += 1
    return total


def _hourly_calls_on_date(call_qs, target_date):
    """
    Build a 24-slot hourly distribution of ACTUAL calls on ``target_date``,
    counting every entry in ``call_times`` (not just one per row). Mirrors the
    logic in :func:`_count_calls_on_date`.
    """
    date_prefix = target_date.strftime('%d-%m-%Y')
    hourly_map = {h: 0 for h in range(24)}
    for times, called_at in call_qs.values_list('call_times', 'called_at'):
        if times:
            for t in times:
                if isinstance(t, str) and t.startswith(date_prefix):
                    # Format: 'DD-MM-YYYY HH:MM:SS'
                    try:
                        hour = int(t[11:13])
                        if 0 <= hour <= 23:
                            hourly_map[hour] += 1
                    except (ValueError, IndexError):
                        continue
        elif called_at and called_at.date() == target_date:
            hourly_map[called_at.hour] += 1
    return hourly_map


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
        """Check if user should see all data — superuser, staff, or admin-flagged user.

        Mirrors the canonical admin check in utils.apply_data_scope so the
        dashboard/reports scope matches every other screen. Users created with
        the "Admin User" toggle (Users.User.is_admin) must see all data.
        """
        return user.is_superuser or user.is_staff or getattr(user, 'is_admin', False)

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
        # Count every actual call today (repeat calls to the same number are
        # collapsed into one CallLog row via call_count/call_times), not rows.
        today_calls = _count_calls_on_date(call_qs, today)
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
        # Count every actual call (each call_times entry), not one per row.
        hourly_map = _hourly_calls_on_date(call_qs, today)
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
            emp_calls_qs = all_calls.filter(called_by=emp)
            # Lifetime total = sum of every synced call (call_count), not rows.
            calls = emp_calls_qs.aggregate(total=Sum('call_count'))['total'] or 0
            # Today's total = every actual call made today across the emp's rows.
            today_emp_calls = _count_calls_on_date(emp_calls_qs, today)
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
        # Include the custom is_admin flag so toggle-admin users see all data,
        # consistent with utils.apply_data_scope used across every other screen.
        is_admin = user.is_superuser or user.is_staff or getattr(user, 'is_admin', False)

        # --- Scoped querysets ---
        # NOTE: call_qs is scoped by user only (NOT by called_at date). Repeat
        # calls to the same number are merged into one CallLog row whose
        # called_at may be from an earlier day, so filtering by called_at__date
        # would drop today's repeat calls. Today-filtering is applied via the
        # call_times-aware helpers below.
        if is_admin:
            call_qs = CallLog.objects.all()
            lead_qs = Lead.objects.filter(is_deleted=False, created_on__date=today)
            fu_qs = LeadFollowUp.objects.filter(lead__is_deleted=False, follow_up_date=today)
            sv_qs = SiteVisit.objects.filter(is_deleted=False, visit_date=today)
            bkg_qs = Booking.objects.filter(is_deleted=False, booking_date=today)
        else:
            call_qs = CallLog.objects.filter(called_by=user)
            lead_qs = Lead.objects.filter(is_deleted=False, created_on__date=today, assigned_employee=user)
            fu_qs = LeadFollowUp.objects.filter(
                lead__is_deleted=False, follow_up_date=today
            ).filter(models_Q(created_by=user) | models_Q(lead__assigned_employee=user))
            sv_qs = SiteVisit.objects.filter(is_deleted=False, visit_date=today, assigned_employee=user)
            bkg_qs = Booking.objects.filter(is_deleted=False, booking_date=today, sales_executive=user)

        # Rows that have at least one call today (used for by-type/duration/recent).
        today_prefix = today.strftime('%d-%m-%Y')
        today_row_ids = [
            row_id for row_id, times, called_at in call_qs.values_list('id', 'call_times', 'called_at')
            if (times and any(isinstance(t, str) and t.startswith(today_prefix) for t in times))
            or (not times and called_at and called_at.date() == today)
        ]
        today_call_rows = call_qs.filter(id__in=today_row_ids)

        # --- Call summary ---
        # total_calls counts every actual call today (via call_times), not rows.
        total_calls = _count_calls_on_date(call_qs, today)
        calls_by_type = list(
            today_call_rows.values('call_type').annotate(count=Count('id')).order_by('-count')
        )
        total_duration = today_call_rows.aggregate(total=Sum('duration_secs'))['total'] or 0
        avg_duration = today_call_rows.aggregate(avg=Avg('duration_secs'))['avg'] or 0

        # --- Connected vs Dialed ---
        # Connected = client answered (duration_secs > 0).
        # Dialed    = called but no answer / not connected (duration_secs == 0,
        #             e.g. missed/rejected calls).
        connected_calls = today_call_rows.filter(duration_secs__gt=0).count()
        dialed_calls = today_call_rows.filter(duration_secs=0).count()

        # --- Hourly distribution (every actual call today, not one per row) ---
        hourly_map = _hourly_calls_on_date(call_qs, today)
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

        # --- Recent calls (last 20) — only rows with a call today ---
        recent_calls = list(
            today_call_rows.order_by('-called_at')[:20].values(
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
                'connected_calls': connected_calls,
                'dialed_calls': dialed_calls,
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


class TodaysCallsView(APIView):
    """
    Paginated + filterable list of TODAY's calls for the Recent Calls card.

    Why this is separate from TodaysInsightsDetailView:
      That view returns a fixed "last 20" preview. This endpoint returns EVERY
      call made today, with server-side filtering and pagination, so the UI can
      show all records (10/20/50 per page) and filter by time/employee/type.

    Important — call expansion:
      CallLog collapses repeat calls to the same number by the same user into one
      row (call_count incremented, each timestamp appended to the call_times JSON
      list formatted 'DD-MM-YYYY HH:MM:SS' in IST). "One call" is therefore ONE
      entry in call_times, not one row. To paginate/filter individual calls (and
      keep totals consistent with _count_calls_on_date), we EXPAND each row into
      one record per today call_times entry before filtering, sorting and paging.

    Query params:
      - from_time  : 'HH:MM' lower bound (inclusive) of the call time window (optional)
      - to_time    : 'HH:MM' upper bound (inclusive) of the call time window (optional)
                     from_time/to_time can be used alone (open-ended) or together.
      - hour       : 0-23, keep only calls in that clock hour. Legacy/back-compat;
                     ignored when from_time or to_time is supplied (optional)
      - call_type  : outgoing|incoming|missed|rejected|unknown (optional)
      - employee   : User id, keep only calls made by that user (admin only; a
                     non-admin is already scoped to their own calls) (optional)
      - page       : 1-based page number (default 1)
      - page_size  : 10 | 20 | 50 (default 10, capped at 100)

    Response:
      {
        "count": <total matching calls>,
        "page": <int>, "page_size": <int>, "num_pages": <int>,
        "is_admin_view": <bool>,
        "employees": [ {"id","name"} ... ],   # for the Called-By filter dropdown
        "results": [ {id, phone_number, call_type, duration_secs, called_at,
                      lead_name, lead_id, called_by_name, called_by_id} ... ]
      }
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from django.utils import timezone
        from Lead.models import CallLog

        today = timezone.localdate()
        today_prefix = today.strftime('%d-%m-%Y')
        user = request.user
        is_admin = user.is_superuser or user.is_staff or getattr(user, 'is_admin', False)

        # --- Scope (same rule as the insights view) ---
        if is_admin:
            call_qs = CallLog.objects.all()
        else:
            call_qs = CallLog.objects.filter(called_by=user)

        # --- Parse filters ---
        def _parse_minutes(value):
            """'HH:MM' (or 'HH:MM:SS') -> minutes-since-midnight, else None."""
            if not value:
                return None
            parts = str(value).split(':')
            try:
                h = int(parts[0])
                m = int(parts[1]) if len(parts) > 1 else 0
            except (ValueError, IndexError):
                return None
            if not (0 <= h <= 23 and 0 <= m <= 59):
                return None
            return h * 60 + m

        from_min = _parse_minutes(request.query_params.get('from_time'))
        to_min = _parse_minutes(request.query_params.get('to_time'))

        # Legacy single-hour filter — only honoured when no range is supplied.
        hour_param = request.query_params.get('hour')
        try:
            hour_filter = int(hour_param) if hour_param not in (None, '') else None
            if hour_filter is not None and not (0 <= hour_filter <= 23):
                hour_filter = None
        except (TypeError, ValueError):
            hour_filter = None
        if from_min is not None or to_min is not None:
            # If a range is given, convert the legacy hour into the range too so
            # only one time rule is active; the range always wins.
            hour_filter = None

        def _time_ok(dt):
            """True if dt's clock time passes the active time filter(s)."""
            if from_min is not None or to_min is not None:
                mins = dt.hour * 60 + dt.minute
                if from_min is not None and mins < from_min:
                    return False
                if to_min is not None and mins > to_min:
                    return False
                return True
            if hour_filter is not None:
                return dt.hour == hour_filter
            return True

        call_type_filter = request.query_params.get('call_type') or None
        employee_filter = request.query_params.get('employee') or None
        # A non-admin can only ever see their own calls; ignore any employee param.
        if not is_admin:
            employee_filter = None

        try:
            page = max(1, int(request.query_params.get('page', 1)))
        except (TypeError, ValueError):
            page = 1
        try:
            page_size = int(request.query_params.get('page_size', 10))
        except (TypeError, ValueError):
            page_size = 10
        if page_size not in (10, 20, 50):
            page_size = min(max(page_size, 1), 100)

        # Pre-filter rows by DB-level fields to avoid expanding irrelevant rows.
        if call_type_filter:
            call_qs = call_qs.filter(call_type=call_type_filter)
        if employee_filter:
            call_qs = call_qs.filter(called_by__id=employee_filter)

        rows = call_qs.values(
            'id', 'phone_number', 'call_type', 'duration_secs', 'called_at',
            'call_times', 'lead__name', 'lead__id',
            'called_by__first_name', 'called_by__last_name', 'called_by__username',
            'called_by__id',
        )

        # --- Expand each row into one record per today's call_times entry ---
        expanded = []
        for r in rows:
            name = f"{r.get('called_by__first_name') or ''} {r.get('called_by__last_name') or ''}".strip()
            called_by_name = name or r.get('called_by__username') or 'Unknown'
            called_by_id = str(r.get('called_by__id')) if r.get('called_by__id') else None
            lead_name = r.get('lead__name')
            lead_id = str(r.get('lead__id')) if r.get('lead__id') else None

            base = {
                'id': str(r['id']),
                'phone_number': r['phone_number'],
                'call_type': r['call_type'],
                'duration_secs': r['duration_secs'],
                'lead_name': lead_name,
                'lead_id': lead_id,
                'called_by_name': called_by_name,
                'called_by_id': called_by_id,
            }

            times = r.get('call_times') or []
            today_times = [t for t in times if isinstance(t, str) and t.startswith(today_prefix)]

            if today_times:
                for idx, t in enumerate(today_times):
                    try:
                        dt = timezone.datetime.strptime(t, '%d-%m-%Y %H:%M:%S')
                    except (ValueError, TypeError):
                        continue
                    if not _time_ok(dt):
                        continue
                    rec = dict(base)
                    # Keep a stable unique key per expanded call.
                    rec['id'] = f"{base['id']}-{idx}"
                    rec['called_at'] = dt.isoformat()
                    rec['_sort'] = dt
                    expanded.append(rec)
            else:
                # Legacy row without call_times: fall back to called_at if it's today.
                called_at = r.get('called_at')
                if called_at and timezone.localtime(called_at).date() == today:
                    local_dt = timezone.localtime(called_at)
                    if _time_ok(local_dt):
                        rec = dict(base)
                        rec['called_at'] = local_dt.isoformat()
                        rec['_sort'] = local_dt.replace(tzinfo=None)
                        expanded.append(rec)

        # --- Sort newest-first and paginate ---
        expanded.sort(key=lambda x: x['_sort'], reverse=True)
        for rec in expanded:
            rec.pop('_sort', None)

        count = len(expanded)
        num_pages = (count + page_size - 1) // page_size if count else 0
        if num_pages and page > num_pages:
            page = num_pages
        start = (page - 1) * page_size
        results = expanded[start:start + page_size]

        # --- Employee dropdown options (admin only) ---
        employees = []
        if is_admin:
            seen = {}
            for r in rows:
                uid = r.get('called_by__id')
                if uid and uid not in seen:
                    nm = f"{r.get('called_by__first_name') or ''} {r.get('called_by__last_name') or ''}".strip()
                    seen[uid] = nm or r.get('called_by__username') or 'Unknown'
            employees = [{'id': str(k), 'name': v} for k, v in sorted(seen.items(), key=lambda kv: kv[1].lower())]

        return Response({
            'count': count,
            'page': page,
            'page_size': page_size,
            'num_pages': num_pages,
            'is_admin_view': is_admin,
            'employees': employees,
            'results': results,
        })


class EmployeePerformanceDetailView(APIView):
    """
    All-round performance drill-down for a single employee, filterable by period.

    Opened from the dashboard Employee Performance table when an employee row is
    clicked. Returns:
      - profile  : identity + HR fields (designation, joining date, tenure,
                   reporting manager, contact, status)
      - period   : the applied period + its resolved [start, end] date range
      - summary  : period-scoped counters (leads, site visits, calls, bookings,
                   registrations) and money (booking value, revenue, incentive)
      - bookings : full list of the employee's bookings/registrations in the
                   period (newest first) with project / unit / customer / amounts

    Query params:
      - period : today | this_week | this_month | last_month | this_year | all
                 (default: this_month)

    Access: superuser / staff / is_admin can view anyone; a regular user may only
    view their OWN detail (returns 403 otherwise).
    """
    permission_classes = [permissions.IsAuthenticated]

    def _resolve_period(self, period, today):
        """Return (start_date, end_date) inclusive, or (None, None) for 'all'."""
        import datetime as _dt
        if period == 'today':
            return today, today
        if period == 'this_week':
            start = today - _dt.timedelta(days=today.weekday())  # Monday
            return start, today
        if period == 'this_month':
            return today.replace(day=1), today
        if period == 'last_month':
            first_this = today.replace(day=1)
            last_prev = first_this - _dt.timedelta(days=1)
            return last_prev.replace(day=1), last_prev
        if period == 'this_year':
            return today.replace(month=1, day=1), today
        return None, None  # 'all'

    def get(self, request, employee_id):
        from django.utils import timezone
        from django.contrib.auth import get_user_model
        from django.db.models import Count, Sum, Q as models_Q
        from Lead.models import Lead, CallLog
        from SiteVisit.models import SiteVisit
        from Booking.models import Booking

        User = get_user_model()
        today = timezone.localdate()
        user = request.user
        is_admin = user.is_superuser or user.is_staff or getattr(user, 'is_admin', False)

        # --- Access control ---
        if not is_admin and str(user.id) != str(employee_id):
            return Response(
                {'detail': 'You do not have permission to view this employee.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            emp = User.objects.filter(id=employee_id).first()
        except (ValueError, TypeError, Exception):
            # Invalid UUID / lookup error -> treat as not found.
            emp = None
        if emp is None:
            return Response({'detail': 'Employee not found.'}, status=status.HTTP_404_NOT_FOUND)

        period = (request.query_params.get('period') or 'this_month').lower()
        valid_periods = {'today', 'this_week', 'this_month', 'last_month', 'this_year', 'all'}
        if period not in valid_periods:
            period = 'this_month'
        start_date, end_date = self._resolve_period(period, today)

        # --- Profile ---
        full_name = f"{emp.first_name} {emp.last_name}".strip() or emp.username
        manager = getattr(emp, 'reporting_manager', None)
        manager_name = None
        if manager:
            manager_name = f"{manager.first_name} {manager.last_name}".strip() or manager.username

        joining_date = getattr(emp, 'joining_date', None)
        tenure_days = (today - joining_date).days if joining_date else None

        profile = {
            'id': str(emp.id),
            'name': full_name,
            'username': emp.username,
            'designation': getattr(emp, 'designation', None),
            'email': emp.email or None,
            'phone': getattr(emp, 'phone', None) or getattr(emp, 'mobile', None),
            'joining_date': joining_date.isoformat() if joining_date else None,
            'tenure_days': tenure_days,
            'reporting_manager': manager_name,
            'status': getattr(emp, 'user_status', None),
            'is_active': emp.is_active,
        }

        # --- Period-scoped querysets (by date field relevant to each model) ---
        leads_qs = Lead.objects.filter(is_deleted=False, assigned_employee=emp)
        sv_qs = SiteVisit.objects.filter(is_deleted=False, assigned_employee=emp)
        bkg_qs = Booking.objects.filter(is_deleted=False, sales_executive=emp)
        call_qs = CallLog.objects.filter(called_by=emp)

        if start_date is not None:
            leads_qs = leads_qs.filter(created_on__date__range=(start_date, end_date))
            sv_qs = sv_qs.filter(visit_date__range=(start_date, end_date))
            bkg_qs = bkg_qs.filter(booking_date__range=(start_date, end_date))

        active_bkg = bkg_qs.exclude(status='CANCELLED')
        reg_bkg = bkg_qs.filter(status='REGISTERED')

        # --- Calls in the period (expand call_times; honours the dedup model) ---
        if start_date is None:
            calls_count = call_qs.aggregate(total=Sum('call_count'))['total'] or 0
        else:
            calls_count = 0
            for times, called_at in call_qs.values_list('call_times', 'called_at'):
                if times:
                    for t in times:
                        if not isinstance(t, str):
                            continue
                        try:
                            d = timezone.datetime.strptime(t[:10], '%d-%m-%Y').date()
                        except (ValueError, TypeError):
                            continue
                        if start_date <= d <= end_date:
                            calls_count += 1
                elif called_at:
                    d = timezone.localtime(called_at).date()
                    if start_date <= d <= end_date:
                        calls_count += 1

        money = active_bkg.aggregate(
            booking_value=Sum('agreed_price'),
            revenue=Sum('revenue'),
            incentive=Sum('incentive'),
        )

        summary = {
            'leads': leads_qs.count(),
            'site_visits': sv_qs.count(),
            'site_visits_completed': sv_qs.filter(status='COMPLETED').count(),
            'calls': calls_count,
            'bookings': active_bkg.count(),
            'registrations': reg_bkg.count(),
            'booking_value': float(money['booking_value'] or 0),
            'revenue': float(money['revenue'] or 0),
            'incentive': float(money['incentive'] or 0),
        }

        # --- Booking / registration detail list (newest first) ---
        status_labels = dict(getattr(Booking, 'BOOKING_STATUS_CHOICES', []) or [])
        try:
            from Booking.models import BOOKING_STATUS_CHOICES
            status_labels = dict(BOOKING_STATUS_CHOICES)
        except Exception:
            pass

        bookings = []
        for b in bkg_qs.select_related('project').order_by('-booking_date', '-created_on')[:200]:
            bookings.append({
                'id': str(b.id),
                'code': getattr(b, 'code', None),
                'customer_name': b.customer_name,
                'customer_mobile': b.customer_mobile,
                'project_name': b.project.name if b.project_id else None,
                'unit_type': b.unit_type,
                'unit_number': b.unit_number,
                'agreed_price': float(b.agreed_price) if b.agreed_price is not None else None,
                'booking_amount': float(b.booking_amount) if b.booking_amount is not None else None,
                'revenue': float(b.revenue) if b.revenue is not None else None,
                'incentive': float(b.incentive) if b.incentive is not None else None,
                'status': b.status,
                'status_label': status_labels.get(b.status, b.status),
                'booking_date': b.booking_date.isoformat() if b.booking_date else None,
            })

        return Response({
            'profile': profile,
            'period': period,
            'period_range': {
                'start': start_date.isoformat() if start_date else None,
                'end': end_date.isoformat() if end_date else None,
            },
            'summary': summary,
            'bookings': bookings,
            'is_admin_view': is_admin,
        })
