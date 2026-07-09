"""Fonte ÚNICA de verdade para os itens de uma sprint (atividades + chamados + bugs).

Usada por Planejamento, Kanban e indicadores — todos consomem os MESMOS itens,
com a MESMA coluna de kanban e os MESMOS totais. Nenhum item é descartado: status
sem coluna cai em 'Não mapeado'.
"""

# Colunas oficiais do kanban da sprint (para ATIVIDADES).
ACTIVITY_KANBAN_COLUMNS = ["Backlog", "A fazer", "Em progresso", "Em revisão", "Bloqueado", "Concluído"]

# Mapeia o status real da atividade (com variações de acento/grafia) para a coluna.
_ACTIVITY_STATUS_TO_COLUMN = {
    "backlog": "Backlog",
    "a fazer": "A fazer",
    "afazer": "A fazer",
    "todo": "A fazer",
    "em progresso": "Em progresso",
    "em andamento": "Em progresso",
    "in progress": "Em progresso",
    "em revisao": "Em revisão",
    "em revisão": "Em revisão",
    "review": "Em revisão",
    "homologacao": "Em revisão",
    "homologação": "Em revisão",
    "bloqueado": "Bloqueado",
    "pausado": "Bloqueado",
    "blocked": "Bloqueado",
    "concluido": "Concluído",
    "concluído": "Concluído",
    "concluída": "Concluído",
    "concluida": "Concluído",
    "done": "Concluído",
    "finalizado": "Concluído",
}

DONE_COLUMN = "Concluído"


def activity_kanban_column(status: str) -> str:
    """Coluna do kanban para o status da atividade. Nunca descarta: fallback 'Não mapeado'."""
    key = (status or "").strip().lower()
    return _ACTIVITY_STATUS_TO_COLUMN.get(key, "Não mapeado")


def _activity_type(activity) -> str:
    t = (getattr(activity, "type", "") or "").lower()
    if t == "bug":
        return "bug"
    return "activity"


def build_sprint_items(sprint) -> dict:
    """Retorna todos os itens da sprint com status/coluna/horas normalizados + totais."""
    from apps.sprints.models import SprintActivityPlan, SprintTicketPlan
    from apps.activities.models import ActivityTimeEntry
    from apps.tickets.models import TicketTimeEntry

    a_plans = list(
        SprintActivityPlan.objects.filter(sprint=sprint, deleted_at__isnull=True)
        .select_related("activity", "activity__assignee")
    )
    t_plans = list(
        SprintTicketPlan.objects.filter(sprint=sprint, deleted_at__isnull=True)
        .select_related("ticket", "ticket__responsible_technician")
    )

    # Horas executadas agregadas por item.
    act_ids = [p.activity_id for p in a_plans if p.activity_id]
    tkt_ids = [p.ticket_id for p in t_plans if p.ticket_id]
    act_hours = {}
    for e in ActivityTimeEntry.objects.filter(sprint=sprint, activity_id__in=act_ids, deleted_at__isnull=True):
        act_hours[e.activity_id] = act_hours.get(e.activity_id, 0) + float(e.hours or 0)
    tkt_hours = {}
    for e in TicketTimeEntry.objects.filter(ticket_id__in=tkt_ids, deleted_at__isnull=True):
        tkt_hours[e.ticket_id] = tkt_hours.get(e.ticket_id, 0) + float(e.hours or 0)

    items = []
    n_activities = n_bugs = n_tickets = 0

    for p in a_plans:
        a = p.activity
        if not a:
            continue
        itype = _activity_type(a)
        if itype == "bug":
            n_bugs += 1
        else:
            n_activities += 1
        items.append({
            "id": str(a.id),
            "plan_id": str(p.id),
            "type": itype,
            "title": a.title,
            "code": (str(a.id)[:8]).upper(),
            "status": a.status or "Backlog",
            "kanban_column": activity_kanban_column(a.status),
            "priority": p.priority or a.priority or "Média",
            "assignee_ids": [str(x) for x in (p.responsible_ids or [])] or (
                [str(a.assignee_id)] if a.assignee_id else []
            ),
            "assignee_name": a.assignee.full_name_or_username if a.assignee_id else "",
            "planned_hours": float(p.planned_hours or 0),
            "executed_hours": round(act_hours.get(a.id, 0), 2),
            "story_points": p.story_points,
            "project_name": a.project.name if a.project_id else "",
        })

    for p in t_plans:
        t = p.ticket
        if not t:
            continue
        n_tickets += 1
        items.append({
            "id": str(t.id),
            "plan_id": str(p.id),
            "type": "ticket",
            "title": t.title,
            "code": t.code or str(t.id)[:8],
            "status": t.status or "Aberto",
            "kanban_column": t.status or "Aberto",  # chamados usam o próprio workflow
            "priority": p.priority or t.priority or "Media",
            "assignee_ids": [str(x) for x in (p.responsible_ids or [])] or (
                [str(t.responsible_technician_id)] if t.responsible_technician_id else []
            ),
            "assignee_name": t.responsible_technician.full_name_or_username if t.responsible_technician_id else "",
            "planned_hours": float(p.planned_hours or 0),
            "executed_hours": round(tkt_hours.get(t.id, 0), 2),
            "story_points": p.story_points,
            "project_name": t.client.name if t.client_id else "",
        })

    return {
        "sprint_id": str(sprint.id),
        "items": items,
        "totals": {
            "activities": n_activities,
            "tickets": n_tickets,
            "bugs": n_bugs,
            "total": len(items),
        },
    }
