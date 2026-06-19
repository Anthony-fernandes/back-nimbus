from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.companies.models import Company
from apps.users.models import User
from apps.clients.models import Client
from apps.projects.models import Project, ProjectMember


def make_token(user):
    return str(RefreshToken.for_user(user).access_token)


class ProjectCreationTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Test Company")
        self.client_obj = Client.objects.create(company=self.company, name="Test Client")
        self.user = User.objects.create_user(
            username="proj_user", password="pass123", company=self.company, role="ADMIN"
        )
        self.api_client = APIClient()
        self.api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {make_token(self.user)}")

    def test_project_creation_by_authenticated_user(self):
        resp = self.api_client.post("/api/projects/", {
            "name": "New Project",
            "client": str(self.client_obj.id),
            "status": "Planejado",
        })
        self.assertIn(resp.status_code, [200, 201])
        self.assertEqual(resp.data["name"], "New Project")

    def test_unauthenticated_cannot_create_project(self):
        anon = APIClient()
        resp = anon.post("/api/projects/", {"name": "Hack", "client": str(self.client_obj.id)})
        self.assertEqual(resp.status_code, 401)


class ProjectIsolationTest(TestCase):
    def setUp(self):
        self.company_a = Company.objects.create(name="Company A")
        self.company_b = Company.objects.create(name="Company B")
        self.client_a = Client.objects.create(company=self.company_a, name="Client A")
        self.client_b = Client.objects.create(company=self.company_b, name="Client B")

        self.user_a = User.objects.create_user(
            username="user_a", password="pass123", company=self.company_a, role="ADMIN"
        )
        self.user_b = User.objects.create_user(
            username="user_b", password="pass123", company=self.company_b, role="ADMIN"
        )

        self.project_b = Project.objects.create(
            company=self.company_b, client=self.client_b, name="Secret Project B"
        )

        self.api_a = APIClient()
        self.api_a.credentials(HTTP_AUTHORIZATION=f"Bearer {make_token(self.user_a)}")

    def test_project_list_isolation(self):
        resp = self.api_a.get("/api/projects/")
        self.assertEqual(resp.status_code, 200)
        ids = [str(p["id"]) for p in resp.data.get("results", resp.data)]
        self.assertNotIn(str(self.project_b.id), ids)

    def test_project_detail_isolation(self):
        resp = self.api_a.get(f"/api/projects/{self.project_b.id}/")
        self.assertIn(resp.status_code, [403, 404])


class ProjectMemberManagementTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Dev Co")
        self.client_obj = Client.objects.create(company=self.company, name="Client X")
        self.admin = User.objects.create_user(
            username="admin", password="pass123", company=self.company, role="ADMIN"
        )
        self.member = User.objects.create_user(
            username="dev", password="pass123", company=self.company, role="TECHNICIAN"
        )
        self.project = Project.objects.create(
            company=self.company, client=self.client_obj, name="Member Test Project"
        )

    def test_add_project_member(self):
        pm = ProjectMember.objects.create(
            company=self.company,
            project=self.project,
            user=self.member,
            role="DESENVOLVEDOR",
        )
        self.assertEqual(pm.project, self.project)
        self.assertEqual(pm.user, self.member)
        self.assertTrue(pm.active)

    def test_remove_project_member(self):
        pm = ProjectMember.objects.create(
            company=self.company,
            project=self.project,
            user=self.member,
            role="DESENVOLVEDOR",
        )
        pm_id = pm.id
        pm.delete()
        self.assertFalse(ProjectMember.objects.filter(id=pm_id).exists())

    def test_project_member_unique_constraint(self):
        ProjectMember.objects.create(
            company=self.company, project=self.project, user=self.member, role="DESENVOLVEDOR"
        )
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            ProjectMember.objects.create(
                company=self.company, project=self.project, user=self.member, role="TESTER"
            )
