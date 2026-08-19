from django.db.models import Q
from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from ProjectManagement.models import Project, ProjectImage
from ProjectManagement.serializers import ProjectSerializer, ProjectImageSerializer, ProjectMiniSerializer


# ============================================================================
# PROJECT MASTER VIEWSETS — SRS Module 6
# ============================================================================

class ProjectList(generics.ListCreateAPIView):
    """List + Create Project."""
    serializer_class = ProjectSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'project_type', 'approval_type', 'is_active', 'location']
    search_fields = ['name', 'code', 'developer_name']
    ordering_fields = ['name', 'created_on', 'status']
    ordering = ['name']

    def get_queryset(self):
        user = self.request.user
        qs = Project.objects.filter(is_deleted=False).all()

        # Superuser/staff sees all projects
        if not user.is_superuser and not user.is_staff:
            qs = qs.filter(created_by_identifier=str(user.id))

        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        if from_date:
            qs = qs.filter(created_on__date__gte=from_date)
        if to_date:
            qs = qs.filter(created_on__date__lte=to_date)
        return qs


class ProjectExportView(APIView):
    """Export projects as Excel or PDF"""

    def get(self, request):
        from django.http import HttpResponse
        from rest_framework.exceptions import PermissionDenied
        from RealEstateReports.services import export_to_excel, export_to_pdf

        # Check export permission
        if not request.user.is_superuser and not request.user.has_perm('ProjectManagement.export_project'):
            raise PermissionDenied('You do not have permission to export projects.')

        export_format = request.query_params.get('export_type', 'excel')

        qs = Project.objects.filter(is_deleted=False)
        search = request.query_params.get('search')
        status_filter = request.query_params.get('status')
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')

        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(code__icontains=search) | Q(developer_name__icontains=search))
        if status_filter:
            qs = qs.filter(status=status_filter)
        if from_date:
            qs = qs.filter(created_on__date__gte=from_date)
        if to_date:
            qs = qs.filter(created_on__date__lte=to_date)

        data = []
        for proj in qs[:5000]:
            data.append({
                'code': proj.code or '',
                'name': proj.name,
                'developer_name': proj.developer_name or '-',
                'project_type': proj.get_project_type_display(),
                'location': proj.location or '-',
                'approval_type': proj.get_approval_type_display(),
                'status': proj.get_status_display(),
                'is_active': 'Yes' if proj.is_active else 'No',
            })

        columns = [
            {'key': 'code', 'label': 'Code'},
            {'key': 'name', 'label': 'Project Name'},
            {'key': 'developer_name', 'label': 'Developer'},
            {'key': 'project_type', 'label': 'Type'},
            {'key': 'location', 'label': 'Location'},
            {'key': 'approval_type', 'label': 'Approval'},
            {'key': 'status', 'label': 'Status'},
            {'key': 'is_active', 'label': 'Active'},
        ]

        if export_format == 'pdf':
            content = export_to_pdf(data, columns, 'Project Report')
            response = HttpResponse(content, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="Project_Report.pdf"'
            return response
        else:
            content = export_to_excel(data, columns, 'Projects')
            response = HttpResponse(
                content,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
            response['Content-Disposition'] = 'attachment; filename="Project_Report.xlsx"'
            return response


class ProjectDetail(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve / Update / Soft-delete Project."""
    serializer_class = ProjectSerializer
    lookup_field = 'pk'

    def get_queryset(self):
        return Project.objects.all()

    def perform_destroy(self, instance):
        # Soft delete: flip is_deleted, don't drop the row
        instance.delete()


class ProjectMini(generics.ListAPIView):
    """Minimal list for dropdowns. Excludes soft-deleted."""
    serializer_class = ProjectMiniSerializer
    pagination_class = None

    def get_queryset(self):
        return Project.objects.filter(is_deleted=False).order_by('name')


class ProjectChoices(APIView):
    """Return choice enums for Project form."""

    def get(self, request):
        return Response({
            'project_statuses': [{'value': k, 'label': v} for k, v in Project.PROJECT_STATUS_CHOICES],
            'project_types': [{'value': k, 'label': v} for k, v in Project.PROJECT_TYPE_CHOICES],
            'approval_types': [{'value': k, 'label': v} for k, v in Project.APPROVAL_TYPE_CHOICES],
        })


class ProjectImageList(generics.ListCreateAPIView):
    """List and create project images (gallery, floor plans, elevation)."""
    serializer_class = ProjectImageSerializer

    def get_queryset(self):
        project_id = self.kwargs.get('project_id')
        image_type = self.request.query_params.get('image_type')
        qs = ProjectImage.objects.filter(project_id=project_id)
        if image_type:
            qs = qs.filter(image_type=image_type)
        return qs.order_by('order', 'created_on')

    def perform_create(self, serializer):
        project_id = self.kwargs.get('project_id')
        serializer.save(project_id=project_id)


class ProjectImageDetail(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a project image."""
    serializer_class = ProjectImageSerializer
    queryset = ProjectImage.objects.all()


class ProjectImageUpload(APIView):
    """Bulk upload images for a project."""

    def post(self, request, project_id):
        project = Project.objects.filter(id=project_id, is_deleted=False).first()
        if not project:
            return Response({'detail': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

        image_type = request.data.get('image_type', 'GALLERY')
        images = request.FILES.getlist('images')

        if not images:
            return Response({'detail': 'No images provided'}, status=status.HTTP_400_BAD_REQUEST)

        created = []
        for idx, img in enumerate(images):
            proj_img = ProjectImage.objects.create(
                project=project,
                image=img,
                image_type=image_type,
                order=idx,
            )
            created.append(ProjectImageSerializer(proj_img, context={'request': request}).data)

        return Response({'created': created, 'count': len(created)}, status=status.HTTP_201_CREATED)
