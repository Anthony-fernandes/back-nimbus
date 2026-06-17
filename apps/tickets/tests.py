from django.test import TestCase
from django.utils import timezone

from apps.companies.models import Company
from apps.users.models import User
from apps.clients.models import Client
from apps.tickets.models import Ticket
from apps.tickets.sla import parse_sla_duration, compute_sla_due_at

from datetime import timedelta


def make_company(name="Acme"):
    return Company.objects.create(name=name)


def make_user(company, username="tech", role="TECHNICIAN"):
    return User.objects.create_user(
        username=username,
        password="testpass",
        company=company,
        role=role,
    )


def make_client(company):
    return Client.objects.create(company=company, name="Client Corp")


def make_ticket(company, client, user, **kwargs):
    return Ticket.objects.create(
        company=company,
        client=client,
        title=kwargs.get("title", "Test ticket"),
        priority=kwargs.get("priority", "Media"),
        status=kwargs.get("status", "Aberto"),
        requester="test",
        requester_user=user,
        **{k: v for k, v in kwargs.items() if k not in ("title", "priority", "status")},
    )


class ParseSLADurationTest(TestCase):
    def test_hours(self):
        self.assertEqual(parse_sla_duration("4h"), timedelta(hours=4))

    def test_days(self):
        self.assertEqual(parse_sla_duration("2d"), timedelta(days=2))

    def test_minutes(self):
        self.assertEqual(parse_sla_duration("30m"), timedelta(minutes=30))

    def test_invalid(self):
        self.assertIsNone(parse_sla_duration(""))
        self.assertIsNone(parse_sla_duration("xyz"))

    def test_case_insensitive(self):
        self.assertEqual(parse_sla_duration("8H"), timedelta(hours=8))


class TicketModelTest(TestCase):
    def setUp(self):
        self.company = make_company()
        self.user = make_user(self.company)
        self.client_obj = make_client(self.company)

    def test_code_auto_generated(self):
        ticket = make_ticket(self.company, self.client_obj, self.user)
        self.assertTrue(ticket.code.startswith("NIM-"))

    def test_code_unique(self):
        t1 = make_ticket(self.company, self.client_obj, self.user, title="T1")
        t2 = make_ticket(self.company, self.client_obj, self.user, title="T2")
        self.assertNotEqual(t1.code, t2.code)

    def test_default_status(self):
        ticket = make_ticket(self.company, self.client_obj, self.user)
        self.assertEqual(ticket.status, "Aberto")

    def test_default_priority(self):
        ticket = make_ticket(self.company, self.client_obj, self.user)
        self.assertEqual(ticket.priority, "Media")

    def test_rating_initially_null(self):
        ticket = make_ticket(self.company, self.client_obj, self.user)
        self.assertIsNone(ticket.rating)

    def test_sla_due_at_set_by_compute(self):
        ticket = make_ticket(self.company, self.client_obj, self.user, priority="Alta")
        before = timezone.now()
        compute_sla_due_at(ticket)
        after = timezone.now()
        self.assertIsNotNone(ticket.sla_due_at)
        # Alta = 4h default
        expected = before + timedelta(hours=4)
        self.assertAlmostEqual(
            ticket.sla_due_at.timestamp(),
            expected.timestamp(),
            delta=60,
        )


class TicketAPITest(TestCase):
    def setUp(self):
        self.company = make_company("APITest")
        self.user = make_user(self.company, username="apiuser", role="ADMIN")
        self.client_obj = make_client(self.company)
        self.client.force_login(self.user)

    def test_list_tickets_requires_auth(self):
        from django.test import Client as TestClient
        anon = TestClient()
        response = anon.get("/api/tickets/")
        self.assertEqual(response.status_code, 401)

    def test_create_ticket(self):
        from rest_framework.test import APIClient
        api = APIClient()
        api.force_authenticate(user=self.user)
        response = api.post("/api/tickets/", {
            "title": "API Test Ticket",
            "client": str(self.client_obj.id),
            "priority": "Media",
        }, format="json")
        self.assertIn(response.status_code, [200, 201])
        if response.status_code in [200, 201]:
            data = response.json()
            self.assertTrue(data.get("code", "").startswith("NIM-"))

    def test_rate_ticket_only_by_requester(self):
        from rest_framework.test import APIClient
        ticket = make_ticket(self.company, self.client_obj, self.user, status="Finalizado")
        other_user = make_user(self.company, username="other", role="TECHNICIAN")
        api = APIClient()
        api.force_authenticate(user=other_user)
        response = api.post(f"/api/tickets/{ticket.id}/rate/", {"rating": 5}, format="json")
        self.assertEqual(response.status_code, 403)


class KnowledgeArticleTest(TestCase):
    def setUp(self):
        self.company = make_company("KBTest")
        self.user = make_user(self.company, username="kbuser", role="ADMIN")

    def test_create_article(self):
        from apps.knowledge.models import KnowledgeArticle
        article = KnowledgeArticle.objects.create(
            company=self.company,
            title="Test Article",
            slug="test-article",
            content="Content here",
            author=self.user,
            status="DRAFT",
            visibility="INTERNAL",
        )
        self.assertEqual(article.status, "DRAFT")
        self.assertEqual(article.views_count, 0)


class SLAPolicyTest(TestCase):
    def setUp(self):
        self.company = make_company("SLATest")
        self.user = make_user(self.company, username="slauser", role="ADMIN")
        self.client_obj = make_client(self.company)

    def test_sla_policy_overrides_default(self):
        from apps.tickets.models import SLAPolicy
        SLAPolicy.objects.create(
            company=self.company,
            name="Critico 1h",
            priority="Critica",
            response_time="1h",
            priority_weight=10,
            active=True,
        )
        ticket = make_ticket(self.company, self.client_obj, self.user, priority="Critica")
        before = timezone.now()
        compute_sla_due_at(ticket)
        # Policy says 1h, default would be 2h
        expected_max = before + timedelta(hours=2)
        expected_min = before + timedelta(minutes=50)
        self.assertGreater(ticket.sla_due_at, expected_min)
        self.assertLess(ticket.sla_due_at, expected_max)
