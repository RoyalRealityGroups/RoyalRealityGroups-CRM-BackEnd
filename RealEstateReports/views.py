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
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from django.utils import timezone
        from Lead.models import Lead
        from SiteVisit.models import SiteVisit
        from Booking.models import Booking
        from Users.models import User
        from django.db.models import Sum, Count
        from django.db.models import Q as models_Q

        today = timezone.now().date()
        user = request.user

        lead_qs = Lead.objects.filter(is_deleted=False)
        sv_qs = SiteVisit.objects.filter(is_deleted=False)
        bkg_qs = Booking.objects.filter(is_deleted=False)
        active_bkg = bkg_qs.exclude(status='CANCELLED')

        # Employee performance (top performers)
        employees = User.objects.filter(is_active=True, is_superuser=False)[:20]
        employee_performance = []
        for emp in employees:
            leads = lead_qs.filter(assigned_employee=emp).count()
            visits = sv_qs.filter(assigned_employee=emp).count()
            bookings = active_bkg.filter(sales_executive=emp).count()
            registrations = bkg_qs.filter(sales_executive=emp, status='REGISTERED').count()
            if leads > 0 or visits > 0 or bookings > 0:
                employee_performance.append({
                    'employee_id': str(emp.id),
                    'employee_name': f"{emp.first_name} {emp.last_name}".strip() or emp.username,
                    'designation': getattr(emp, 'designation', None),
                    'leads': leads,
                    'site_visits': visits,
                    'bookings': bookings,
                    'registrations': registrations,
                })
        employee_performance.sort(key=lambda x: x['bookings'], reverse=True)

        # Project performance
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

        # Monthly trend (last 6 months)
        from django.db.models.functions import TruncMonth
        from datetime import timedelta
        six_months_ago = today - timedelta(days=180)

        monthly_leads = list(
            lead_qs.filter(created_on__date__gte=six_months_ago)
            .annotate(month=TruncMonth('created_on'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )
        monthly_bookings = list(
            active_bkg.filter(booking_date__gte=six_months_ago)
            .annotate(month=TruncMonth('booking_date'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )
        monthly_visits = list(
            sv_qs.filter(visit_date__gte=six_months_ago)
            .annotate(month=TruncMonth('visit_date'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )

        # Merge into single trend array
        months_map = {}
        for row in monthly_leads:
            key = row['month'].strftime('%b %Y')
            months_map.setdefault(key, {'month': key, 'leads': 0, 'site_visits': 0, 'bookings': 0})
            months_map[key]['leads'] = row['count']
        for row in monthly_visits:
            key = row['month'].strftime('%b %Y')
            months_map.setdefault(key, {'month': key, 'leads': 0, 'site_visits': 0, 'bookings': 0})
            months_map[key]['site_visits'] = row['count']
        for row in monthly_bookings:
            key = row['month'].strftime('%b %Y')
            months_map.setdefault(key, {'month': key, 'leads': 0, 'site_visits': 0, 'bookings': 0})
            months_map[key]['bookings'] = row['count']

        monthly_trend = sorted(months_map.values(), key=lambda x: x['month'])

        return Response({
            'leads': {
                'total': lead_qs.count(),
                'today': lead_qs.filter(created_on__date=today).count(),
                'this_month': lead_qs.filter(
                    created_on__year=today.year,
                    created_on__month=today.month
                ).count(),
            },
            'site_visits': {
                'total': sv_qs.count(),
                'today': sv_qs.filter(visit_date=today).count(),
                'completed': sv_qs.filter(status='COMPLETED').count(),
                'scheduled': sv_qs.filter(status='SCHEDULED').count(),
            },
            'bookings': {
                'total': active_bkg.count(),
                'this_month': active_bkg.filter(
                    booking_date__year=today.year,
                    booking_date__month=today.month
                ).count(),
            },
            'registrations': {
                'total': bkg_qs.filter(status='REGISTERED').count(),
            },
            'revenue': {
                'total': float(active_bkg.aggregate(t=Sum('agreed_price'))['t'] or 0),
                'this_month': float(
                    active_bkg.filter(
                        booking_date__year=today.year,
                        booking_date__month=today.month
                    ).aggregate(t=Sum('agreed_price'))['t'] or 0
                ),
            },
            'employee_performance': employee_performance[:10],
            'project_performance': project_performance,
            'monthly_trend': monthly_trend,
        })
