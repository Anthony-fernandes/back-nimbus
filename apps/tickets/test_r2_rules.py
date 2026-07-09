"""
Testes das regras críticas consolidadas na rodada R2.
Usam APIRequestFactory (sem passar pelo middleware, que depende de whitenoise
não instalado neste ambiente) para exercitar viewsets/regras diretamente.

Rodar: DEBUG=True SECRET_KEY=dev python manage.py test apps.tickets.test_r2_rules
"""
from datetime import date, timedelta

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.request import Request

from apps.companies.models import Company
from apps.users.models import User
from apps.tickets.models import Ticket
from apps.activities.models import Activity
from apps.projects.models import Project
from apps.sprints.models import Sprint, SprintActivityPlan
from apps.knowledge.models import KnowledgeArticle
from apps.communication.models import ForumTopic, ForumCategory
from common.status_rules import validate_ticket_update
from apps.sprints.views import SprintActivityPlanViewSet
from apps.knowledge.views import KnowledgeArticleViewSet
from apps.communication.views import ForumTopicViewSet, ChatConversationViewSet
from apps.communication.models import ChatConversation


class R2Base(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.company = Company.objects.create(name="ACME R2")
        self.admin = User.objects.create(username="r2admin", role="ADMIN", company=self.company)
        self.tech = User.objects.create(username="r2tech", role="TECHNICIAN", company=self.company)
        self.client_user = User.objects.create(username="r2client", role="CLIENT", company=self.company)

    def _auth(self, method, user, data=None):
        req = getattr(self.factory, method)("/", data or {}, format="json")
        force_authenticate(req, user)
        return req


class TicketFlowRules(R2Base):
    def test_ticket_without_technician_cannot_start(self):
        t = Ticket.objects.create(company=self.company, title="X", status="Aguardando atendimento")
        with self.assertRaises(Exception):
            validate_ticket_update(t, {"status": "Em atendimento"})

    def test_ticket_with_technician_can_start(self):
        t = Ticket.objects.create(company=self.company, title="X", status="Aguardando atendimento",
                                  responsible_technician=self.tech)
        # não deve levantar
        validate_ticket_update(t, {"status": "Em atendimento"})


class SprintRules(R2Base):
    def _plan_view(self, user, ticket=None, activity=None, sprint=None):
        req = self._auth("post", user, {
            "sprint": str(sprint.id), "activity": str(activity.id) if activity else None,
            "planned_hours": 4,
        })
        return SprintActivityPlanViewSet.as_view({"post": "create"})(req)

    def test_finished_sprint_rejects_planning(self):
        self.admin.granted_permissions = {"sprints.edit": True, "sprints.manage": True}
        self.admin.save()
        sprint = Sprint.objects.create(company=self.company, name="S1", status="Finalizada")
        act = Activity.objects.create(company=self.company, title="A", status="Backlog")
        resp = self._plan_view(self.admin, activity=act, sprint=sprint)
        self.assertEqual(resp.status_code, 400)

    def test_backlog_activity_promoted_to_todo_on_plan(self):
        self.admin.granted_permissions = {"sprints.edit": True, "sprints.manage": True}
        self.admin.save()
        sprint = Sprint.objects.create(company=self.company, name="S2", status="Em andamento")
        act = Activity.objects.create(company=self.company, title="A", status="Backlog")
        resp = self._plan_view(self.admin, activity=act, sprint=sprint)
        self.assertEqual(resp.status_code, 201)
        act.refresh_from_db()
        self.assertEqual(act.status, "A fazer")
        self.assertEqual(act.sprint_id, sprint.id)


class KnowledgeIsolation(R2Base):
    def test_client_sees_only_published_public(self):
        KnowledgeArticle.objects.create(company=self.company, title="Interno", status="PUBLISHED", visibility="INTERNAL")
        KnowledgeArticle.objects.create(company=self.company, title="Rascunho", status="DRAFT", visibility="PUBLIC")
        pub = KnowledgeArticle.objects.create(company=self.company, title="Público", status="PUBLISHED", visibility="PUBLIC")
        req = Request(self._auth("get", self.client_user))
        req.user = self.client_user
        view = KnowledgeArticleViewSet()
        view.request = req
        view.format_kwarg = None
        ids = set(view.get_queryset().values_list("id", flat=True))
        self.assertEqual(ids, {pub.id})


class ForumIsolation(R2Base):
    def test_client_does_not_see_internal_topics(self):
        cat = ForumCategory.objects.create(company=self.company, name="Geral")
        interno = ForumTopic.objects.create(company=self.company, category=cat, title="Interno", visibility="interna")
        publico = ForumTopic.objects.create(company=self.company, category=cat, title="Público", visibility="todos")
        req = self._auth("get", self.client_user)
        req.user = self.client_user
        view = ForumTopicViewSet()
        view.request = req
        view.format_kwarg = None
        ids = set(view.get_queryset().values_list("id", flat=True))
        self.assertIn(publico.id, ids)
        self.assertNotIn(interno.id, ids)


class Conversions(R2Base):
    def test_forum_topic_converts_to_ticket_and_locks(self):
        cat = ForumCategory.objects.create(company=self.company, name="Sup")
        topic = ForumTopic.objects.create(company=self.company, category=cat, author=self.tech,
                                          title="Bug", content="detalhe", visibility="todos")
        req = self._auth("post", self.admin)
        resp = ForumTopicViewSet.as_view({"post": "convert_to_ticket"})(req, pk=str(topic.id))
        self.assertEqual(resp.status_code, 201)
        topic.refresh_from_db()
        self.assertIsNotNone(topic.converted_ticket_id)
        self.assertTrue(topic.is_locked)

    def test_forum_convert_blocked_for_client(self):
        cat = ForumCategory.objects.create(company=self.company, name="Sup")
        topic = ForumTopic.objects.create(company=self.company, category=cat, author=self.tech,
                                          title="Bug", content="x", visibility="todos")
        req = self._auth("post", self.client_user)
        resp = ForumTopicViewSet.as_view({"post": "convert_to_ticket"})(req, pk=str(topic.id))
        self.assertIn(resp.status_code, (403, 404))

    def test_chat_converts_to_ticket_and_links(self):
        conv = ChatConversation.objects.create(company=self.company, created_by=self.tech, name="Ajuda")
        conv.participants.add(self.admin)
        req = self._auth("post", self.admin)
        resp = ChatConversationViewSet.as_view({"post": "convert_to_ticket"})(req, pk=str(conv.id))
        self.assertEqual(resp.status_code, 201)
        conv.refresh_from_db()
        self.assertIsNotNone(conv.ticket_id)
