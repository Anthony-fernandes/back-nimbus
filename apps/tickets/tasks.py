import logging

from config.celery import app

logger = logging.getLogger(__name__)


@app.task(name="apps.tickets.tasks.check_sla_task")
def check_sla_task():
    """Check SLA deadlines for all companies and send notifications."""
    from apps.companies.models import Company
    from apps.notifications.services import notify
    from apps.users.models import User
    from .sla import check_sla_alerts

    companies = Company.objects.filter(deleted_at__isnull=True)
    total_breached = 0
    total_warning = 0

    for company in companies:
        try:
            alerts = check_sla_alerts(company)
            breached = alerts.get("breached", [])
            warning = alerts.get("warning", [])
            total_breached += len(breached)
            total_warning += len(warning)

            for ticket_data in breached:
                tech_id = ticket_data.get("responsible_technician_id")
                if not tech_id:
                    continue
                try:
                    tech = User.objects.get(id=tech_id)
                    notify(
                        tech,
                        title=f"SLA vencido: {ticket_data.get('code', '')} – {ticket_data.get('title', '')[:60]}",
                        event="ticket.sla_breached",
                        category="SLA",
                        message=f"O chamado {ticket_data.get('code')} ultrapassou o prazo de SLA.",
                        link=f"tickets/{ticket_data.get('id')}",
                        company=company,
                        send_email=False,
                    )
                except User.DoesNotExist:
                    pass

                # SLA Escalation: escalate priority to Critica if not already
                ticket_id = ticket_data.get("id")
                if ticket_id:
                    try:
                        from .models import Ticket
                        from common.audit import record_audit
                        ticket = Ticket.objects.select_related('responsible_technician').get(id=ticket_id)
                        if ticket.priority != "Critica":
                            ticket.priority = "Critica"
                            ticket.save(update_fields=["priority", "updated_at"])
                            record_audit(
                                action="ticket.sla_escalated",
                                instance=ticket,
                                description=f"Chamado {ticket.code} escalado para prioridade Critica por violacao de SLA.",
                                origin="tickets",
                            )
                            if ticket.responsible_technician:
                                notify(
                                    ticket.responsible_technician,
                                    title=f"Chamado escalado: {ticket.code}",
                                    event="ticket.sla_escalated",
                                    category="SLA",
                                    message=f"O chamado {ticket.code} foi escalado para prioridade CRITICA por violacao de SLA.",
                                    link=f"tickets/{ticket_id}",
                                    company=company,
                                    send_email=True,
                                )
                    except Exception as exc:
                        logger.warning("SLA escalation failed for ticket %s: %s", ticket_id, exc)

            for ticket_data in warning:
                tech_id = ticket_data.get("responsible_technician_id")
                if not tech_id:
                    continue
                try:
                    tech = User.objects.get(id=tech_id)
                    notify(
                        tech,
                        title=f"SLA expira em breve: {ticket_data.get('code', '')} – {ticket_data.get('title', '')[:60]}",
                        event="ticket.sla_warning",
                        category="SLA",
                        message=f"O chamado {ticket_data.get('code')} vence em menos de 1 hora.",
                        link=f"tickets/{ticket_data.get('id')}",
                        company=company,
                        send_email=False,
                    )
                except User.DoesNotExist:
                    pass

        except Exception as exc:
            logger.exception("SLA check failed for company %s: %s", company.id, exc)

    logger.info("SLA task complete: %d breached, %d warning", total_breached, total_warning)


@app.task(name='apps.tickets.tasks.auto_close_stale_tickets')
def auto_close_stale_tickets():
    """Auto-close tickets stuck in Validacao for 7+ days."""
    from datetime import timedelta
    from django.utils import timezone
    from .models import Ticket
    from apps.notifications.services import notify
    from common.audit import record_audit

    cutoff = timezone.now() - timedelta(days=7)
    stale = Ticket.objects.filter(
        deleted_at__isnull=True,
        status="Validacao",
        updated_at__lt=cutoff,
    ).select_related('company', 'requester_user', 'responsible_technician')

    closed = 0
    for ticket in stale:
        try:
            ticket.status = "Finalizado"
            ticket.finished_at = timezone.now()
            ticket.save(update_fields=["status", "finished_at", "updated_at"])
            record_audit(
                action="ticket.auto_closed",
                instance=ticket,
                description=f"Chamado {ticket.code} fechado automaticamente após 7 dias em Validação.",
                origin="system",
            )
            # Notify requester
            if ticket.requester_user:
                notify(
                    ticket.requester_user,
                    title=f"Chamado {ticket.code} finalizado automaticamente",
                    event="ticket.auto_closed",
                    category="Chamados",
                    message=f"O chamado '{ticket.title}' foi finalizado automaticamente após 7 dias sem validação.",
                    link=f"chamados/{ticket.id}",
                    company=ticket.company,
                    send_email=False,
                )
            closed += 1
        except Exception as exc:
            logger.warning("Auto-close failed for ticket %s: %s", ticket.id, exc)

    logger.info("Auto-close task: %d tickets closed", closed)


@app.task(name='apps.tickets.tasks.escalate_ticket_priorities')
def escalate_ticket_priorities():
    """Escalate ticket priority if open too long without response."""
    from datetime import timedelta
    from django.utils import timezone
    from .models import Ticket
    from apps.notifications.services import notify
    from common.audit import record_audit

    now = timezone.now()
    escalation_rules = [
        # (current_priority, hours_without_response, new_priority)
        ("Baixa", 48, "Media"),
        ("Media", 24, "Alta"),
        ("Alta", 8, "Critica"),
    ]
    open_statuses = ["Aberto", "Triagem", "Backlog", "Aguardando atendimento"]
    total = 0

    for current_priority, hours, new_priority in escalation_rules:
        cutoff = now - timedelta(hours=hours)
        tickets = Ticket.objects.filter(
            deleted_at__isnull=True,
            status__in=open_statuses,
            priority=current_priority,
            updated_at__lt=cutoff,
        ).select_related('company', 'responsible_technician')

        for ticket in tickets:
            try:
                ticket.priority = new_priority
                ticket.save(update_fields=["priority", "updated_at"])
                record_audit(
                    action="ticket.priority_escalated",
                    instance=ticket,
                    description=f"Prioridade escalada de {current_priority} para {new_priority} por inatividade.",
                    origin="system",
                )
                if ticket.responsible_technician:
                    notify(
                        ticket.responsible_technician,
                        title=f"Prioridade escalada: {ticket.code}",
                        event="ticket.priority_changed",
                        category="Chamados",
                        message=f"O chamado {ticket.code} teve prioridade escalada para {new_priority}.",
                        link=f"chamados/{ticket.id}",
                        company=ticket.company,
                        send_email=False,
                    )
                total += 1
            except Exception as exc:
                logger.warning("Priority escalation failed for ticket %s: %s", ticket.id, exc)

    logger.info("Priority escalation task: %d tickets escalated", total)
