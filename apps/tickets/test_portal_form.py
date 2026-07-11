"""Testes do formulário configurável de abertura no Portal do Cliente.

Usam APIRequestFactory (o middleware depende de whitenoise/redis indisponíveis
no ambiente de testes).
"""
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.clients.models import Client
from apps.companies.models import Company
from apps.tickets.models import Ticket, TicketCategory, TicketPortalFormConfig
from apps.tickets.views import TicketPortalFormConfigView, TicketViewSet
from apps.users.models import Department, User


class PortalFormConfigTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.company = Company.objects.create(name="Portal Co")
        self.org = Client.objects.create(company=self.company, name="Org Cliente")
        self.admin = User.objects.create_user(
            username="admin@portal.co", email="admin@portal.co", password="x",
            company=self.company, role="ADMIN",
        )
        self.client_user = User.objects.create_user(
            username="cli@portal.co", email="cli@portal.co", password="x",
            company=self.company, role="CLIENT", client=self.org,
        )

    def _create(self, user, payload):
        req = self.factory.post("/api/tickets/", payload, format="json")
        force_authenticate(req, user)
        return TicketViewSet.as_view({"post": "create"})(req)

    def _config(self, fields):
        config, _ = TicketPortalFormConfig.objects.get_or_create(company=self.company)
        config.fields = fields
        config.save()

    def test_get_config_returns_defaults_and_catalogs(self):
        TicketCategory.objects.create(
            company=self.company, name="Sistema", subcategories=["Lentidão", "Erro de acesso"]
        )
        Department.objects.create(company=self.company, name="Financeiro", manager=self.admin)
        req = self.factory.get("/api/tickets/portal-form-config/")
        force_authenticate(req, self.client_user)
        resp = TicketPortalFormConfigView.as_view()(req)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data["fields"]["title"]["required"])
        self.assertEqual(resp.data["categories"][0]["subcategories"], ["Lentidão", "Erro de acesso"])
        self.assertEqual(resp.data["departments"][0]["manager_name"], self.admin.full_name_or_username)

    def test_put_config_requires_settings_edit(self):
        req = self.factory.put(
            "/api/tickets/portal-form-config/",
            {"fields": {"category": {"visible": True, "required": True}}},
            format="json",
        )
        force_authenticate(req, self.client_user)
        resp = TicketPortalFormConfigView.as_view()(req)
        self.assertEqual(resp.status_code, 403)

        force_authenticate(req, self.admin)
        resp = TicketPortalFormConfigView.as_view()(req)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data["fields"]["category"]["required"])

    def test_client_without_category_enters_triage_pending(self):
        resp = self._create(
            self.client_user,
            {"title": "Sem categoria", "description": "d", "client": str(self.org.id),
             "urgency": "Média", "impact": "Baixo", "status": "Aberto"},
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        ticket = Ticket.objects.get(id=resp.data["id"])
        self.assertEqual(ticket.status, "Triagem")
        self.assertEqual(ticket.category, "")
        self.assertEqual(ticket.source, "portal")
        self.assertTrue(resp.data["classification_pending"])

    def test_required_category_blocks_creation(self):
        self._config({"category": {"visible": True, "required": True}})
        resp = self._create(
            self.client_user,
            {"title": "x", "description": "d", "client": str(self.org.id),
             "urgency": "Média", "impact": "Baixo"},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("category", resp.data.get("error", {}).get("detail", resp.data))

    def test_hidden_field_cannot_be_sent(self):
        self._config({"affected_service": {"visible": False, "required": False}})
        resp = self._create(
            self.client_user,
            {"title": "x", "description": "d", "client": str(self.org.id),
             "urgency": "Média", "impact": "Baixo", "affected_service": "ERP"},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("affected_service", resp.data.get("error", {}).get("detail", resp.data))

    def test_internal_fields_are_stripped(self):
        tech = User.objects.create_user(
            username="tec@portal.co", email="tec@portal.co", password="x",
            company=self.company, role="TECHNICIAN",
        )
        resp = self._create(
            self.client_user,
            {"title": "x", "description": "d", "client": str(self.org.id),
             "urgency": "Média", "impact": "Baixo",
             "responsible_technician": str(tech.id), "sla": "1h"},
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        ticket = Ticket.objects.get(id=resp.data["id"])
        self.assertIsNone(ticket.responsible_technician_id)
        self.assertNotEqual(ticket.sla, "1h")

    def test_client_with_category_keeps_status(self):
        TicketCategory.objects.create(company=self.company, name="Acesso")
        resp = self._create(
            self.client_user,
            {"title": "x", "description": "d", "client": str(self.org.id),
             "category": "Acesso", "subcategory": "Bloqueio de usuário",
             "urgency": "Média", "impact": "Baixo", "status": "Aberto"},
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        ticket = Ticket.objects.get(id=resp.data["id"])
        self.assertEqual(ticket.status, "Aberto")
        self.assertEqual(ticket.subcategory, "Bloqueio de usuário")
        self.assertFalse(resp.data["classification_pending"])
