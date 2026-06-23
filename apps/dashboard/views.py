from datetime import date, timedelta

from django.db.models import Avg, Count, F, Q, Sum
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.activities.models import Activity
from apps.clients.models import Client
from apps.projects.models import Project
from apps.sprints.models import Sprint, SprintActivityPlan
from apps.tickets.models import Ticket
from apps.users.models import User
from common.viewsets import CompanyScopedModelViewSet

from .models import Dashboard, DashboardVersion
from .serializers import DashboardSerializer, DashboardVersionSerializer


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = getattr(request.user, "company", None)

        if not company:
            return Response({
                "tickets_open": 0,
                "tickets_critical": 0,
                "clients": 0,
                "projects_active": 0,
                "activities": 0,
                "recent_tickets": [],
                "projects_at_risk": [],
            })

        tickets = Ticket.objects.filter(company=company)
        projects = Project.objects.filter(company=company)
        clients = Client.objects.filter(company=company)
        activities = Activity.objects.filter(company=company)

        return Response({
            "tickets_open": tickets.exclude(status="Finalizado").count(),
            "tickets_critical": tickets.filter(priority="Crítica").count(),
            "clients": clients.count(),
            "projects_active": projects.exclude(status="Concluído").count(),
            "activities": activities.count(),
            "recent_tickets": list(
                tickets.order_by("-created_at")[:8].values(
                    "id",
                    "code",
                    "title",
                    "priority",
                    "status",
                    "sla",
                )
            ),
            "projects_at_risk": list(
                projects.filter(status="Em risco")[:5].values("id", "name", "progress", "due_at")
            ),
        })


class DashboardViewSet(CompanyScopedModelViewSet):
    serializer_class = DashboardSerializer
    queryset = Dashboard.objects.all()

    def get_queryset(self):
        company = getattr(self.request.user, "company", None)
        if not company:
            return Dashboard.objects.none()
        return Dashboard.objects.filter(company=company, deleted_at__isnull=True)

    def perform_create(self, serializer):
        company = getattr(self.request.user, "company", None)
        serializer.save(company=company)

    @action(detail=False, methods=["get"], url_path="active")
    def active(self, request):
        company = getattr(request.user, "company", None)
        if not company:
            return Response(None)
        dashboard = Dashboard.objects.filter(company=company, is_active=True, deleted_at__isnull=True).first()
        if not dashboard:
            return Response(None)
        serializer = self.get_serializer(dashboard)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="duplicate")
    def duplicate(self, request, pk=None):
        original = self.get_object()
        clone = Dashboard.objects.create(
            company=original.company,
            name=f"{original.name} (copia)",
            description=original.description,
            type=original.type,
            status="draft",
            is_active=False,
            components_json=original.components_json,
            filters_json=original.filters_json,
            created_by=original.created_by,
        )
        serializer = self.get_serializer(clone)
        return Response(serializer.data, status=201)

    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request, pk=None):
        dashboard = self.get_object()
        # Deactivate all other dashboards for this company
        Dashboard.objects.filter(company=dashboard.company, is_active=True).exclude(pk=dashboard.pk).update(is_active=False)
        dashboard.status = "active"
        dashboard.is_active = True
        dashboard.save()
        # Create a version snapshot
        last_version = DashboardVersion.objects.filter(dashboard=dashboard).order_by("-version_number").first()
        next_version = (last_version.version_number + 1) if last_version else 1
        DashboardVersion.objects.create(
            dashboard=dashboard,
            version_number=next_version,
            config_snapshot={
                "name": dashboard.name,
                "description": dashboard.description,
                "type": dashboard.type,
                "status": dashboard.status,
                "components_json": dashboard.components_json,
                "filters_json": dashboard.filters_json,
            },
            created_by=dashboard.created_by,
            is_published=True,
        )
        serializer = self.get_serializer(dashboard)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="set-active")
    def set_active(self, request, pk=None):
        dashboard = self.get_object()
        Dashboard.objects.filter(company=dashboard.company, is_active=True).exclude(pk=dashboard.pk).update(is_active=False)
        dashboard.status = "active"
        dashboard.is_active = True
        dashboard.save()
        serializer = self.get_serializer(dashboard)
        return Response(serializer.data)


def _parse_period(period: str):
    """Return (date_from, date_to) based on period filter string."""
    today = date.today()
    if period == "today":
        return today, today
    if period == "this_week":
        start = today - timedelta(days=today.weekday())
        return start, today
    if period == "this_month":
        return today.replace(day=1), today
    if period == "7d":
        return today - timedelta(days=6), today
    if period == "90d":
        return today - timedelta(days=89), today
    # default 30d
    return today - timedelta(days=29), today


def _apply_ticket_filters(qs, filters: dict):
    period = filters.get("period", "30d")
    date_from, date_to = _parse_period(period)
    qs = qs.filter(created_at__date__gte=date_from, created_at__date__lte=date_to)
    if filters.get("priority"):
        qs = qs.filter(priority=filters["priority"])
    if filters.get("status"):
        qs = qs.filter(status=filters["status"])
    if filters.get("responsible"):
        qs = qs.filter(responsible_technician_id=filters["responsible"])
    if filters.get("client"):
        qs = qs.filter(client_id=filters["client"])
    if filters.get("project"):
        qs = qs.filter(project_id=filters["project"])
    if filters.get("sprint"):
        qs = qs.filter(sprint_id=filters["sprint"])
    return qs


CLOSED_STATUSES = ["Finalizado", "Cancelado", "Convertido em Atividade de Projeto"]
OPEN_STATUSES = [s for s, _ in Ticket.STATUS if s not in CLOSED_STATUSES]


class DashboardDataQueryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        company = getattr(request.user, "company", None)
        if not company:
            return Response({"error": "no_company"}, status=400)

        source = request.data.get("source", "")
        filters = request.data.get("filters", {})
        today = date.today()
        now = timezone.now()

        tickets_qs = Ticket.objects.filter(company=company, deleted_at__isnull=True)
        open_tickets = tickets_qs.filter(status__in=OPEN_STATUSES)

        # ── KPI helpers ───────────────────────────────────────────────
        if source == "tickets_open":
            return Response({"value": open_tickets.count(), "unit": "chamados"})

        if source == "tickets_critical":
            return Response({"value": open_tickets.filter(priority="Critica").count(), "unit": "chamados"})

        if source == "tickets_late":
            return Response({"value": open_tickets.filter(sla_due_at__lt=now).count(), "unit": "chamados"})

        if source == "tickets_due_today":
            return Response({"value": open_tickets.filter(due_at=today).count(), "unit": "chamados"})

        if source == "tickets_in_progress":
            return Response({"value": tickets_qs.filter(status="Em atendimento").count(), "unit": "chamados"})

        if source == "tickets_waiting_customer":
            return Response({"value": tickets_qs.filter(status="Aguardando cliente").count(), "unit": "chamados"})

        if source == "tickets_unassigned":
            return Response({"value": open_tickets.filter(responsible_technician__isnull=True).count(), "unit": "chamados"})

        if source == "tickets_closed_today":
            return Response({"value": tickets_qs.filter(status="Finalizado", finished_at__date=today).count(), "unit": "chamados"})

        # ── Distributions ─────────────────────────────────────────────
        if source == "tickets_by_status":
            rows = (
                _apply_ticket_filters(tickets_qs, filters)
                .values("status")
                .annotate(total=Count("id"))
                .order_by("-total")
            )
            return Response({"data": [{"name": r["status"], "value": r["total"]} for r in rows]})

        if source == "tickets_by_priority":
            rows = (
                _apply_ticket_filters(tickets_qs, filters)
                .values("priority")
                .annotate(total=Count("id"))
                .order_by("-total")
            )
            return Response({"data": [{"name": r["priority"], "value": r["total"]} for r in rows]})

        if source == "tickets_by_owner":
            rows = (
                _apply_ticket_filters(tickets_qs, filters)
                .filter(responsible_technician__isnull=False)
                .values(name=F("responsible_technician__first_name"))
                .annotate(total=Count("id"))
                .order_by("-total")[:15]
            )
            return Response({"data": [{"name": r["name"] or "Sem nome", "value": r["total"]} for r in rows]})

        if source == "tickets_by_client":
            rows = (
                _apply_ticket_filters(tickets_qs, filters)
                .values(name=F("client__name"))
                .annotate(total=Count("id"))
                .order_by("-total")[:15]
            )
            return Response({"data": [{"name": r["name"] or "Sem cliente", "value": r["total"]} for r in rows]})

        if source == "tickets_trend":
            period = filters.get("period", "30d")
            date_from, date_to = _parse_period(period)
            delta = (date_to - date_from).days + 1
            rows = (
                tickets_qs
                .filter(created_at__date__gte=date_from, created_at__date__lte=date_to)
                .values(day=F("created_at__date"))
                .annotate(total=Count("id"))
                .order_by("day")
            )
            counts_by_day = {str(r["day"]): r["total"] for r in rows}
            data = []
            for i in range(delta):
                d = date_from + timedelta(days=i)
                data.append({"name": d.strftime("%d/%m"), "value": counts_by_day.get(str(d), 0)})
            return Response({"data": data})

        if source == "tickets_attention_list":
            late = open_tickets.filter(sla_due_at__lt=now)
            due_today = open_tickets.filter(due_at=today)
            critical = open_tickets.filter(priority="Critica")
            attention = (late | due_today | critical).distinct().order_by("-created_at")[:20]
            items = list(attention.values("id", "code", "title", "priority", "status", "sla_due_at", "due_at"))
            return Response({"data": items})

        # ── Sprints ───────────────────────────────────────────────────
        sprints_qs = Sprint.objects.filter(company=company, deleted_at__isnull=True)
        active_sprint = sprints_qs.filter(status="Em andamento").order_by("-start_at").first()

        if source == "sprints_active":
            return Response({"value": sprints_qs.filter(status="Em andamento").count(), "unit": "sprints"})

        # For sprint detail sources, resolve which sprint to use
        sprint_id = filters.get("sprint")
        sprint = None
        if sprint_id:
            sprint = sprints_qs.filter(id=sprint_id).first()
        if not sprint:
            sprint = active_sprint

        sprint_activities = Activity.objects.none()
        if sprint:
            sprint_activities = Activity.objects.filter(company=company, sprint=sprint, deleted_at__isnull=True)

        COMPLETED_STATUSES = ["Concluido", "Finalizado", "Done", "Concluída"]
        IN_PROGRESS_STATUSES = ["Em andamento", "Em progresso", "In Progress"]
        BLOCKED_STATUSES = ["Bloqueado", "Impedido", "Blocked"]
        NOT_STARTED_STATUSES = ["Backlog", "A fazer", "To Do", "Nao iniciado"]

        total = sprint_activities.count()
        completed = sprint_activities.filter(status__in=COMPLETED_STATUSES).count()

        if source == "sprint_items_total":
            return Response({"value": total, "unit": "itens"})

        if source == "sprint_items_completed":
            return Response({"value": completed, "unit": "itens"})

        if source == "sprint_items_in_progress":
            return Response({"value": sprint_activities.filter(status__in=IN_PROGRESS_STATUSES).count(), "unit": "itens"})

        if source == "sprint_items_not_started":
            return Response({"value": sprint_activities.filter(status__in=NOT_STARTED_STATUSES).count(), "unit": "itens"})

        if source == "sprint_items_blocked":
            return Response({"value": sprint_activities.filter(status__in=BLOCKED_STATUSES).count(), "unit": "itens"})

        if source == "sprint_items_late":
            return Response({"value": sprint_activities.filter(due_at__lt=today).exclude(status__in=COMPLETED_STATUSES).count(), "unit": "itens"})

        if source == "sprint_days_remaining":
            if sprint and sprint.end_at:
                remaining = max(0, (sprint.end_at - today).days)
            else:
                remaining = 0
            return Response({"value": remaining, "unit": "dias"})

        if source == "sprint_progress":
            pct = round((completed / total * 100)) if total > 0 else 0
            return Response({"value": pct, "unit": "%"})

        if source == "sprint_status_distribution":
            rows = sprint_activities.values("status").annotate(total=Count("id")).order_by("-total")
            return Response({"data": [{"name": r["status"], "value": r["total"]} for r in rows]})

        if source == "sprint_owner_distribution":
            rows = (
                sprint_activities
                .filter(assignee__isnull=False)
                .values(name=F("assignee__first_name"))
                .annotate(total=Count("id"))
                .order_by("-total")
            )
            return Response({"data": [{"name": r["name"] or "Sem nome", "value": r["total"]} for r in rows]})

        if source == "sprint_burndown":
            if sprint and sprint.start_at and sprint.end_at:
                delta = (sprint.end_at - sprint.start_at).days + 1
                # planned: linear burndown from total to 0
                planned_per_day = total / delta if delta > 0 else 0
                data = []
                for i in range(delta):
                    d = sprint.start_at + timedelta(days=i)
                    planned = round(total - planned_per_day * i)
                    done = sprint_activities.filter(
                        status__in=COMPLETED_STATUSES, updated_at__date__lte=d
                    ).count()
                    remaining = total - done
                    data.append({"name": d.strftime("%d/%m"), "Planejado": planned, "Realizado": remaining})
            else:
                data = []
            return Response({"data": data})

        if source == "sprint_capacity_people":
            plans = SprintActivityPlan.objects.filter(
                company=company, sprint=sprint
            ).values("responsible_ids", "planned_hours") if sprint else []
            user_map: dict[str, dict] = {}
            for plan in plans:
                hours = float(plan["planned_hours"] or 0)
                for uid in (plan["responsible_ids"] or []):
                    if uid not in user_map:
                        user_map[uid] = {"planned": 0}
                    user_map[uid]["planned"] += hours
            users_qs = User.objects.filter(company=company, is_active=True)
            rows = []
            for u in users_qs:
                uid = str(u.id)
                planned = user_map.get(uid, {}).get("planned", 0)
                capacity = u.total_hours or 40
                occupancy = round(planned / capacity * 100) if capacity > 0 else 0
                rows.append({
                    "name": u.get_full_name() or u.username,
                    "Capacidade": capacity,
                    "Utilizado": round(planned),
                    "Ocupacao": occupancy,
                })
            return Response({"data": rows})

        if source == "sprint_attention_items":
            attention = sprint_activities.filter(
                Q(status__in=BLOCKED_STATUSES) | Q(due_at__lt=today)
            ).exclude(status__in=COMPLETED_STATUSES).order_by("due_at")[:20]
            items = list(attention.values("id", "title", "status", "priority", "due_at", "assignee__first_name"))
            return Response({"data": items})

        # ── Projects ──────────────────────────────────────────────────
        projects_qs = Project.objects.filter(company=company, deleted_at__isnull=True)

        if source == "projects_active":
            return Response({"value": projects_qs.exclude(status="Concluido").count(), "unit": "projetos"})

        if source == "projects_late":
            return Response({"value": projects_qs.filter(due_at__lt=today).exclude(status="Concluido").count(), "unit": "projetos"})

        if source == "projects_by_status":
            rows = projects_qs.values("status").annotate(total=Count("id")).order_by("-total")
            return Response({"data": [{"name": r["status"], "value": r["total"]} for r in rows]})

        if source == "projects_deliveries_week":
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            items = list(
                projects_qs.filter(due_at__gte=week_start, due_at__lte=week_end)
                .values("id", "name", "status", "progress", "due_at")
                .order_by("due_at")
            )
            return Response({"data": items})

        if source == "project_activity_distribution":
            rows = (
                Activity.objects.filter(company=company, project__isnull=False, deleted_at__isnull=True)
                .values(name=F("project__name"))
                .annotate(total=Count("id"))
                .order_by("-total")[:15]
            )
            return Response({"data": [{"name": r["name"], "value": r["total"]} for r in rows]})

        # ── Users ─────────────────────────────────────────────────────
        users_qs = User.objects.filter(company=company, is_active=True)

        if source == "users_active":
            return Response({"value": users_qs.count(), "unit": "pessoas"})

        if source == "users_capacity_people":
            rows = [
                {"name": u.get_full_name() or u.username, "value": u.total_hours or 40}
                for u in users_qs.order_by("-total_hours")[:20]
            ]
            return Response({"data": rows})

        if source == "users_hours_used_people":
            rows = [
                {"name": u.get_full_name() or u.username, "value": u.used_hours or 0}
                for u in users_qs.order_by("-used_hours")[:20]
            ]
            return Response({"data": rows})

        if source == "users_occupancy_people":
            rows = []
            for u in users_qs:
                capacity = u.total_hours or 40
                used = u.used_hours or 0
                pct = round(used / capacity * 100) if capacity > 0 else 0
                rows.append({"name": u.get_full_name() or u.username, "value": pct})
            rows.sort(key=lambda x: x["value"], reverse=True)
            return Response({"data": rows[:20]})

        if source == "users_bottlenecks_role":
            rows = (
                users_qs.filter(job_title__gt="")
                .values(name=F("job_title"))
                .annotate(count=Count("id"), avg_used=Avg("used_hours"), avg_capacity=Avg("total_hours"))
                .order_by("-avg_used")[:10]
            )
            data = []
            for r in rows:
                cap = float(r["avg_capacity"] or 40)
                used = float(r["avg_used"] or 0)
                data.append({"name": r["name"], "value": round(used / cap * 100) if cap > 0 else 0, "count": r["count"]})
            return Response({"data": data})

        return Response({"error": f"unknown_source: {source}"}, status=400)


class AdminDashboardStatsView(APIView):
    """Unified admin dashboard stats across all modules."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = getattr(request.user, "company", None)
        if not company:
            return Response({"error": "no company"}, status=400)

        from apps.communication.models import (
            ForumTopic, ForumReply, ChatConversation,
        )
        from apps.knowledge.models import KnowledgeArticle, ArticleRating
        from apps.tickets.models import Ticket
        from apps.users.models import User
        from django.db.models import Avg

        # Forum stats
        forum_topics = ForumTopic.objects.filter(company=company).count()
        forum_replies = ForumReply.objects.filter(topic__company=company).count()
        forum_active_users = ForumTopic.objects.filter(company=company).values("author").distinct().count()

        # KB stats
        kb_articles = KnowledgeArticle.objects.filter(company=company, status="PUBLISHED").count()
        kb_avg_rating_qs = ArticleRating.objects.filter(article__company=company).aggregate(
            avg=Avg("helpful")
        )
        kb_avg_rating = round(float(kb_avg_rating_qs["avg"] or 0) * 5, 2)

        # Tickets stats
        tickets_open = Ticket.objects.filter(company=company, status__in=["OPEN", "IN_PROGRESS"]).count()
        tickets_closed = Ticket.objects.filter(company=company, status="CLOSED").count()

        # Chat stats
        chat_active = ChatConversation.objects.filter(company=company, is_archived=False).count()

        return Response({
            "forum": {
                "topics": forum_topics,
                "replies": forum_replies,
                "active_users": forum_active_users,
            },
            "kb": {
                "articles": kb_articles,
                "avg_rating": kb_avg_rating,
            },
            "tickets": {
                "open": tickets_open,
                "closed": tickets_closed,
            },
            "chat": {
                "active_conversations": chat_active,
            },
        })
