"""Helpers de auditoria global da plataforma.

Qualquer acao critica do sistema deve ser registrada por meio de
``record_audit`` para garantir rastreabilidade completa (usuario, data,
hora, acao, valor anterior, valor novo e origem da alteracao).
"""

from __future__ import annotations

from typing import Any, Iterable


def _client_ip(request: Any) -> str | None:
    if request is None:
        return None

    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")


def _safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def build_changes(before: dict, after: dict, fields: Iterable[str]) -> list[dict]:
    """Monta a lista de alteracoes (valor anterior/novo) entre dois estados."""

    changes: list[dict] = []
    for field in fields:
        old = before.get(field)
        new = after.get(field)
        if old != new:
            changes.append({"field": field, "old": _safe(old), "new": _safe(new)})
    return changes


def record_audit(
    *,
    action: str,
    actor: Any = None,
    company: Any = None,
    instance: Any = None,
    entity_type: str = "",
    entity_id: str = "",
    entity_label: str = "",
    description: str = "",
    changes: list | None = None,
    origin: str = "",
    request: Any = None,
    metadata: dict | None = None,
):
    """Cria um registro de auditoria.

    Importacao do modelo e feita de forma tardia para evitar dependencias
    circulares durante a carga dos apps.
    """

    from apps.audit.models import AuditLog

    if actor is None and request is not None:
        candidate = getattr(request, "user", None)
        if candidate is not None and getattr(candidate, "is_authenticated", False):
            actor = candidate

    if company is None:
        company = getattr(actor, "company", None) or getattr(instance, "company", None)

    if instance is not None:
        entity_type = entity_type or instance.__class__.__name__
        entity_id = entity_id or str(getattr(instance, "id", "") or "")
        entity_label = entity_label or str(instance)[:255]

    return AuditLog.objects.create(
        action=action,
        actor=actor if getattr(actor, "pk", None) else None,
        actor_name=(
            getattr(actor, "full_name_or_username", "")
            or getattr(actor, "username", "")
            or ""
        ),
        company=company,
        entity_type=entity_type or "",
        entity_id=str(entity_id or ""),
        entity_label=entity_label or "",
        description=description or "",
        changes=changes or [],
        origin=origin or (getattr(request, "method", "") if request is not None else "") or "",
        ip_address=_client_ip(request),
        metadata=metadata or {},
    )
