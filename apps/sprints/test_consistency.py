"""Testes das regras de consistência (C1–C4):
progresso/status de projeto como fonte única, itens da sprint e a regra de
'uma sprint ativa por técnico'.
"""
from django.test import TestCase

from apps.companies.models import Company
from apps.users.models import User
from apps.clients.models import Client
from apps.projects.models import Project
from apps.activities.models import Activity
from apps.sprints.models import Sprint, SprintParticipant, SprintActivityPlan

from common.project_metrics import compute_project_metrics
from common.sprint_items import activity_kanban_column, build_sprint_items
from common.active_sprint import user_active_sprint, other_active_sprint_for_user


class ProjectMetricsTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Metrics Co")
        self.client_obj = Client.objects.create(company=self.company, name="Cli")

    def _project(self, **kw):
        return Project.objects.create(company=self.company, client=self.client_obj, name="P", **kw)

    def test_empty_project_has_no_basis_and_zero_progress(self):
        p = self._project()
        m = compute_project_metrics(p)
        self.assertEqual(m["progress"], 0)
        self.assertFalse(m["has_calculation_basis"])
        self.assertFalse(m["can_complete"])

    def test_progress_from_activities(self):
        p = self._project()
        Activity.objects.create(company=self.company, project=p, title="A1", status="Concluída")
        Activity.objects.create(company=self.company, project=p, title="A2", status="A fazer")
        m = compute_project_metrics(p)
        self.assertEqual(m["progress"], 50)
        self.assertTrue(m["has_calculation_basis"])
        self.assertFalse(m["can_complete"])

    def test_can_complete_when_all_done(self):
        p = self._project()
        Activity.objects.create(company=self.company, project=p, title="A1", status="Concluída")
        Activity.objects.create(company=self.company, project=p, title="A2", status="Concluído")
        m = compute_project_metrics(p)
        self.assertEqual(m["progress"], 100)
        self.assertTrue(m["can_complete"])


class SprintItemsTest(TestCase):
    def test_kanban_column_mapping_never_drops(self):
        self.assertEqual(activity_kanban_column("Em revisao"), "Em revisão")
        self.assertEqual(activity_kanban_column("A fazer"), "A fazer")
        self.assertEqual(activity_kanban_column("qualquer coisa"), "Não mapeado")

    def test_build_sprint_items_counts(self):
        company = Company.objects.create(name="Items Co")
        client_obj = Client.objects.create(company=company, name="C")
        project = Project.objects.create(company=company, client=client_obj, name="P")
        sprint = Sprint.objects.create(company=company, name="S1")
        a1 = Activity.objects.create(company=company, project=project, title="A1", status="A fazer")
        a2 = Activity.objects.create(company=company, project=project, title="A2", status="Em revisao")
        SprintActivityPlan.objects.create(company=company, sprint=sprint, activity=a1)
        SprintActivityPlan.objects.create(company=company, sprint=sprint, activity=a2)
        data = build_sprint_items(sprint)
        self.assertEqual(data["totals"]["total"], 2)
        cols = {it["kanban_column"] for it in data["items"]}
        self.assertIn("A fazer", cols)
        self.assertIn("Em revisão", cols)


class ActiveSprintRuleTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Sprint Co")
        self.user = User.objects.create_user(
            username="tec", password="x", company=self.company, role="TECHNICIAN"
        )
        self.s1 = Sprint.objects.create(company=self.company, name="S1", status="Em andamento")
        self.s2 = Sprint.objects.create(company=self.company, name="S2", status="Em andamento")

    def test_user_active_sprint(self):
        SprintParticipant.objects.create(company=self.company, sprint=self.s1, user=self.user)
        self.assertEqual(user_active_sprint(self.user), self.s1)

    def test_other_active_sprint_detects_conflict(self):
        SprintParticipant.objects.create(company=self.company, sprint=self.s1, user=self.user)
        other = other_active_sprint_for_user(self.user, self.company, exclude_sprint_id=self.s2.id)
        self.assertEqual(other, self.s1)

    def test_no_conflict_when_only_one(self):
        SprintParticipant.objects.create(company=self.company, sprint=self.s1, user=self.user)
        other = other_active_sprint_for_user(self.user, self.company, exclude_sprint_id=self.s1.id)
        self.assertIsNone(other)
