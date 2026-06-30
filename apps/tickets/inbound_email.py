"""Inbound email webhook: parse and create tickets."""
import logging
from django.utils import timezone
from .models import Ticket

logger = logging.getLogger(__name__)

def process_inbound_email(company, subject: str, body: str, from_email: str, html_body: str = ""):
    """Create a ticket from an inbound email."""
    from apps.users.models import User
    title = (subject or "Sem assunto")[:200]
    description = body or html_body or ""
    requester = None
    try:
        requester = User.objects.filter(company=company, email=from_email, deleted_at__isnull=True).first()
    except Exception:
        pass

    ticket = Ticket(
        company=company,
        title=title,
        description=description,
        source="email",
        status="Aberto",
        priority="Media",
        type="Requisição",
        requester_user=requester,
    )
    ticket.save()
    logger.info("Created ticket %s from inbound email <%s>", ticket.code, from_email)
    return ticket
