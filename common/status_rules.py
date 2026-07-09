"""Matriz central de ações permitidas por status para Chamados e Atividades.

Usada pelos viewsets para impedir ações incoerentes mesmo via API direta.
As mesmas regras existem no frontend em src/lib/workItemRules.ts.
"""
from rest_framework.exceptions import ValidationError

# ── Chamados ────────────────────────────────────────────────────────
TICKET_FINAL = {"Finalizado", "Cancelado", "Reprovado"}

# Ações operacionais permitidas por status
TICKET_ACTIONS = {
    "Aberto":                {"edit", "priority", "responsible", "team", "cancel"},
    "Triagem":               {"edit", "priority", "responsible", "team", "approve", "reject", "cancel", "sprint"},
    "Aguardando Aprovacao":  {"approve", "reject", "cancel"},
    "Aprovado":              {"responsible", "team", "sprint", "priority"},
    "Reprovado":             {"reopen"},
    "Aguardando atendimento": {"edit", "start", "priority", "responsible", "team", "sprint", "cancel"},
    "Em atendimento":        {"edit", "pause", "wait_customer", "validate", "resolve", "cancel", "responsible", "sprint", "priority"},
    "Aguardando cliente":    {"resume", "pause", "cancel", "responsible"},
    "Validacao":             {"resolve", "resume", "reject_solution"},
    "Pausado":               {"resume", "cancel"},
    "Cancelado":             {"reopen"},
    "Finalizado":            {"reopen"},
}

# Transições de status permitidas via PATCH direto
TICKET_TRANSITIONS = {
    "Aberto": {"Triagem", "Aguardando Aprovacao", "Cancelado"},
    "Triagem": {"Aguardando Aprovacao", "Aprovado", "Reprovado", "Aguardando atendimento", "Cancelado"},
    "Aguardando Aprovacao": {"Aprovado", "Reprovado", "Cancelado"},
    "Aprovado": {"Aguardando atendimento", "Em atendimento"},
    "Reprovado": set(),
    "Aguardando atendimento": {"Em atendimento", "Cancelado"},
    "Em atendimento": {"Aguardando cliente", "Validacao", "Pausado", "Finalizado", "Cancelado"},
    "Aguardando cliente": {"Em atendimento", "Pausado", "Cancelado"},
    "Validacao": {"Em atendimento", "Finalizado"},
    "Pausado": {"Em atendimento", "Cancelado"},
    "Cancelado": set(),
    "Finalizado": set(),
}

TICKET_SPRINT_ELIGIBLE = {"Triagem", "Aprovado", "Aguardando atendimento", "Em atendimento"}

# ── Atividades ──────────────────────────────────────────────────────
ACTIVITY_DONE = {"Concluída", "Concluido", "Concluído", "Done", "Cancelada", "Cancelado"}

ACTIVITY_TRANSITIONS = {
    "Backlog": {"A fazer", "Em progresso"},
    "A fazer": {"Em progresso", "Backlog", "Bloqueado"},
    "Em progresso": {"Em revisao", "Bloqueado", "A fazer"},
    "Em revisao": {"Em progresso", "Concluída", "Concluido", "Concluído"},
    "Bloqueado": {"A fazer", "Em progresso"},
}

ACTIVITY_SPRINT_ELIGIBLE = {"Backlog", "A fazer", "Em progresso", "Bloqueado"}


def _err(msg):
    raise ValidationError({"detail": msg})


def validate_ticket_update(ticket, data: dict):
    """Valida um PATCH de chamado contra a regra efetiva do status (builtin ou workflow)."""
    status = ticket.status or "Aberto"
    rule = resolve_status_rule(ticket.company, "ticket", status)
    if not rule["found"]:
        _err(f"O status '{status}' não possui regras configuradas. "
             "Configure este status no workflow em Configurações antes de operar chamados nele.")

    new_status = data.get("status")
    perms = rule["permissions"]

    if rule["is_final"]:
        blocked = {"status", "priority", "responsible_technician", "sprint", "title",
                   "description", "category", "team", "due_at", "est_hours"}
        if blocked & set(data.keys()):
            _err("Chamados encerrados não podem ser editados. Reabra o chamado para alterar.")

    if new_status and new_status != status:
        if new_status not in rule["transitions"]:
            _err(f"Não é permitido mover o chamado de '{status}' para '{new_status}'. "
                 f"Transições permitidas: {', '.join(rule['transitions']) or 'nenhuma'}.")
        target = resolve_status_rule(ticket.company, "ticket", new_status)
        if target["found"] and target["requirements"].get("requires_reason") and not data.get("status_change_reason"):
            _err(f"O status '{new_status}' exige um motivo para a transição.")
        # Exigir técnico: por requirement configurado OU regra crítica builtin
        # (chamado não pode entrar em atendimento sem responsável).
        needs_assignee = target["found"] and target["requirements"].get("requires_assignee")
        if new_status == "Em atendimento":
            needs_assignee = True
        if needs_assignee and not (
            data.get("responsible_technician") or ticket.responsible_technician_id
        ):
            _err(f"Defina um técnico responsável antes de mover para '{new_status}'.")

    if "sprint" in data and data.get("sprint") and not perms.get("allows_send_to_sprint"):
        _err(f"Chamados em '{status}' não podem ser enviados para uma sprint.")

    if "priority" in data and not perms.get("allows_priority_change"):
        _err(f"A prioridade não pode ser alterada com o chamado em '{status}'.")

    if "responsible_technician" in data and not perms.get("allows_assignment"):
        _err(f"O responsável não pode ser alterado com o chamado em '{status}'.")

    operational = {"title", "description", "category", "team", "due_at", "est_hours"}
    if (operational & set(data.keys())) and not perms.get("allows_edit"):
        _err(f"Chamados em '{status}' não podem ser editados.")


def validate_activity_update(activity, data: dict):
    """Valida um PATCH de atividade contra a regra efetiva do status."""
    status = activity.status or "Backlog"
    rule = resolve_status_rule(activity.company, "activity", status)
    if not rule["found"]:
        _err(f"O status '{status}' não possui regras configuradas. "
             "Configure este status no workflow em Configurações antes de operar atividades nele.")

    new_status = data.get("status")
    perms = rule["permissions"]

    # Backlog é status de item NÃO planejado: atividade vinculada a sprint não pode ficar em Backlog
    incoming_sprint = data.get("sprint", "__unset__")
    will_have_sprint = (
        bool(incoming_sprint) if incoming_sprint != "__unset__" else bool(activity.sprint_id)
    )
    if new_status == "Backlog" and will_have_sprint:
        _err("Atividade planejada em sprint não pode voltar para 'Backlog'. Remova-a da sprint primeiro.")

    if rule["is_final"]:
        blocked = {"status", "priority", "assignee", "sprint", "title", "description",
                   "est_hours", "story_points", "due_at"}
        if blocked & set(data.keys()):
            _err("Atividades concluídas não podem ser alteradas. Reabra a atividade para continuar.")

    if new_status and new_status != status:
        target = resolve_status_rule(activity.company, "activity", new_status)
        if target["found"] and target["is_final"] and status != "Em revisao":
            _err("Conclua a atividade pelo fluxo de resolução (Execução → Finalizar) ou envie para revisão antes.")
        if new_status not in rule["transitions"] and not (target["found"] and target["is_final"]):
            _err(f"Não é permitido mover a atividade de '{status}' para '{new_status}'.")
        if target["found"] and target["requirements"].get("requires_reason") and not data.get("status_reason"):
            _err(f"O status '{new_status}' exige um motivo para a transição.")

    if "sprint" in data and data.get("sprint") and not perms.get("allows_send_to_sprint"):
        _err(f"Atividades em '{status}' não podem ser enviadas para uma sprint.")

    if "priority" in data and not perms.get("allows_priority_change"):
        _err(f"A prioridade não pode ser alterada com a atividade em '{status}'.")

    if new_status == "Em progresso" and not (data.get("assignee") or activity.assignee_id):
        _err("Defina um responsável antes de iniciar o progresso da atividade.")


# ── Workflow configurável (TicketWorkflowStatus) ────────────────────

ALL_PERMS = [
    "allows_edit", "allows_comment", "allows_attachment", "allows_assignment",
    "allows_priority_change", "allows_send_to_sprint", "allows_backlog",
    "allows_start_work", "allows_pause", "allows_resume",
    "allows_send_to_validation", "allows_finish", "allows_cancel", "allows_reopen",
]
ALL_REQS = [
    "requires_reason", "requires_comment", "requires_assignee",
    "requires_resolution", "requires_approval",
]

# Sugestões de permissão por fase — aplicadas quando o status não define as suas
PHASE_DEFAULTS = {
    "entrada": {"allows_edit": True, "allows_comment": True, "allows_attachment": True,
                "allows_assignment": True, "allows_priority_change": True,
                "allows_backlog": True, "allows_cancel": True},
    "triagem": {"allows_edit": True, "allows_comment": True, "allows_attachment": True,
                "allows_assignment": True, "allows_priority_change": True,
                "allows_send_to_sprint": True, "allows_backlog": True,
                "allows_start_work": True, "allows_cancel": True},
    "aprovacao": {"allows_comment": True, "allows_attachment": True, "allows_cancel": True},
    "atendimento": {"allows_edit": True, "allows_comment": True, "allows_attachment": True,
                    "allows_assignment": True, "allows_priority_change": True,
                    "allows_send_to_sprint": True, "allows_pause": True,
                    "allows_send_to_validation": True, "allows_finish": True,
                    "allows_cancel": True},
    "aguardando_terceiro": {"allows_comment": True, "allows_attachment": True,
                            "allows_resume": True, "allows_pause": True,
                            "allows_cancel": True},
    "validacao": {"allows_comment": True, "allows_finish": True, "allows_resume": True},
    "pausado": {"allows_comment": True, "allows_attachment": True,
                "allows_resume": True, "allows_cancel": True},
    "final": {"allows_comment": True, "allows_reopen": True},
}

# Mapeia os status builtin para fases (para responder available-actions uniformemente)
BUILTIN_TICKET_PHASES = {
    "Aberto": "entrada", "Triagem": "triagem", "Aguardando Aprovacao": "aprovacao",
    "Aprovado": "triagem", "Reprovado": "final",
    "Aguardando atendimento": "triagem", "Em atendimento": "atendimento",
    "Aguardando cliente": "aguardando_terceiro", "Validacao": "validacao",
    "Pausado": "pausado", "Cancelado": "final", "Finalizado": "final",
}
BUILTIN_ACTIVITY_PHASES = {
    "Backlog": "entrada", "A fazer": "triagem", "Em progresso": "atendimento",
    "Em revisao": "validacao", "Bloqueado": "pausado",
    "Concluída": "final", "Concluido": "final", "Concluído": "final",
    "Cancelado": "final", "Cancelada": "final",
}


def resolve_status_rule(company, item_type: str, status_name: str):
    """Retorna a regra efetiva de um status: builtin ou configurada no workflow.

    Shape: {found, is_final, phase, permissions, requirements, transitions}
    """
    from apps.tickets.models import TicketWorkflowStatus

    builtin_phases = BUILTIN_TICKET_PHASES if item_type == "ticket" else BUILTIN_ACTIVITY_PHASES
    transitions_map = TICKET_TRANSITIONS if item_type == "ticket" else ACTIVITY_TRANSITIONS

    row = (
        TicketWorkflowStatus.objects.filter(
            company=company, item_type=item_type, deleted_at__isnull=True, active=True,
        )
        .filter(name=status_name)
        .first()
    )
    if row:
        phase = row.phase or builtin_phases.get(status_name, "")
        perms = dict(PHASE_DEFAULTS.get(phase, {}))
        perms.update({k: v for k, v in (row.permissions or {}).items() if k in ALL_PERMS})
        reqs = {k: v for k, v in (row.requirements or {}).items() if k in ALL_REQS}
        is_final = bool(row.is_final or phase == "final")
        if is_final:
            # Regras críticas: status final nunca libera edição operacional/sprint
            for k in ("allows_edit", "allows_assignment", "allows_priority_change",
                      "allows_send_to_sprint", "allows_start_work", "allows_finish"):
                perms[k] = False
            perms["allows_reopen"] = True
        return {
            "found": True,
            "custom": True,
            "is_final": is_final,
            "phase": phase,
            "permissions": {k: bool(perms.get(k)) for k in ALL_PERMS},
            "requirements": {k: bool(reqs.get(k)) for k in ALL_REQS},
            "transitions": list(row.next_statuses or []),
        }

    if status_name in builtin_phases:
        phase = builtin_phases[status_name]
        perms = dict(PHASE_DEFAULTS.get(phase, {}))
        return {
            "found": True,
            "custom": False,
            "is_final": phase == "final",
            "phase": phase,
            "permissions": {k: bool(perms.get(k)) for k in ALL_PERMS},
            "requirements": {},
            "transitions": sorted(transitions_map.get(status_name, set())),
        }

    return {"found": False, "custom": False, "is_final": False, "phase": "",
            "permissions": {}, "requirements": {}, "transitions": []}
