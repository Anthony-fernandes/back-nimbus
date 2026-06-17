"""Regras de aprovacao de chamados.

Ordem de avaliacao quando a categoria exige aprovacao:

* Regra 3 - Aprovacao automatica por cargo (``Position.auto_approval`` ou
  ``approval_mode == "AUTO"``): o chamado e aprovado imediatamente.
* Regra 1 - Aprovador vinculado (supervisor/gerente do solicitante).
* Regra 2 - Aprovacao pela equipe de chamados (Service Desk) quando o
  solicitante nao possui aprovador vinculado.
"""

from __future__ import annotations

from typing import Any


def get_category(ticket: Any):
    from .models import TicketCategory

    if not ticket.category:
        return None
    return TicketCategory.objects.filter(company=ticket.company, name=ticket.category).first()


def requires_approval(ticket: Any) -> tuple[bool, Any]:
    category = get_category(ticket)
    return bool(category and category.approval_required), category


def resolve_approval_plan(ticket: Any) -> dict:
    """Retorna o plano de aprovacao inicial do chamado."""

    required, _category = requires_approval(ticket)
    if not required:
        return {
            "route": "NONE",
            "approver": None,
            "status": "Nao requerido",
            "reason": "Categoria nao exige aprovacao.",
        }

    requester = ticket.requester_user

    # Regra 3 - Aprovacao automatica por cargo.
    if requester and (
        (requester.position_id and getattr(requester.position, "auto_approval", False))
        or requester.approval_mode == "AUTO"
    ):
        return {
            "route": "AUTO",
            "approver": None,
            "status": "Aprovado",
            "reason": "Aprovacao automatica por cargo do solicitante.",
        }

    # Regra 1 - Aprovador vinculado (supervisor/gerente).
    approver = None
    if requester:
        mode = requester.approval_mode
        if mode == "MANAGER":
            approver = requester.manager or requester.supervisor
        elif mode == "SUPERVISOR":
            approver = requester.supervisor or requester.manager
        elif mode == "SERVICE_DESK":
            approver = None
        else:  # INHERITED
            approver = requester.supervisor or requester.manager

    if approver:
        return {
            "route": "APPROVER",
            "approver": approver,
            "status": "Aguardando Aprovacao",
            "reason": "Encaminhado ao aprovador vinculado.",
        }

    # Regra 2 - Equipe de chamados (Service Desk).
    return {
        "route": "SERVICE_DESK",
        "approver": None,
        "status": "Aguardando Aprovacao",
        "reason": "Encaminhado a equipe de chamados (Service Desk).",
    }


def service_desk_approvers(company: Any) -> list:
    from apps.users.models import User

    if company is None:
        return []
    return list(
        User.objects.filter(company=company, is_service_desk_approver=True, is_active=True)
    )
