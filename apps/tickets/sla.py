"""SLA calculation utilities."""
import logging
from datetime import datetime, time, timedelta
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


def add_business_duration(start_dt, duration, company):
    """Advance start_dt by `duration` worth of business time."""
    from apps.tickets.business_hours_models import BusinessHours, CompanyHoliday

    bh_qs = BusinessHours.objects.filter(company=company, active=True)
    bh_map = {bh.weekday: bh for bh in bh_qs}
    holidays = set(
        CompanyHoliday.objects.filter(company=company, active=True).values_list("date", flat=True)
    )

    if not bh_map:
        return start_dt + duration

    remaining = duration
    current = start_dt

    while remaining.total_seconds() > 0:
        local_date = current.date()
        weekday = current.weekday()

        # Skip holidays and non-working days
        if local_date in holidays or weekday not in bh_map:
            # Jump to start of next day and retry
            current = datetime.combine(local_date + timedelta(days=1), time.min, tzinfo=current.tzinfo)
            continue

        bh = bh_map[weekday]
        day_start = current.replace(hour=bh.start_time.hour, minute=bh.start_time.minute, second=0, microsecond=0)
        day_end = current.replace(hour=bh.end_time.hour, minute=bh.end_time.minute, second=0, microsecond=0)

        # If we're before start of business, jump to start
        if current < day_start:
            current = day_start
            continue

        # If we're past end of business, jump to next day
        if current >= day_end:
            current = datetime.combine(local_date + timedelta(days=1), time.min, tzinfo=current.tzinfo)
            continue

        # Time available today from current position
        available_today = day_end - current

        if remaining <= available_today:
            return current + remaining
        else:
            remaining -= available_today
            current = datetime.combine(local_date + timedelta(days=1), time.min, tzinfo=current.tzinfo)

    return current


def _company_now(company):
    """Current time converted to the company's configured timezone (falls back to default)."""
    now = timezone.now()
    tz_name = getattr(company, "timezone", "") or ""
    if tz_name:
        try:
            from zoneinfo import ZoneInfo
            return now.astimezone(ZoneInfo(tz_name))
        except Exception:
            logger.warning("Invalid company timezone %r, using default.", tz_name)
    return timezone.localtime(now)


def _policy_specificity(policy, ticket) -> int:
    """Score how specific a policy is for the ticket: client > category > priority."""
    score = 0
    if policy.client_id and getattr(ticket, "client_id", None) == policy.client_id:
        score += 100
    if policy.subcategory and policy.subcategory == (getattr(ticket, "subcategory", "") or ""):
        score += 30
    if policy.category and policy.category == (ticket.category or ""):
        score += 10
    if policy.priority and policy.priority == (ticket.priority or ""):
        score += 1
    return score


def compute_sla_due_at(ticket) -> None:
    """Set ticket.sla_due_at based on the most specific matching SLAPolicy, or priority defaults."""
    start = _company_now(ticket.company)
    try:
        from apps.tickets.models import SLAPolicy
        candidates = list(
            SLAPolicy.objects.filter(company=ticket.company, active=True)
            .filter(models_filter(ticket))
        )
        if candidates:
            # Mais específico primeiro (cliente > categoria > prioridade); weight desempata.
            candidates.sort(
                key=lambda p: (_policy_specificity(p, ticket), p.priority_weight or 0),
                reverse=True,
            )
            policy = candidates[0]
            duration = parse_sla_duration(policy.response_time) or timedelta(hours=8)
            ticket.sla_due_at = add_business_duration(start, duration, ticket.company)
            return
    except Exception as exc:
        logger.exception("Error computing SLA from policy for ticket %s: %s", getattr(ticket, "id", "?"), exc)

    # Fall back to ticket.sla field
    duration = parse_sla_duration(ticket.sla)
    if not duration:
        duration = SLA_DEFAULTS.get(ticket.priority, timedelta(hours=8))
    ticket.sla_due_at = add_business_duration(start, duration, ticket.company)


def models_filter(ticket):
    """Build Q filter for SLAPolicy matching (priority, category and client scoping)."""
    from django.db.models import Q
    q = Q()
    if ticket.priority:
        q &= Q(priority=ticket.priority) | Q(priority="")
    if ticket.category:
        q &= Q(category=ticket.category) | Q(category="")
    # Política com subcategoria só casa com o chamado daquela subcategoria
    q &= Q(subcategory="") | Q(subcategory=(getattr(ticket, "subcategory", "") or ""))
    # Política de cliente só se aplica ao próprio cliente; políticas sem cliente valem para todos.
    client_id = getattr(ticket, "client_id", None)
    if client_id:
        q &= Q(client_id=client_id) | Q(client__isnull=True)
    else:
        q &= Q(client__isnull=True)
    return q


def check_sla_alerts(company):
    """Return tickets near or past SLA breach for a company."""
    from apps.tickets.models import Ticket
    now = timezone.now()
    # Antecedência de alerta proporcional à criticidade do chamado.
    warning_windows = {
        "Critica": timedelta(minutes=30),
        "Alta": timedelta(hours=1),
        "Media": timedelta(hours=2),
        "Baixa": timedelta(hours=4),
    }
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
    fields = ["id", "code", "title", "priority", "sla_due_at", "responsible_technician_id"]
    breached = list(qs.filter(sla_due_at__lt=now).values(*fields))
    warning = [
        t for t in qs.filter(sla_due_at__gte=now).values(*fields)
        if t["sla_due_at"] <= now + warning_windows.get(t["priority"], timedelta(hours=1))
    ]
    return {"breached": breached, "warning": warning}
