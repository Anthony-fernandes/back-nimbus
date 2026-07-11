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


class CategoryRulesTest(TestCase):
    """Regras próprias da categoria: subcategoria/anexo obrigatórios e campos extras."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.company = Company.objects.create(name="Rules Co")
        self.org = Client.objects.create(company=self.company, name="Org")
        self.client_user = User.objects.create_user(
            username="cli@rules.co", email="cli@rules.co", password="x",
            company=self.company, role="CLIENT", client=self.org,
        )
        self.category = TicketCategory.objects.create(
            company=self.company, name="Erro no sistema",
            subcategories=["Erro visual", "Erro de dados"],
            subcategory_required=True, attachment_required=True,
        )

    def _create(self, payload):
        req = self.factory.post("/api/tickets/", payload, format="json")
        force_authenticate(req, self.client_user)
        return TicketViewSet.as_view({"post": "create"})(req)

    def _base(self, **extra):
        base = {"title": "x", "description": "d", "client": str(self.org.id),
                "category": "Erro no sistema", "urgency": "Média", "impact": "Baixo"}
        base.update(extra)
        return base

    def _detail(self, resp):
        return resp.data.get("error", {}).get("detail", resp.data)

    def test_category_requires_subcategory_and_attachment(self):
        resp = self._create(self._base())
        self.assertEqual(resp.status_code, 400)
        detail = self._detail(resp)
        self.assertIn("subcategory", detail)
        self.assertIn("attachments", detail)

        resp = self._create(self._base(subcategory="Erro visual", has_attachments=True))
        self.assertEqual(resp.status_code, 201, resp.data)

    def test_required_client_custom_field(self):
        from apps.tickets.models import TicketCustomField, TicketCustomValue
        field = TicketCustomField.objects.create(
            company=self.company, name="mensagem_erro", label="Mensagem de erro",
            field_type="text", required=True, visible_to_client=True, category=self.category,
        )
        resp = self._create(self._base(subcategory="Erro visual", has_attachments=True))
        self.assertEqual(resp.status_code, 400)
        self.assertIn(f"custom_values.{field.id}", self._detail(resp))

        resp = self._create(self._base(
            subcategory="Erro visual", has_attachments=True,
            custom_values={str(field.id): "ORA-00942"},
        ))
        self.assertEqual(resp.status_code, 201, resp.data)
        ticket = Ticket.objects.get(id=resp.data["id"])
        value = TicketCustomValue.objects.get(ticket=ticket, field=field)
        self.assertEqual(value.value, "ORA-00942")

    def test_custom_field_of_other_category_not_required(self):
        other = TicketCategory.objects.create(company=self.company, name="Acesso")
        from apps.tickets.models import TicketCustomField
        TicketCustomField.objects.create(
            company=self.company, name="modulo", label="Módulo desejado",
            field_type="text", required=True, visible_to_client=True, category=other,
        )
        resp = self._create(self._base(subcategory="Erro visual", has_attachments=True))
        self.assertEqual(resp.status_code, 201, resp.data)


class SLASubcategoryTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="SLA Sub Co")
        self.org = Client.objects.create(company=self.company, name="Org")

    def test_subcategory_policy_wins_over_category(self):
        from apps.tickets.models import SLAPolicy
        from apps.tickets.sla import compute_sla_due_at
        SLAPolicy.objects.create(company=self.company, name="Acesso geral", category="Acesso", response_time="8h")
        SLAPolicy.objects.create(
            company=self.company, name="Bloqueio", category="Acesso",
            subcategory="Bloqueio de usuário", response_time="1h",
        )
        t_generic = Ticket.objects.create(
            company=self.company, client=self.org, title="a", category="Acesso", priority="Media",
        )
        t_block = Ticket.objects.create(
            company=self.company, client=self.org, title="b", category="Acesso",
            subcategory="Bloqueio de usuário", priority="Media",
        )
        compute_sla_due_at(t_generic)
        compute_sla_due_at(t_block)
        self.assertLess(t_block.sla_due_at, t_generic.sla_due_at)

    def test_subcategory_policy_does_not_match_other_subcategory(self):
        from apps.tickets.models import SLAPolicy
        from apps.tickets.sla import compute_sla_due_at
        SLAPolicy.objects.create(
            company=self.company, name="Bloqueio", category="Acesso",
            subcategory="Bloqueio de usuário", response_time="1h",
        )
        t = Ticket.objects.create(
            company=self.company, client=self.org, title="a", category="Acesso",
            subcategory="Novo acesso", priority="Media", sla="8h",
        )
        compute_sla_due_at(t)
        other = Ticket.objects.create(
            company=self.company, client=self.org, title="b", category="Acesso",
            subcategory="Bloqueio de usuário", priority="Media", sla="8h",
        )
        compute_sla_due_at(other)
        self.assertLess(other.sla_due_at, t.sla_due_at)
