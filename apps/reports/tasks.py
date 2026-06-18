import logging
from config.celery import app
logger = logging.getLogger(__name__)


@app.task(name='apps.reports.tasks.send_weekly_ticket_report')
def send_weekly_ticket_report():
    """Send weekly ticket summary report to company admins."""
    from datetime import timedelta
    from django.utils import timezone
    from django.db.models import Count
    from apps.companies.models import Company
    from apps.tickets.models import Ticket
    from apps.notifications.services import _send_email

    now = timezone.now()
    week_ago = now - timedelta(days=7)

    companies = Company.objects.filter(deleted_at__isnull=True)

    for company in companies:
        try:
            qs = Ticket.objects.filter(
                company=company,
                created_at__gte=week_ago,
                deleted_at__isnull=True,
            )
            total = qs.count()
            if total == 0:
                continue

            closed = qs.filter(status__in=["Finalizado", "Cancelado"]).count()
            open_count = total - closed
            by_priority = list(qs.values("priority").annotate(c=Count("id")).order_by("-c"))

            lines = [
                f"Relatório semanal de chamados — {company.name}",
                f"Período: {week_ago.strftime('%d/%m/%Y')} a {now.strftime('%d/%m/%Y')}",
                "",
                f"Total abertos na semana: {total}",
                f"Finalizados: {closed}",
                f"Em aberto: {open_count}",
                "",
                "Por prioridade:",
            ]
            for row in by_priority:
                lines.append(f"  {row['priority'] or 'Sem prioridade'}: {row['c']}")

            # Send to all admin users of this company
            from apps.users.models import User
            admins = User.objects.filter(company=company, role__in=["ADMIN", "admin"], deleted_at__isnull=True, email__isnull=False).exclude(email="")
            for admin in admins:
                try:
                    _send_email(
                        admin,
                        title=f"Relatório semanal — {company.name}",
                        message="\n".join(lines),
                        link="reports?type=tickets",
                        event="report.weekly_tickets",
                    )
                except Exception as exc:
                    logger.warning("Weekly report email failed for user %s: %s", admin.id, exc)

        except Exception as exc:
            logger.exception("Weekly report task failed for company %s: %s", company.id, exc)

    logger.info("Weekly ticket report task complete for %d companies", companies.count())
