from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from Masters.models import Project, ProjectStatusHistory

User = get_user_model()


class ProjectModelTests(TestCase):
    """Model-level tests for Project — SRS Module 6."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass123', email='t@example.com',
        )

    def test_create_project_assigns_code(self):
        proj = Project.objects.create(
            name='Sunrise Heights',
            developer_name='Acme Builders',
            project_type='PLOT',
            approval_type='GVMC',
            status='UPCOMING',
            created_by_identifier=str(self.user.id),
        )
        self.assertTrue(proj.code.startswith('PROJ'))
        self.assertEqual(proj.status, 'UPCOMING')
        self.assertFalse(proj.is_deleted)

    def test_default_status_is_upcoming(self):
        proj = Project.objects.create(name='X')
        self.assertEqual(proj.status, 'UPCOMING')

    def test_soft_delete_flips_flag(self):
        proj = Project.objects.create(name='Y')
        proj.delete()  # overridden to soft-delete
        proj.refresh_from_db()
        self.assertTrue(proj.is_deleted)
        # Hard delete still works for cleanup paths
        proj.hard_delete()
        self.assertFalse(Project.objects.filter(pk=proj.pk).exists())

    def test_status_transition_writes_history(self):
        proj = Project.objects.create(
            name='Z',
            status='UPCOMING',
            created_by_identifier=str(self.user.id),
        )
        # No history yet beyond the creation row
        self.assertEqual(proj.status_history.count(), 1)

        proj.status = 'ACTIVE'
        proj.save()

        self.assertEqual(proj.status_history.count(), 2)
        latest = proj.status_history.first()
        self.assertEqual(latest.from_status, 'UPCOMING')
        self.assertEqual(latest.to_status, 'ACTIVE')

    def test_str_representation(self):
        proj = Project.objects.create(name='Sample')
        self.assertIn('Sample', str(proj))


class ProjectAPITests(TestCase):
    """Endpoint-level tests for /api/masters/projects/."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='apiuser', password='apipass123',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_requires_auth(self):
        anon = APIClient()
        resp = anon.get('/api/masters/projects/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_then_list(self):
        payload = {
            'name': 'API Project',
            'developer_name': 'Dev Co',
            'project_type': 'FLAT',
            'approval_type': 'VMRDA',
            'status': 'UPCOMING',
            'is_active': True,
        }
        resp = self.client.post('/api/masters/projects/', payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertIn('code', resp.data)
        self.assertTrue(resp.data['code'].startswith('PROJ'))

        resp = self.client.get('/api/masters/projects/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(resp.data['count'], 1)

    def test_soft_delete_via_api(self):
        proj = Project.objects.create(
            name='Delete Me',
            created_by_identifier=str(self.user.id),
        )
        resp = self.client.delete(f'/api/masters/projects/{proj.id}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        proj.refresh_from_db()
        self.assertTrue(proj.is_deleted)

        # Hidden from default list
        resp = self.client.get('/api/masters/projects/')
        ids = [r['id'] for r in resp.data['results']]
        self.assertNotIn(str(proj.id), ids)

    def test_choices_endpoint(self):
        resp = self.client.get('/api/masters/projects/choices/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('project_statuses', resp.data)
        self.assertIn('project_types', resp.data)
        self.assertIn('approval_types', resp.data)

    def test_mini_endpoint_excludes_soft_deleted(self):
        Project.objects.create(name='Active One', is_active=True)
        deleted = Project.objects.create(name='Deleted One', is_active=True)
        deleted.delete()  # soft-delete
        deleted.save()

        resp = self.client.get('/api/masters/projects/mini/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        names = [p['name'] for p in resp.data]
        self.assertIn('Active One', names)
        self.assertNotIn('Deleted One', names)