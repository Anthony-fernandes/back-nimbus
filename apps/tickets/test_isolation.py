"""
Tests that verify multi-tenant data isolation — no company can see another's data.
"""
import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


def make_token(user):
    return str(RefreshToken.for_user(user).access_token)


class MultiTenantIsolationTest(TestCase):
    """Verify that data from company A is never accessible to company B."""

    def setUp(self):
        from apps.companies.models import Company
        from apps.users.models import User

        self.company_a = Company.objects.create(name="Company A")
        self.company_b = Company.objects.create(name="Company B")

        self.user_a = User.objects.create_user(
            username="user_a", password="pass123", company=self.company_a, role="ADMIN"
        )
        self.user_b = User.objects.create_user(
            username="user_b", password="pass123", company=self.company_b, role="ADMIN"
        )

        self.client_a = APIClient()
        self.client_a.credentials(HTTP_AUTHORIZATION=f"Bearer {make_token(self.user_a)}")

        self.client_b = APIClient()
        self.client_b.credentials(HTTP_AUTHORIZATION=f"Bearer {make_token(self.user_b)}")

    def _create_ticket(self, company, user):
        from apps.tickets.models import Ticket
        return Ticket.objects.create(
            company=company,
            title="Test ticket",
            status="Aberto",
            priority="Media",
            requester_user=user,
            requester=user.username,
        )

    def test_ticket_list_isolation(self):
        """User A cannot see User B's tickets in the list."""
        ticket_b = self._create_ticket(self.company_b, self.user_b)
        resp = self.client_a.get("/api/tickets/")
        self.assertEqual(resp.status_code, 200)
        ids = [t["id"] for t in resp.data.get("results", resp.data)]
        self.assertNotIn(str(ticket_b.id), ids)

    def test_ticket_detail_isolation(self):
        """User A cannot retrieve User B's ticket by ID."""
        ticket_b = self._create_ticket(self.company_b, self.user_b)
        resp = self.client_a.get(f"/api/tickets/{ticket_b.id}/")
        self.assertIn(resp.status_code, [403, 404])

    def test_ticket_update_isolation(self):
        """User A cannot update User B's ticket."""
        ticket_b = self._create_ticket(self.company_b, self.user_b)
        resp = self.client_a.patch(f"/api/tickets/{ticket_b.id}/", {"title": "Hacked"})
        self.assertIn(resp.status_code, [403, 404])

    def test_ticket_delete_isolation(self):
        """User A cannot delete User B's ticket."""
        ticket_b = self._create_ticket(self.company_b, self.user_b)
        resp = self.client_a.delete(f"/api/tickets/{ticket_b.id}/")
        self.assertIn(resp.status_code, [403, 404])

    def test_project_list_isolation(self):
        """User A cannot see User B's projects."""
        from apps.projects.models import Project
        project_b = Project.objects.create(company=self.company_b, name="Project B")
        resp = self.client_a.get("/api/projects/")
        self.assertEqual(resp.status_code, 200)
        ids = [p["id"] for p in resp.data.get("results", resp.data)]
        self.assertNotIn(str(project_b.id), ids)

    def test_unauthenticated_access_denied(self):
        """Unauthenticated requests are rejected."""
        ticket_a = self._create_ticket(self.company_a, self.user_a)
        resp = self.client.get(f"/api/tickets/{ticket_a.id}/")
        self.assertEqual(resp.status_code, 401)
