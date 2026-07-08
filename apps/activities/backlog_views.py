"""Backlog unificado: atividades, chamados, bugs, melhorias e demandas internas."""
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.activities.models import Activity
from apps.tickets.models import Ticket

# Statuses que caracterizam item "no backlog" (aguardando planejamento)
ACTIVITY_BACKLOG_STATUSES = ["Backlog", "A fazer"]
TICKET_BACKLOG_STATUSES = ["Aberto", "Triagem", "Backlog", "Aguardando atendimento"]


def _activity_type_to_backlog(activity_type: str) -> str:
    t = (activity_type or "").lower()
    if t == "bug":
        return "bug"
    if t in ("melhoria", "improvement"):
        return "improvement"
    if t in ("demanda interna", "interna", "internal"):
        return "internal_task"
    return "task"


def _collect_items(request):
    """Aplica filtros comuns e retorna a lista unificada (sem paginação)."""
    company = request.user.company
    params = request.query_params
    search = (params.get("search") or "").strip().lower()
    item_type = params.get("type") or ""
    status_f = params.get("status") or ""
    priority = params.get("priority") or ""
    team = params.get("team") or ""
    no_sprint = params.get("no_sprint") == "true"

    items = []

    include_tickets = item_type in ("", "ticket")
    include_activities = item_type in ("", "task", "bug", "improvement", "internal_task")

    if include_activities:
        qs = Activity.objects.filter(
            company=company, deleted_at__isnull=True, status__in=ACTIVITY_BACKLOG_STATUSES,
        ).select_related("assignee", "project", "sprint")
        if priority:
            qs = qs.filter(priority=priority)
        if status_f:
            qs = qs.filter(status=status_f)
        if no_sprint:
            qs = qs.filter(sprint__isnull=True)
        if team:
            qs = qs.filter(sprint__team_id=team)
        for a in qs:
            btype = _activity_type_to_backlog(a.type)
            if item_type and btype != item_type:
                continue
            title = a.title or ""
            if search and search not in title.lower() and search not in str(a.id):
                continue
            items.append({
                "id": str(a.id),
                "type": btype,
                "code": str(a.id)[:8].upper(),
                "title": title,
                "origin": a.project.name if a.project_id else "Demanda interna",
                "priority": a.priority or "Média",
                "status": a.status,
                "responsible": a.assignee.full_name_or_username if a.assignee_id else "",
                "sprint": a.sprint.name if a.sprint_id else None,
                "sprint_id": str(a.sprint_id) if a.sprint_id else None,
                "due_at": str(a.due_at) if a.due_at else None,
                "created_at": a.created_at.isoformat(),
            })

    if include_tickets:
        qs = Ticket.objects.filter(
            company=company, deleted_at__isnull=True, status__in=TICKET_BACKLOG_STATUSES,
        ).select_related("responsible_technician", "client", "sprint")
        if priority:
            qs = qs.filter(priority=priority)
        if status_f:
            qs = qs.filter(status=status_f)
        if no_sprint:
            qs = qs.filter(sprint__isnull=True)
        if search:
            qs = qs.filter(
                Q(title__icontains=search) | Q(code__icontains=search)
                | Q(client__name__icontains=search)
            )
        for t in qs:
            items.append({
                "id": str(t.id),
                "type": "ticket",
                "code": t.code or str(t.id)[:8],
                "title": t.title,
                "origin": t.client.name if t.client_id else "Helpdesk",
                "priority": t.priority or "Media",
                "status": t.status,
                "responsible": (
                    t.responsible_technician.full_name_or_username
                    if t.responsible_technician_id else ""
                ),
                "sprint": t.sprint.name if t.sprint_id else None,
                "sprint_id": str(t.sprint_id) if t.sprint_id else None,
                "due_at": t.due_at.isoformat() if t.due_at else None,
                "created_at": t.created_at.isoformat(),
            })

    items.sort(key=lambda i: i["created_at"], reverse=True)
    return items


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def backlog_list(request):
    items = _collect_items(request)
    try:
        page = max(1, int(request.query_params.get("page", 1)))
        page_size = min(100, max(1, int(request.query_params.get("page_size", 25))))
    except ValueError:
        page, page_size = 1, 25
    count = len(items)
    total_pages = max(1, -(-count // page_size))
    start = (page - 1) * page_size
    return Response({
        "results": items[start:start + page_size],
        "count": count,
        "page": page,
        "pageSize": page_size,
        "totalPages": total_pages,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def backlog_metrics(request):
    """Métricas do backlog respeitando os mesmos filtros da listagem."""
    from django.utils import timezone
    items = _collect_items(request)
    today = timezone.now().date().isoformat()
    return Response({
        "total": len(items),
        "tasks": sum(1 for i in items if i["type"] == "task"),
        "tickets": sum(1 for i in items if i["type"] == "ticket"),
        "bugs": sum(1 for i in items if i["type"] == "bug"),
        "improvements": sum(1 for i in items if i["type"] == "improvement"),
        "no_sprint": sum(1 for i in items if not i["sprint_id"]),
        "critical": sum(1 for i in items if i["priority"] in ("Critica", "Crítica")),
        "no_responsible": sum(1 for i in items if not i["responsible"]),
        "overdue": sum(1 for i in items if i["due_at"] and i["due_at"][:10] < today),
        "due_today": sum(1 for i in items if i["due_at"] and i["due_at"][:10] == today),
    })
