from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.utils import timezone

from .models import SiteVisit, SiteVisitPhoto, CalendarTodo, SITE_VISIT_STATUS_TRANSITIONS
from .serializers import SiteVisitSerializer, SiteVisitPhotoSerializer, SITE_VISIT_STATUS_CHOICES_LIST


class SiteVisitViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Site Visit Management - Module 5.

    Schedule Site Visit: customer_name, project, visit_date, assigned_employee
    Status: Scheduled → Confirmed → Completed / Cancelled
    Completion Details: customer_feedback, remarks, photos
    """
    queryset = SiteVisit.objects.select_related(
        'lead', 'project', 'assigned_employee'
    ).filter(is_deleted=False)
    serializer_class = SiteVisitSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'project', 'assigned_employee', 'lead']
    search_fields = ['customer_name', 'project_name', 'code']
    ordering_fields = ['visit_date', 'created_on']
    ordering = ['-visit_date']
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        from utils import apply_data_scope
        qs = super().get_queryset()
        # Apply data scope first
        qs = apply_data_scope(qs, self.request.user, 'sitevisit', employee_field='assigned_employee')
        # Then apply date filters
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        if from_date:
            qs = qs.filter(visit_date__gte=from_date)
        if to_date:
            qs = qs.filter(visit_date__lte=to_date)
        return qs

    # Lead status sync mapping
    LEAD_STATUS_BY_VISIT = {
        'SCHEDULED': 'SITE_VISIT_SCHEDULED',
        'CONFIRMED': 'SITE_VISIT_SCHEDULED',
        'COMPLETED': 'SITE_VISIT_COMPLETED',
        'CANCELLED': None,
    }

    def _sync_lead_status(self, site_visit):
        """Auto-update linked lead status based on visit status."""
        if not site_visit.lead_id:
            return
        target = self.LEAD_STATUS_BY_VISIT.get(site_visit.status)
        if not target:
            return
        if site_visit.lead.status == target:
            return
        site_visit.lead.status = target
        site_visit.lead.save(update_fields=['status', 'modified_on'])

    def perform_create(self, serializer):
        instance = serializer.save()
        self._handle_photos(instance)
        self._sync_lead_status(instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        self._handle_photos(instance)
        self._sync_lead_status(instance)

    def _handle_photos(self, instance):
        """Save uploaded photo files as SiteVisitPhoto records."""
        files = self.request.FILES.getlist("photos")
        if not files:
            return
        for photo in files:
            SiteVisitPhoto.objects.create(
                site_visit=instance,
                photo=photo,
            )

    @action(detail=True, methods=['post'])
    def upload_photos(self, request, pk=None):
        """Upload photos for a site visit (typically on completion)."""
        site_visit = self.get_object()
        photos = request.FILES.getlist('photos')
        if not photos:
            return Response({'error': 'No photos provided'}, status=status.HTTP_400_BAD_REQUEST)

        created = []
        for photo in photos:
            obj = SiteVisitPhoto.objects.create(
                site_visit=site_visit,
                photo=photo,
                caption=request.data.get('caption', ''),
            )
            created.append(SiteVisitPhotoSerializer(obj).data)

        return Response({'photos': created, 'count': len(created)}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def delete_photo(self, request, pk=None):
        """Delete a specific photo from a site visit."""
        site_visit = self.get_object()
        photo_id = request.data.get('photo_id')
        if not photo_id:
            return Response({'error': 'photo_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            photo = site_visit.photos.get(id=photo_id)
            photo.delete()
            return Response({'message': 'Photo deleted'}, status=status.HTTP_200_OK)
        except SiteVisitPhoto.DoesNotExist:
            return Response({'error': 'Photo not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update site visit status with optional completion details."""
        sv = self.get_object()
        new_status = request.data.get('status')
        if not new_status:
            return Response({'error': 'status is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate transition
        allowed = SITE_VISIT_STATUS_TRANSITIONS.get(sv.status, set())
        if new_status != sv.status and new_status not in allowed:
            return Response(
                {'error': f'Cannot transition from {sv.status} to {new_status}. Allowed: {sorted(allowed) or "none (terminal)"}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        sv.status = new_status
        if new_status == 'COMPLETED':
            sv.customer_feedback = request.data.get('customer_feedback', sv.customer_feedback)
            sv.remarks = request.data.get('remarks', sv.remarks)
        sv.save()

        # Sync linked lead status
        self._sync_lead_status(sv)

        return Response(SiteVisitSerializer(sv, context={'request': request}).data)

    @action(detail=False, methods=['get'])
    def choices(self, request):
        """Return available status choices for dropdowns."""
        return Response({
            'statuses': SITE_VISIT_STATUS_CHOICES_LIST,
        })

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Site visit statistics for dashboard."""
        today = timezone.now().date()
        qs = SiteVisit.objects.filter(is_deleted=False)
        return Response({
            'total': qs.count(),
            'today': qs.filter(visit_date=today).count(),
            'scheduled': qs.filter(status='SCHEDULED').count(),
            'confirmed': qs.filter(status='CONFIRMED').count(),
            'completed': qs.filter(status='COMPLETED').count(),
            'cancelled': qs.filter(status='CANCELLED').count(),
        })

    @action(detail=False, methods=['get'])
    def calendar(self, request):
        """
        Calendar endpoint - returns site visits for a month with lead status for colour-coding.

        Query params:
          - month (int, required): 1-12
          - year (int, required): e.g. 2026
          - assigned_employee (uuid, optional): filter by employee
          - project (uuid, optional): filter by project
          - status (str, optional): filter by site visit status

        Returns flat list of events with colour classification:
          - RED: lead is LOST or site visit CANCELLED
          - YELLOW: site visit COMPLETED (but lead not yet converted)
          - GREEN: lead reached BOOKING or REGISTRATION (sale closed)
          - BLUE: CONFIRMED
          - ORANGE: SCHEDULED
        """
        import calendar as cal
        from datetime import date

        month = request.query_params.get('month')
        year = request.query_params.get('year')

        if not month or not year:
            return Response(
                {'error': 'month and year query params are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            month = int(month)
            year = int(year)
        except (ValueError, TypeError):
            return Response(
                {'error': 'month and year must be integers'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Calculate date range for the month
        _, last_day = cal.monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)

        qs = SiteVisit.objects.select_related(
            'lead', 'project', 'assigned_employee'
        ).filter(
            is_deleted=False,
            visit_date__gte=start_date,
            visit_date__lte=end_date,
        )

        # Apply data scope — same as list view
        user = request.user
        if not user.is_superuser and not user.is_staff:
            from django.db.models import Q
            scope = getattr(user, 'sitevisit_data_scope', 'OWN')
            if scope == 'OWN':
                qs = qs.filter(
                    Q(assigned_employee=user) |
                    Q(created_by_identifier=str(user.id))
                ).distinct()
            elif scope == 'TEAM':
                team_ids = {user.id}
                if hasattr(user, 'get_team_users'):
                    for m in user.get_team_users():
                        team_ids.add(m.id)
                team_id_strs = [str(uid) for uid in team_ids]
                qs = qs.filter(
                    Q(assigned_employee__in=team_ids) |
                    Q(created_by_identifier__in=team_id_strs)
                ).distinct()

        # Apply filters
        employee_id = request.query_params.get('assigned_employee')
        if employee_id:
            qs = qs.filter(assigned_employee_id=employee_id)

        project_id = request.query_params.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)

        sv_status = request.query_params.get('status')
        if sv_status:
            qs = qs.filter(status=sv_status)

        # Build calendar events
        events = []
        for sv in qs:
            # Determine colour based on lead status + visit status
            colour = self._get_calendar_colour(sv)
            emp = sv.assigned_employee
            emp_name = ''
            if emp:
                emp_name = f"{emp.first_name} {emp.last_name}".strip() or emp.username

            events.append({
                'id': str(sv.id),
                'code': sv.code,
                'customer_name': sv.customer_name,
                'project_name': sv.project_name or (sv.project.name if sv.project else ''),
                'project_id': str(sv.project_id) if sv.project_id else None,
                'visit_date': sv.visit_date.isoformat(),
                'assigned_employee_id': str(sv.assigned_employee_id) if sv.assigned_employee_id else None,
                'assigned_employee_name': emp_name,
                'status': sv.status,
                'status_display': sv.get_status_display(),
                'lead_id': str(sv.lead_id) if sv.lead_id else None,
                'lead_status': sv.lead.status if sv.lead else None,
                'colour': colour,
                'remarks': sv.remarks or '',
            })

        # Summary counts for the sidebar
        all_visits = SiteVisit.objects.filter(
            is_deleted=False,
            visit_date__gte=start_date,
            visit_date__lte=end_date,
        )
        if employee_id:
            all_visits = all_visits.filter(assigned_employee_id=employee_id)
        if project_id:
            all_visits = all_visits.filter(project_id=project_id)

        summary = {
            'total': all_visits.count(),
            'scheduled': all_visits.filter(status='SCHEDULED').count(),
            'confirmed': all_visits.filter(status='CONFIRMED').count(),
            'completed': all_visits.filter(status='COMPLETED').count(),
            'cancelled': all_visits.filter(status='CANCELLED').count(),
        }

        return Response({
            'month': month,
            'year': year,
            'events': events,
            'summary': summary,
        })

    def _get_calendar_colour(self, site_visit):
        """
        Determine colour code for a site visit on the calendar.
        RED: Lead LOST or visit CANCELLED
        GREEN: Lead reached BOOKING/REGISTRATION (sale closed)
        YELLOW: Visit COMPLETED but lead not yet converted
        BLUE: Visit CONFIRMED
        ORANGE: Visit SCHEDULED
        """
        # If visit is cancelled or lead is lost → RED
        if site_visit.status == 'CANCELLED':
            return 'RED'
        if site_visit.lead and site_visit.lead.status == 'LOST':
            return 'RED'

        # If lead has reached booking/registration → GREEN
        if site_visit.lead and site_visit.lead.status in ('BOOKING', 'REGISTRATION'):
            return 'GREEN'

        # Visit completed but lead not yet at booking → YELLOW
        if site_visit.status == 'COMPLETED':
            return 'YELLOW'

        # Confirmed → BLUE
        if site_visit.status == 'CONFIRMED':
            return 'BLUE'

        # Scheduled → ORANGE
        return 'ORANGE'

    @action(detail=False, methods=['get'])
    def export(self, request):
        from django.http import HttpResponse
        from rest_framework.exceptions import PermissionDenied
        from RealEstateReports.services import export_to_excel, export_to_pdf

        # Check export permission
        if not request.user.is_superuser and not request.user.has_perm('SiteVisit.export_sitevisit'):
            raise PermissionDenied('You do not have permission to export site visits.')

        export_format = request.query_params.get('export_type', 'excel')
        qs = self.filter_queryset(self.get_queryset())

        data = []
        for sv in qs[:5000]:
            emp = sv.assigned_employee
            emp_name = f"{emp.first_name} {emp.last_name}".strip() or emp.username if emp else '-'
            data.append({
                'code': sv.code or '',
                'customer_name': sv.customer_name,
                'project_name': sv.project_name or (sv.project.name if sv.project else '-'),
                'visit_date': sv.visit_date.strftime('%d-%b-%Y') if sv.visit_date else '-',
                'assigned_employee': emp_name,
                'status': sv.get_status_display(),
                'customer_feedback': sv.customer_feedback or '-',
                'remarks': sv.remarks or '-',
            })

        columns = [
            {'key': 'code', 'label': 'Code'},
            {'key': 'customer_name', 'label': 'Customer Name'},
            {'key': 'project_name', 'label': 'Project'},
            {'key': 'visit_date', 'label': 'Visit Date'},
            {'key': 'assigned_employee', 'label': 'Assigned To'},
            {'key': 'status', 'label': 'Status'},
            {'key': 'customer_feedback', 'label': 'Feedback'},
            {'key': 'remarks', 'label': 'Remarks'},
        ]

        if export_format == 'pdf':
            content = export_to_pdf(data, columns, 'Site Visit Report')
            response = HttpResponse(content, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="SiteVisit_Report.pdf"'
            return response
        else:
            content = export_to_excel(data, columns, 'Site Visits')
            response = HttpResponse(content, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="SiteVisit_Report.xlsx"'
            return response


class CalendarTodoViewSet(viewsets.ModelViewSet):
    """
    Personal To-Do items for the Site Visit Calendar.
    Each user manages their own to-do list.

    GET /api/sitevisit/todos/?month=7&year=2026 → list todos for a month
    POST /api/sitevisit/todos/ → create a todo {date, title}
    PATCH /api/sitevisit/todos/{id}/ → toggle completion or update title
    DELETE /api/sitevisit/todos/{id}/ → remove a todo
    """
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        qs = CalendarTodo.objects.filter(user=self.request.user)
        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')
        if month and year:
            try:
                qs = qs.filter(date__month=int(month), date__year=int(year))
            except (ValueError, TypeError):
                pass
        return qs.order_by('date', 'created_on')

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        data = [
            {
                'id': t.id,
                'date': t.date.isoformat(),
                'title': t.title,
                'is_completed': t.is_completed,
            }
            for t in qs
        ]
        return Response(data)

    def create(self, request, *args, **kwargs):
        date_str = request.data.get('date')
        title = request.data.get('title', '').strip()
        if not date_str or not title:
            return Response(
                {'error': 'date and title are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from datetime import date as date_type
        try:
            todo_date = date_type.fromisoformat(date_str)
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        todo = CalendarTodo.objects.create(
            user=request.user,
            date=todo_date,
            title=title,
        )
        return Response(
            {'id': todo.id, 'date': todo.date.isoformat(), 'title': todo.title, 'is_completed': False},
            status=status.HTTP_201_CREATED,
        )

    def partial_update(self, request, *args, **kwargs):
        try:
            todo = CalendarTodo.objects.get(id=kwargs['pk'], user=request.user)
        except CalendarTodo.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        if 'is_completed' in request.data:
            todo.is_completed = request.data['is_completed']
        if 'title' in request.data:
            todo.title = request.data['title']
        todo.save()
        return Response(
            {'id': todo.id, 'date': todo.date.isoformat(), 'title': todo.title, 'is_completed': todo.is_completed}
        )

    def destroy(self, request, *args, **kwargs):
        try:
            todo = CalendarTodo.objects.get(id=kwargs['pk'], user=request.user)
        except CalendarTodo.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        todo.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
