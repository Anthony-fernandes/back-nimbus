"""SLA calculation utilities."""
import logging
from datetime import timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)


SLA_DEFAULTS = {
    "Critica": timedelta(hours=2),
    "Alta": timedelta(hours=4),
    "Media": timedelta(hours=8),
    "Baixa": timedelta(hours=24),
}


def parse_sla_duration(sla_str: str) -> timedelta | None:
    """Parse strings like '4h', '2d', '30m' into timedelta."""
    if not sla_str:
        return None
    sla_str = sla_str.strip().lower()
    try:
        if sla_str.endswith("h"):
            return timedelta(hours=int(sla_str[:-1]))
        if sla_str.endswith("d"):
            return timedelta(days=int(sla_str[:-1]))
        if sla_str.endswith("m"):
            return timedelta(minutes=int(sla_str[:-1]))
    except ValueError:
        logger.warning("Could not parse SLA duration string: %r", sla_str)
    return None


def compute_sla_due_at(ticket) -> None:
    """Set ticket.sla_due_at based on SLAPolicy or priority defaults."""
    # Try to find a company SLAPolicy for this category+priority
    try:
        from apps.tickets.models import SLAPolicy
        policy = SLAPolicy.objects.filter(
            company=ticket.company,
            active=True,
        ).filter(
            models_filter(ticket)
        ).order_by("-priority_weight").first()
        if policy:
            duration = parse_sla_duration(policy.response_time) or timedelta(hours=8)
            ticket.sla_due_at = timezone.now() + duration
            return
    except Exception as exc:
        logger.exception("Error computing SLA from policy for ticket %s: %s", getattr(ticket, "id", "?"), exc)

    # Fall back to ticket.sla field
    duration = parse_sla_duration(ticket.sla)
    if not duration:
        duration = SLA_DEFAULTS.get(ticket.priority, timedelta(hours=8))
    ticket.sla_due_at = timezone.now() + duration


def models_filter(ticket):
    """Build Q filter for SLAPolicy matching."""
    from django.db.models import Q
    q = Q()
    if ticket.priority:
        q &= Q(priority=ticket.priority) | Q(priority="")
    if ticket.category:
        q &= Q(category=ticket.category) | Q(category="")
    return q


def check_sla_alerts(company):
    """Return tickets near or past SLA breach for a company."""
    from apps.tickets.models import Ticket
    now = timezone.now()
    warning_threshold = now + timedelta(hours=1)
    open_statuses = [
        "Aberto", "Triagem", "Backlog", "Aguardando atendimento",
        "Em atendimento", "Aguardando cliente", "Validacao",
    ]
    qs = Ticket.objects.filter(
        company=company,
        deleted_at__isnull=True,
        sla_due_at__isnull=False,
        status__in=open_statuses,
    )
    breached = list(qs.filter(sla_due_at__lt=now).values(
        "id", "code", "title", "priority", "sla_due_at", "responsible_technician_id"
    ))
    warning = list(qs.filter(sla_due_at__gte=now, sla_due_at__lte=warning_threshold).values(
        "id", "code", "title", "priority", "sla_due_at", "responsible_technician_id"
    ))
    return {"breached": breached, "warning": warning}
