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
    "Backlog":               {"edit", "priority", "responsible", "team", "sprint", "cancel"},
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
    "Aberto": {"Triagem", "Aguardando Aprovacao", "Cancelado", "Backlog"},
    "Triagem": {"Aguardando Aprovacao", "Aprovado", "Reprovado", "Backlog", "Aguardando atendimento", "Cancelado"},
    "Aguardando Aprovacao": {"Aprovado", "Reprovado", "Cancelado"},
    "Aprovado": {"Backlog", "Aguardando atendimento", "Em atendimento"},
    "Reprovado": set(),
    "Backlog": {"Aguardando atendimento", "Em atendimento", "Cancelado"},
    "Aguardando atendimento": {"Em atendimento", "Backlog", "Cancelado"},
    "Em atendimento": {"Aguardando cliente", "Validacao", "Pausado", "Finalizado", "Cancelado"},
    "Aguardando cliente": {"Em atendimento", "Pausado", "Cancelado"},
    "Validacao": {"Em atendimento", "Finalizado"},
    "Pausado": {"Em atendimento", "Cancelado"},
    "Cancelado": set(),
    "Finalizado": set(),
}

TICKET_SPRINT_ELIGIBLE = {"Triagem", "Aprovado", "Backlog", "Aguardando atendimento", "Em atendimento"}

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
    """Valida um PATCH de chamado contra a matriz de status."""
    status = ticket.status or "Aberto"
    new_status = data.get("status")

    if status in TICKET_FINAL:
        # Encerrados: nada muda via PATCH (reabertura só pelo endpoint /reopen/)
        blocked = {"status", "priority", "responsible_technician", "sprint", "title",
                   "description", "category", "team", "due_at", "est_hours"}
        touched = blocked & set(data.keys())
        if touched:
            label = "finalizados" if status == "Finalizado" else status.lower() + "s"
            _err(f"Chamados {label} não podem ser editados. Reabra o chamado para alterar.")

    if new_status and new_status != status:
        allowed = TICKET_TRANSITIONS.get(status, set())
        if new_status not in allowed:
            _err(f"Não é permitido mover o chamado de '{status}' para '{new_status}'.")

    if "sprint" in data and data.get("sprint"):
        if status not in TICKET_SPRINT_ELIGIBLE:
            _err(f"Chamados em '{status}' não podem ser enviados para uma sprint. "
                 "Apenas chamados em Triagem, Aprovado, Backlog, Aguardando atendimento ou Em atendimento.")

    if "priority" in data and status == "Validacao":
        _err("A prioridade não pode ser alterada durante a validação.")

    if "responsible_technician" in data and status == "Aguardando Aprovacao":
        _err("Atribua o técnico após a aprovação do chamado.")


def validate_activity_update(activity, data: dict):
    """Valida um PATCH de atividade contra a matriz de status."""
    status = activity.status or "Backlog"
    new_status = data.get("status")

    if status in ACTIVITY_DONE:
        blocked = {"status", "priority", "assignee", "sprint", "title", "description",
                   "est_hours", "story_points", "due_at"}
        touched = blocked & set(data.keys())
        if touched:
            _err("Atividades concluídas não podem ser alteradas. Reabra a atividade para continuar.")

    if new_status and new_status != status:
        if new_status in ACTIVITY_DONE and status != "Em revisao":
            # Conclusão sem revisão só pelo endpoint /resolve/ (que documenta a resolução)
            _err("Conclua a atividade pelo fluxo de resolução (Execução → Finalizar) ou envie para revisão antes.")
        allowed = ACTIVITY_TRANSITIONS.get(status, set())
        if new_status not in allowed and new_status not in ACTIVITY_DONE:
            _err(f"Não é permitido mover a atividade de '{status}' para '{new_status}'.")

    if "sprint" in data and data.get("sprint"):
        if status not in ACTIVITY_SPRINT_ELIGIBLE:
            _err(f"Atividades em '{status}' não podem ser enviadas para uma sprint.")

    if new_status == "Em progresso" and not (data.get("assignee") or activity.assignee_id):
        _err("Defina um responsável antes de iniciar o progresso da atividade.")
