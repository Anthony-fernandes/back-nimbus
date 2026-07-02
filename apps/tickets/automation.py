"""Ticket automation rule evaluation engine."""
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

TRIGGER_CHOICES = [
    ("on_create", "Ao criar chamado"),
    ("on_update", "Ao atualizar chamado"),
    ("on_status_change", "Ao mudar status"),
    ("on_sla_breach", "Ao violar SLA"),
]

ACTION_CHOICES = [
    ("set_priority", "Definir prioridade"),
    ("set_status", "Definir status"),
    ("set_category", "Definir categoria"),
    ("assign_technician", "Atribuir técnico"),
    ("assign_team", "Atribuir equipe"),
    ("add_tag", "Adicionar tag"),
    ("send_notification", "Enviar notificação"),
]

CONDITION_FIELD_CHOICES = [
    ("priority", "Prioridade"),
    ("status", "Status"),
    ("category", "Categoria"),
    ("type", "Tipo"),
    ("source", "Canal"),
]

CONDITION_OP_CHOICES = [
    ("eq", "igual a"),
    ("neq", "diferente de"),
    ("in", "está em (lista separada por vírgula)"),
    ("contains", "contém"),
]

def evaluate_condition(condition: dict, ticket) -> bool:
    field = condition.get("field")
    op = condition.get("op")
    value = condition.get("value", "")
    ticket_value = str(getattr(ticket, field, "") or "")
    if op == "eq":
        return ticket_value == value
    if op == "neq":
        return ticket_value != value
    if op == "in":
        return ticket_value in [v.strip() for v in value.split(",")]
    if op == "contains":
        return value.lower() in ticket_value.lower()
    return False

def evaluate_rules(ticket, trigger: str):
    """Evaluate all active automation rules for a ticket on a given trigger."""
    from .models import TicketAutomationRule
    from apps.notifications.services import notify
    from apps.users.models import User
    from apps.teams.models import Team

    rules = TicketAutomationRule.objects.filter(
        company=ticket.company,
        trigger=trigger,
        active=True,
    ).order_by("order")

    for rule in rules:
        try:
            conditions = rule.conditions or []
            if all(evaluate_condition(c, ticket) for c in conditions):
                _apply_action(rule, ticket, notify, User, Team)
        except Exception as exc:
            logger.warning("Automation rule %s failed: %s", rule.id, exc)

def _apply_action(rule, ticket, notify, User, Team):
    action = rule.action
    value = rule.action_value or ""
    changed = []
    recompute_sla = False
    if action == "set_priority" and value:
        ticket.priority = value
        changed.append("priority")
        recompute_sla = True
    elif action == "set_status" and value:
        ticket.status = value
        changed.append("status")
    elif action == "set_category" and value:
        ticket.category = value
        changed.append("category")
        recompute_sla = True
    elif action == "add_tag" and value:
        tags = list(ticket.tags or [])
        new_tags = [t.strip() for t in value.split(",") if t.strip()]
        for tag in new_tags:
            if tag not in tags:
                tags.append(tag)
        if tags != (ticket.tags or []):
            ticket.tags = tags
            changed.append("tags")
    elif action == "assign_technician" and value:
        try:
            user = User.objects.get(id=value, company=ticket.company)
            ticket.responsible_technician = user
            changed.append("responsible_technician")
        except User.DoesNotExist:
            pass
    elif action == "assign_team" and value:
        try:
            team = Team.objects.get(id=value, company=ticket.company)
            ticket.team = team
            changed.append("team")
        except Team.DoesNotExist:
            pass
    elif action == "send_notification":
        # Notifica o técnico responsável; sem responsável, notifica quem criou o chamado.
        recipient = ticket.responsible_technician or getattr(ticket, "created_by", None)
        if recipient:
            notify(
                recipient,
                title=f"Automação: {rule.name}",
                event="ticket.automation",
                category="Chamados",
                message=value or f"Regra de automação '{rule.name}' ativada no chamado {ticket.code}.",
                link=f"tickets/{ticket.id}",
                company=ticket.company,
                send_email=False,
            )
    if recompute_sla:
        try:
            from .sla import compute_sla_due_at
            compute_sla_due_at(ticket)
            if "sla_due_at" not in changed:
                changed.append("sla_due_at")
        except Exception as exc:
            logger.warning("SLA recompute failed for ticket %s: %s", ticket.id, exc)
    if changed:
        ticket.save(update_fields=changed + ["updated_at"])
