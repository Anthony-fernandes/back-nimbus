from django.db.models import Q, Sum
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.access import get_user_organization_ids, normalize_user_role, user_has_any_permission, user_has_permission
from common.viewsets import CompanyScopedModelViewSet
from .models import Sprint, SprintActivityPlan, SprintParticipant, SprintTicketPlan
from .serializers import SprintSerializer, SprintActivityPlanSerializer, SprintParticipantSerializer, SprintTicketPlanSerializer


class SprintViewSet(CompanyScopedModelViewSet):
    queryset = Sprint.objects.all()
    serializer_class = SprintSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["company", "project", "status", "lead", "team"]
    search_fields = ["name", "goal", "project__name"]
    ordering_fields = "__all__"

    @action(detail=False, methods=["get"])
    def velocity(self, request):
        """Histórico de velocity das últimas N sprints."""
        from apps.activities.models import Activity

        company = request.user.company
        n = int(request.query_params.get("n", 10))
        project_id = request.query_params.get("project")

        qs = Sprint.objects.filter(company=company, deleted_at__isnull=True)
        if project_id:
            qs = qs.filter(project_id=project_id)
        qs = qs.order_by("-start_at")[:n]

        result = []
        for sprint in reversed(list(qs)):
            planned = SprintActivityPlan.objects.filter(
                sprint=sprint,
                deleted_at__isnull=True,
            ).aggregate(pts=Sum("story_points"))["pts"] or 0

            delivered = Activity.objects.filter(
                sprint=sprint,
                deleted_at__isnull=True,
                status="Concluido",
            ).aggregate(pts=Sum("story_points"))["pts"] or 0

            result.append({
                "sprint_id": str(sprint.id),
                "sprint_name": sprint.name,
                "start_at": str(sprint.start_at) if sprint.start_at else None,
                "end_at": str(sprint.end_at) if sprint.end_at else None,
                "planned_points": int(planned),
                "delivered_points": int(delivered),
            })

        return Response(result)

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        role = normalize_user_role(getattr(user, "role", None))

        if role == "CLIENT":
            if not user_has_permission(user, "sprints.view"):
                return queryset.none()
            return queryset.filter(project__client_id__in=get_user_organization_ids(user)).distinct()

        if role == "TECHNICIAN":
            if user_has_permission(user, "sprints.manage"):
                return queryset
            if not user_has_permission(user, "sprints.view"):
                return queryset.none()
            return queryset.filter(
                Q(lead=user) | Q(project__owner=user) | Q(project__team=user)
            ).distinct()

        if role == "ADMIN":
            return queryset if user_has_permission(user, "sprints.view") else queryset.none()

        return queryset.none()

    def perform_create(self, serializer):
        if not user_has_permission(self.request.user, "sprints.create"):
            raise PermissionDenied("Seu perfil nao pode criar sprints.")
        super().perform_create(serializer)

    def perform_update(self, serializer):
        if not user_has_any_permission(self.request.user, ["sprints.edit", "sprints.manage"]):
            raise PermissionDenied("Seu perfil nao pode alterar sprints.")
        serializer.save()

    def perform_destroy(self, instance):
        if not user_has_permission(self.request.user, "sprints.delete"):
            raise PermissionDenied("Seu perfil nao pode excluir sprints.")
        instance.delete()


class SprintActivityPlanViewSet(CompanyScopedModelViewSet):
    queryset = SprintActivityPlan.objects.all()
    serializer_class = SprintActivityPlanSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["sprint", "activity", "project"]
    search_fields = ["notes"]
    ordering_fields = "__all__"

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        role = normalize_user_role(getattr(user, "role", None))

        if role == "CLIENT":
            if not user_has_permission(user, "sprints.view"):
                return queryset.none()
            return queryset.filter(project__client_id__in=get_user_organization_ids(user)).distinct()

        if role == "TECHNICIAN":
            if user_has_permission(user, "sprints.manage"):
                return queryset
            if not user_has_permission(user, "sprints.view"):
                return queryset.none()
            return queryset.filter(
                Q(sprint__lead=user) | Q(project__owner=user) | Q(project__team=user)
            ).distinct()

        if role == "ADMIN":
            return queryset if user_has_permission(user, "sprints.view") else queryset.none()

        return queryset.none()

    def perform_create(self, serializer):
        if not user_has_any_permission(self.request.user, ["sprints.edit", "sprints.manage"]):
            raise PermissionDenied("Seu perfil nao pode planejar atividades em sprints.")
        from rest_framework.exceptions import ValidationError
        from common.status_rules import ACTIVITY_SPRINT_ELIGIBLE, resolve_status_rule

        activity = serializer.validated_data.get("activity")
        sprint = serializer.validated_data.get("sprint")
        if activity:
            # Elegibilidade: builtin usa a lista oficial (Backlog/A fazer/Em progresso/Bloqueado);
            # status customizados seguem as permissões configuradas no workflow.
            rule = resolve_status_rule(activity.company, "activity", activity.status)
            allowed = (
                rule["permissions"].get("allows_send_to_sprint")
                if rule.get("custom")
                else activity.status in ACTIVITY_SPRINT_ELIGIBLE
            )
            if not allowed:
                raise ValidationError({"detail": f"Atividades em '{activity.status}' não podem ser planejadas em sprint."})
            # Backlog × Sprint são mutuamente exclusivos: item já planejado não pode ir para outra sprint
            if activity.sprint_id and sprint and str(activity.sprint_id) != str(sprint.id):
                raise ValidationError({"detail": "Esta atividade já está planejada em outra sprint. Remova-a de lá antes de replanejar."})
        super().perform_create(serializer)
        # Planejar = vincular à sprint e sair do Backlog (status Backlog → A fazer)
        if activity and sprint:
            activity.sprint = sprint
            if activity.status == "Backlog":
                activity.status = "A fazer"
            activity.save(update_fields=["sprint", "status", "updated_at"])

    def perform_update(self, serializer):
        if not user_has_any_permission(self.request.user, ["sprints.edit", "sprints.manage"]):
            raise PermissionDenied("Seu perfil nao pode alterar planejamentos de sprint.")
        serializer.save()

    def perform_destroy(self, instance):
        if not user_has_any_permission(self.request.user, ["sprints.edit", "sprints.manage", "sprints.delete"]):
            raise PermissionDenied("Seu perfil nao pode excluir planejamentos de sprint.")
        # Remover da sprint devolve a atividade ao Backlog (se pendente), mantendo o status atual
        activity = instance.activity
        sprint_id = instance.sprint_id
        instance.delete()
        from common.status_rules import ACTIVITY_DONE
        if activity and str(activity.sprint_id) == str(sprint_id) and activity.status not in ACTIVITY_DONE:
            activity.sprint = None
            activity.save(update_fields=["sprint", "updated_at"])


class SprintTicketPlanViewSet(CompanyScopedModelViewSet):
    queryset = SprintTicketPlan.objects.all()
    serializer_class = SprintTicketPlanSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["sprint", "ticket"]
    search_fields = ["notes"]
    ordering_fields = "__all__"

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        role = normalize_user_role(getattr(user, "role", None))

        if role == "CLIENT":
            if not user_has_permission(user, "sprints.view"):
                return queryset.none()
            return queryset.filter(ticket__client_id__in=get_user_organization_ids(user)).distinct()

        if role == "TECHNICIAN":
            if user_has_permission(user, "sprints.manage"):
                return queryset
            if not user_has_permission(user, "sprints.view"):
                return queryset.none()
            return queryset.filter(Q(sprint__lead=user)).distinct()

        if role == "ADMIN":
            return queryset if user_has_permission(user, "sprints.view") else queryset.none()

        return queryset.none()

    def perform_create(self, serializer):
        if not user_has_any_permission(self.request.user, ["sprints.edit", "sprints.manage"]):
            raise PermissionDenied("Seu perfil nao pode planejar chamados em sprints.")
        from rest_framework.exceptions import ValidationError
        from common.status_rules import TICKET_SPRINT_ELIGIBLE, resolve_status_rule

        ticket = serializer.validated_data.get("ticket")
        sprint = serializer.validated_data.get("sprint")
        if ticket:
            rule = resolve_status_rule(ticket.company, "ticket", ticket.status)
            allowed = (
                rule["permissions"].get("allows_send_to_sprint")
                if rule.get("custom")
                else ticket.status in TICKET_SPRINT_ELIGIBLE
            )
            if not allowed:
                raise ValidationError({"detail": f"Chamados em '{ticket.status}' não podem ser planejados em sprint."})
            if ticket.sprint_id and sprint and str(ticket.sprint_id) != str(sprint.id):
                raise ValidationError({"detail": "Este chamado já está planejado em outra sprint. Remova-o de lá antes de replanejar."})
        super().perform_create(serializer)
        # Planejar vincula à sprint (sai do Backlog) SEM alterar o status operacional:
        # o chamado só muda para 'Em atendimento' quando alguém iniciar o atendimento.
        if ticket and sprint:
            ticket.sprint = sprint
            ticket.save(update_fields=["sprint", "updated_at"])

    def perform_update(self, serializer):
        if not user_has_any_permission(self.request.user, ["sprints.edit", "sprints.manage"]):
            raise PermissionDenied("Seu perfil nao pode alterar planejamentos de chamados.")
        serializer.save()

    def perform_destroy(self, instance):
        if not user_has_any_permission(self.request.user, ["sprints.edit", "sprints.manage", "sprints.delete"]):
            raise PermissionDenied("Seu perfil nao pode excluir planejamentos de chamados.")
        # Remover da sprint devolve o chamado ao Backlog se ainda estiver pendente
        ticket = instance.ticket
        sprint_id = instance.sprint_id
        instance.delete()
        if ticket and str(ticket.sprint_id) == str(sprint_id) and ticket.status not in ("Finalizado", "Cancelado", "Reprovado"):
            ticket.sprint = None
            ticket.save(update_fields=["sprint", "updated_at"])


class SprintParticipantViewSet(CompanyScopedModelViewSet):
    queryset = SprintParticipant.objects.all()
    serializer_class = SprintParticipantSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["sprint", "user"]
    ordering_fields = "__all__"

    def get_queryset(self):
        qs = super().get_queryset()
        sprint_id = self.request.query_params.get("sprint")
        if sprint_id:
            qs = qs.filter(sprint_id=sprint_id)
        return qs


# ──────────────────────────────────────────────────────────────────────────────
# Sprint Retrospective & Review
# ──────────────────────────────────────────────────────────────────────────────
from apps.sprints.models import SprintRetrospective, SprintReview
from apps.sprints.serializers import SprintRetrospectiveSerializer, SprintReviewSerializer
from rest_framework.decorators import api_view, permission_classes as _pc
from rest_framework.permissions import IsAuthenticated as _IA
from rest_framework.response import Response as _R


class SprintRetrospectiveViewSet(CompanyScopedModelViewSet):
    serializer_class = SprintRetrospectiveSerializer

    def get_queryset(self):
        qs = SprintRetrospective.objects.filter(
            company=self.request.user.company,
            deleted_at__isnull=True,
        )
        sprint_id = self.request.query_params.get("sprint")
        if sprint_id:
            qs = qs.filter(sprint_id=sprint_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company, created_by=self.request.user)


class SprintReviewViewSet(CompanyScopedModelViewSet):
    serializer_class = SprintReviewSerializer

    def get_queryset(self):
        qs = SprintReview.objects.filter(
            company=self.request.user.company,
            deleted_at__isnull=True,
        )
        sprint_id = self.request.query_params.get("sprint")
        if sprint_id:
            qs = qs.filter(sprint_id=sprint_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company, created_by=self.request.user)


DONE_STATUSES = ["Concluída", "Concluido", "Done", "Finalizado"]
CANCELLED_STATUSES = ["Cancelada", "Cancelado"]


@api_view(["POST"])
@_pc([_IA])
def start_sprint(request, pk):
    """Inicia a sprint (Planejada → Em andamento). Garante uma única sprint ativa por projeto."""
    from apps.sprints.models import Sprint

    try:
        sprint = Sprint.objects.get(pk=pk, company=request.user.company)
    except Sprint.DoesNotExist:
        return _R({"detail": "Sprint não encontrada."}, status=404)

    if sprint.status == "Em andamento":
        return _R({"detail": "A sprint já está em andamento."}, status=400)
    if sprint.status == "Concluída":
        return _R({"detail": "Não é possível iniciar uma sprint concluída."}, status=400)

    active_qs = Sprint.objects.filter(
        company=request.user.company,
        status="Em andamento",
        deleted_at__isnull=True,
    ).exclude(pk=sprint.pk)
    if sprint.project_id:
        active_qs = active_qs.filter(project_id=sprint.project_id)
    conflict = active_qs.first()
    if conflict and not request.data.get("force"):
        return _R(
            {
                "detail": f"A sprint '{conflict.name}' já está em andamento. Encerre-a antes de iniciar outra, ou envie force=true.",
                "active_sprint_id": str(conflict.id),
            },
            status=409,
        )

    from django.utils import timezone as dj_tz

    sprint.status = "Em andamento"
    if not sprint.start_at:
        sprint.start_at = dj_tz.now().date()
    sprint.save(update_fields=["status", "start_at", "updated_at"])
    return _R({"detail": "Sprint iniciada.", "status": sprint.status})


@api_view(["POST"])
@_pc([_IA])
def close_sprint(request, pk):
    """Encerra sprint: cria SprintReview e devolve itens incompletos (atividades e chamados) ao backlog."""
    from apps.sprints.models import Sprint, SprintActivityPlan, SprintTicketPlan
    from apps.activities.models import Activity

    try:
        sprint = Sprint.objects.get(pk=pk, company=request.user.company)
    except Sprint.DoesNotExist:
        return _R({"detail": "Sprint não encontrada."}, status=404)

    if sprint.status == "Concluída":
        return _R({"detail": "A sprint já está concluída."}, status=400)

    # ── Activities: via plano (wizard) + FK legado ─────────────────
    planned_activity_ids = set(
        SprintActivityPlan.objects.filter(sprint=sprint, deleted_at__isnull=True)
        .values_list("activity_id", flat=True)
    )
    legacy_activity_ids = set(
        Activity.objects.filter(sprint=sprint, deleted_at__isnull=True).values_list("id", flat=True)
    )
    all_activity_ids = planned_activity_ids | legacy_activity_ids

    activities = Activity.objects.filter(id__in=all_activity_ids, deleted_at__isnull=True)
    done_activities = activities.filter(status__in=DONE_STATUSES)
    incomplete_activities = activities.exclude(status__in=DONE_STATUSES + CANCELLED_STATUSES)

    incomplete_ids_str = [str(i) for i in incomplete_activities.values_list("id", flat=True)]

    # ── Tickets: via plano (wizard) ────────────────────────────────
    ticket_plans = SprintTicketPlan.objects.filter(
        sprint=sprint, deleted_at__isnull=True
    ).select_related("ticket")
    done_tickets = [p for p in ticket_plans if p.ticket and p.ticket.status in DONE_STATUSES]
    incomplete_ticket_plans = [
        p for p in ticket_plans
        if p.ticket and p.ticket.status not in DONE_STATUSES + CANCELLED_STATUSES
    ]

    # ── Pontos planejados vs entregues (planos primeiro, fallback FK) ─
    activity_plans = SprintActivityPlan.objects.filter(sprint=sprint, deleted_at__isnull=True)
    planned_pts = (
        sum(p.story_points or 0 for p in activity_plans)
        + sum(p.story_points or 0 for p in ticket_plans)
    ) or (sprint.story_points or 0)
    done_activity_ids = set(done_activities.values_list("id", flat=True))
    delivered_pts = sum(
        (p.story_points or 0) for p in activity_plans if p.activity_id in done_activity_ids
    ) + sum((p.story_points or 0) for p in done_tickets)
    if delivered_pts == 0 and not activity_plans.exists() and not ticket_plans:
        delivered_pts = sum(a.story_points or 0 for a in done_activities)

    planned_items = len(all_activity_ids) + len(ticket_plans)
    delivered_items = done_activities.count() + len(done_tickets)

    # ── Tratar itens pendentes conforme decisão do usuário ─────────
    # pending_action: "backlog" (padrão — devolve ao backlog) | "move" (move para outra sprint)
    pending_action = request.data.get("pending_action") or "backlog"
    target_sprint = None
    if pending_action == "move":
        target_id = request.data.get("target_sprint_id")
        target_sprint = Sprint.objects.filter(
            pk=target_id, company=sprint.company, deleted_at__isnull=True
        ).exclude(pk=sprint.pk).first()
        if not target_sprint:
            return _R({"detail": "Informe uma sprint de destino válida em target_sprint_id."}, status=400)

    if target_sprint:
        # Move os itens pendentes (FK + planos) para a sprint de destino
        incomplete_activities.update(sprint=target_sprint)
        SprintActivityPlan.objects.filter(
            sprint=sprint, activity_id__in=incomplete_ids_str
        ).update(sprint=target_sprint)
        for plan in incomplete_ticket_plans:
            plan.sprint = target_sprint
            plan.save(update_fields=["sprint", "updated_at"])
            if plan.ticket and plan.ticket.sprint_id == sprint.id:
                plan.ticket.sprint = target_sprint
                plan.ticket.save(update_fields=["sprint", "updated_at"])
    else:
        # Devolve ao Backlog: remove o vínculo com a sprint mantendo o status de execução.
        # Só volta ao status "Backlog" quem ainda não iniciou (A fazer/Backlog).
        incomplete_activities.filter(status__in=["A fazer", "Backlog"]).update(sprint=None, status="Backlog")
        incomplete_activities.exclude(status__in=["A fazer", "Backlog"]).update(sprint=None)
        SprintActivityPlan.objects.filter(
            sprint=sprint, activity_id__in=incomplete_ids_str
        ).delete()
        for plan in incomplete_ticket_plans:
            ticket = plan.ticket
            plan.delete()
            if ticket and ticket.sprint_id == sprint.id:
                ticket.sprint = None
                ticket.save(update_fields=["sprint", "updated_at"])

    review, _ = SprintReview.objects.get_or_create(
        sprint=sprint,
        company=sprint.company,
        defaults={
            "planned_points": planned_pts,
            "delivered_points": delivered_pts,
            "planned_items": planned_items,
            "delivered_items": delivered_items,
            "incomplete_activity_ids": incomplete_ids_str,
            "notes": request.data.get("notes", ""),
            "created_by": request.user,
        }
    )

    sprint.status = "Concluída"
    sprint.save()

    return _R({
        "detail": "Sprint encerrada com sucesso.",
        "review_id": str(review.id),
        "incomplete_moved": len(incomplete_ids_str) + len(incomplete_ticket_plans),
        "delivered_points": delivered_pts,
        "planned_points": planned_pts,
        "delivered_items": delivered_items,
        "planned_items": planned_items,
    })


@api_view(["GET"])
@_pc([_IA])
def sprint_metrics(request, pk):
    """Agregados da sprint para indicadores configuráveis do frontend."""
    from apps.sprints.models import Sprint, SprintActivityPlan, SprintTicketPlan
    from apps.activities.models import Activity, ActivityTimeEntry

    try:
        sprint = Sprint.objects.get(pk=pk, company=request.user.company)
    except Sprint.DoesNotExist:
        return _R({"detail": "Sprint não encontrada."}, status=404)

    a_plans = list(SprintActivityPlan.objects.filter(sprint=sprint, deleted_at__isnull=True).select_related("activity"))
    t_plans = list(SprintTicketPlan.objects.filter(sprint=sprint, deleted_at__isnull=True).select_related("ticket"))

    done_act = [p for p in a_plans if p.activity and p.activity.status in DONE_STATUSES]
    done_tkt = [p for p in t_plans if p.ticket and p.ticket.status in DONE_STATUSES]
    blocked = [p for p in a_plans if p.activity and p.activity.status in ("Bloqueado", "Pausado")]
    in_progress = [
        p for p in a_plans + t_plans
        if (getattr(p, "activity", None) or getattr(p, "ticket", None))
        and (getattr(p, "activity", None) or getattr(p, "ticket", None)).status
        in ("Em progresso", "Em atendimento", "Em andamento")
    ]

    sp_planned = sum(p.story_points or 0 for p in a_plans + t_plans)
    sp_done = sum(p.story_points or 0 for p in done_act + done_tkt)
    hours_planned = float(sum(p.planned_hours or 0 for p in a_plans + t_plans))
    activity_ids = [p.activity_id for p in a_plans]
    hours_done = float(sum(
        e.hours for e in ActivityTimeEntry.objects.filter(
            sprint=sprint, deleted_at__isnull=True,
        )
    ))
    capacity = sprint.total_capacity
    total_items = len(a_plans) + len(t_plans)
    done_items = len(done_act) + len(done_tkt)

    # Bugs planejados na sprint (atividades do tipo Bug)
    bugs = len([p for p in a_plans if p.activity and (p.activity.type or "").lower() == "bug"])

    # Itens atrasados: não concluídos com prazo vencido (due da atividade,
    # planned_end_date do plano ou fim da sprint)
    from datetime import date as _date
    today = _date.today()
    overdue = 0
    for p in a_plans:
        item = p.activity
        if not item or item.status in DONE_STATUSES:
            continue
        deadline = item.due_at or p.planned_end_date or sprint.end_at
        if deadline and deadline < today:
            overdue += 1
    for p in t_plans:
        item = p.ticket
        if not item or item.status in ("Finalizado", "Cancelado"):
            continue
        deadline = p.planned_end_date or sprint.end_at
        if deadline and deadline < today:
            overdue += 1

    progress_pct = round(done_items / total_items * 100, 1) if total_items else 0

    # Risco da sprint: avanço real vs tempo decorrido + bloqueios/atrasos
    levels = ["baixo", "medio", "alto"]
    risk = "baixo"
    risk_reasons = []

    def bump(level):
        nonlocal risk
        if levels.index(level) > levels.index(risk):
            risk = level

    if sprint.status == "Em andamento" and sprint.start_at and sprint.end_at:
        total_days = max(1, (sprint.end_at - sprint.start_at).days)
        elapsed_pct = min(100, max(0, (today - sprint.start_at).days / total_days * 100))
        gap = elapsed_pct - progress_pct
        if gap > 30:
            bump("alto")
            risk_reasons.append(f"Progresso de {progress_pct:.0f}% com {elapsed_pct:.0f}% do tempo decorrido")
        elif gap > 10:
            bump("medio")
            risk_reasons.append("Progresso abaixo do ritmo esperado")
        if overdue:
            bump("alto" if overdue > 2 else "medio")
            risk_reasons.append(f"{overdue} item(ns) atrasado(s)")
        if blocked:
            bump("medio")
            risk_reasons.append(f"{len(blocked)} item(ns) bloqueado(s)")
    elif sprint.status == "Finalizada" and total_items and progress_pct < 70:
        bump("medio")
        risk_reasons.append("Sprint encerrada com entrega abaixo de 70%")

    return _R({
        "total_items": total_items,
        "activities": len(a_plans),
        "tickets": len(t_plans),
        "bugs": bugs,
        "done": done_items,
        "in_progress": len(in_progress),
        "pending": max(0, total_items - done_items - len(in_progress) - len(blocked)),
        "blocked": len(blocked),
        "overdue": overdue,
        "story_points_planned": sp_planned,
        "story_points_done": sp_done,
        "hours_planned": hours_planned,
        "hours_done": hours_done,
        "capacity": capacity,
        "capacity_used_pct": round(hours_planned / capacity * 100, 1) if capacity else 0,
        "progress_pct": progress_pct,
        "risk": risk,
        "risk_reasons": risk_reasons,
    })


@api_view(["GET"])
@_pc([_IA])
def sprint_velocity(request):
    """Retorna histórico de velocity (story_points entregues) das últimas sprints."""
    from apps.sprints.models import Sprint
    from apps.activities.models import Activity
    from django.db.models import Sum

    company = request.user.company
    project_id = request.query_params.get("project")
    limit = int(request.query_params.get("limit", 10))

    qs = Sprint.objects.filter(company=company, deleted_at__isnull=True)
    if project_id:
        qs = qs.filter(project_id=project_id)
    qs = qs.filter(status__in=["Concluída", "Concluido", "Finalizada", "Concluída/Fechada"]).order_by("-end_at")[:limit]

    result = []
    for sprint in reversed(list(qs)):
        delivered = Activity.objects.filter(
            sprint=sprint,
            deleted_at__isnull=True,
            status__in=["Concluída", "Concluido", "Done"],
        ).aggregate(pts=Sum("story_points"))["pts"] or 0
        result.append({
            "sprint_id": str(sprint.id),
            "sprint_name": sprint.name,
            "end_at": str(sprint.end_at) if sprint.end_at else None,
            "planned_points": sprint.story_points,
            "delivered_points": int(delivered),
        })

    avg_velocity = round(sum(r["delivered_points"] for r in result) / len(result), 1) if result else 0

    return _R({"sprints": result, "avg_velocity": avg_velocity})
