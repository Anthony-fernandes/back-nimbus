"""Regras do chat: tenant, participantes, dedupe, suporte, leitura."""
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.clients.models import Client
from apps.companies.models import Company
from apps.communication.models import ChatConversation, ChatMessage
from apps.communication.views import ChatConversationViewSet
from apps.users.models import User


class ChatRulesTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.company = Company.objects.create(name="Chat Co")
        self.other_company = Company.objects.create(name="Outra Co")
        self.org = Client.objects.create(company=self.company, name="Org")
        self.tech = User.objects.create_user(
            username="tec@chat.co", email="tec@chat.co", password="x",
            company=self.company, role="TECHNICIAN",
        )
        self.tech2 = User.objects.create_user(
            username="tec2@chat.co", email="tec2@chat.co", password="x",
            company=self.company, role="TECHNICIAN",
        )
        self.outsider = User.objects.create_user(
            username="fora@outra.co", email="fora@outra.co", password="x",
            company=self.other_company, role="TECHNICIAN",
        )
        self.client_user = User.objects.create_user(
            username="cli@chat.co", email="cli@chat.co", password="x",
            company=self.company, role="CLIENT", client=self.org,
        )

    @staticmethod
    def _rows(listing):
        data = listing.data
        if isinstance(data, dict):
            return data.get("results", [])
        return data

    def _call(self, user, method, url, payload=None, actions=None, pk=None):
        req = getattr(self.factory, method)(url, payload or {}, format="json")
        force_authenticate(req, user)
        view = ChatConversationViewSet.as_view(actions)
        return view(req, pk=pk) if pk else view(req)

    def test_participants_outside_tenant_are_rejected(self):
        resp = self._call(self.tech, "post", "/api/communication/chat-conversations/",
                          {"tipo": "direto", "participants": [str(self.outsider.id)]},
                          {"post": "create"})
        self.assertEqual(resp.status_code, 400)

    def test_self_only_conversation_rejected(self):
        resp = self._call(self.tech, "post", "/api/communication/chat-conversations/",
                          {"tipo": "direto", "participants": [str(self.tech.id)]},
                          {"post": "create"})
        self.assertEqual(resp.status_code, 400)

    def test_direct_conversation_dedupe(self):
        r1 = self._call(self.tech, "post", "/api/communication/chat-conversations/",
                        {"tipo": "direto", "participants": [str(self.tech2.id)]},
                        {"post": "create"})
        self.assertEqual(r1.status_code, 201)
        r2 = self._call(self.tech, "post", "/api/communication/chat-conversations/",
                        {"tipo": "direto", "participants": [str(self.tech2.id)]},
                        {"post": "create"})
        self.assertEqual(r2.status_code, 200)
        self.assertTrue(r2.data.get("duplicate"))
        self.assertEqual(r1.data["id"], r2.data["id"])

    def test_client_cannot_create_direct_conversation(self):
        resp = self._call(self.client_user, "post", "/api/communication/chat-conversations/",
                          {"tipo": "direto", "participants": [str(self.tech.id)]},
                          {"post": "create"})
        self.assertEqual(resp.status_code, 403)

    def test_client_start_support_and_technician_assumes(self):
        resp = self._call(self.client_user, "post",
                          "/api/communication/chat-conversations/start-support/",
                          {"initial_message": "Preciso de ajuda"},
                          {"post": "start_support"})
        self.assertEqual(resp.status_code, 201)
        conv_id = resp.data["id"]
        self.assertEqual(resp.data["tipo"], "suporte")
        self.assertEqual(resp.data["status"], "aguardando_atendente")

        # Novo start-support reaproveita a conversa aberta
        again = self._call(self.client_user, "post",
                           "/api/communication/chat-conversations/start-support/", {},
                           {"post": "start_support"})
        self.assertEqual(again.status_code, 200)
        self.assertTrue(again.data.get("duplicate"))

        # Técnico vê a fila mesmo sem participar e assume
        listing = self._call(self.tech, "get", "/api/communication/chat-conversations/",
                             None, {"get": "list"})
        ids = [c["id"] for c in self._rows(listing)]
        self.assertIn(conv_id, ids)

        assumed = self._call(self.tech, "post", f"/x/{conv_id}/assume/", {},
                             {"post": "assume"}, pk=conv_id)
        self.assertEqual(assumed.status_code, 200)
        self.assertEqual(assumed.data["status"], "em_atendimento")
        self.assertEqual(assumed.data["assigned_to_name"], self.tech.full_name_or_username)

        # Segundo técnico não assume sem force
        blocked = self._call(self.tech2, "post", f"/x/{conv_id}/assume/", {},
                             {"post": "assume"}, pk=conv_id)
        self.assertEqual(blocked.status_code, 400)

    def test_mark_read_bulk_clears_unread(self):
        conv = ChatConversation.objects.create(company=self.company, tipo="direto", created_by=self.tech)
        conv.participants.add(self.tech, self.tech2)
        for i in range(3):
            ChatMessage.objects.create(conversation=conv, author=self.tech, content=f"m{i}")
        listing = self._call(self.tech2, "get", "/api/communication/chat-conversations/",
                             None, {"get": "list"})
        row = next(c for c in self._rows(listing) if c["id"] == str(conv.id))
        self.assertEqual(row["unread_count"], 3)

        self._call(self.tech2, "post", f"/x/{conv.id}/mark-read/", {},
                   {"post": "mark_read"}, pk=str(conv.id))
        listing = self._call(self.tech2, "get", "/api/communication/chat-conversations/",
                             None, {"get": "list"})
        row = next(c for c in self._rows(listing) if c["id"] == str(conv.id))
        self.assertEqual(row["unread_count"], 0)

    def test_client_does_not_see_internal_conversations(self):
        conv = ChatConversation.objects.create(company=self.company, tipo="direto", created_by=self.tech)
        conv.participants.add(self.tech, self.tech2)
        listing = self._call(self.client_user, "get", "/api/communication/chat-conversations/",
                             None, {"get": "list"})
        ids = [c["id"] for c in self._rows(listing)]
        self.assertNotIn(str(conv.id), ids)
