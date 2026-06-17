"""Management command to check SLA breaches and send notifications."""
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Check SLA deadlines and notify technicians of breaches and warnings."

    def handle(self, *args, **options):
        from apps.companies.models import Company
        from apps.notifications.services import notify
        from apps.tickets.models import Ticket

        now = timezone.now()
        open_statuses = [
            "Aberto", "Triagem", "Backlog", "Aguardando atendimento",
            "Em atendimento", "Aguardando cliente", "Validacao",
        ]

        companies = Company.objects.filter(deleted_at__isnull=True)
        total_notified = 0

        for company in companies:
            tickets = Ticket.objects.filter(
                company=company,
                deleted_at__isnull=True,
                sla_due_at__isnull=False,
                status__in=open_statuses,
            )

            # Breached (overdue)
            breached = tickets.filter(sla_due_at__lt=now)
            for ticket in breached:
                if ticket.responsible_technician:
                    notify(
                        ticket.responsible_technician,
                        title=f"SLA violado: {ticket.code}",
                        message=f"O prazo do chamado '{ticket.title}' foi ultrapassado.",
                        event="ticket.sla_breached",
                        company=company,
                        link=f"chamados/{ticket.id}",
                        entity=ticket,
                        origin="tickets",
                    )
                    total_notified += 1

            # Warning: within next hour
            from datetime import timedelta
            warning_threshold = now + timedelta(hours=1)
            warning = tickets.filter(sla_due_at__gte=now, sla_due_at__lte=warning_threshold)
            for ticket in warning:
                if ticket.responsible_technician:
                    remaining = ticket.sla_due_at - now
                    minutes = int(remaining.total_seconds() / 60)
                    notify(
                        ticket.responsible_technician,
                        title=f"SLA próximo: {ticket.code}",
                        message=f"O prazo do chamado '{ticket.title}' vence em {minutes} minutos.",
                        event="ticket.sla_warning",
                        company=company,
                        link=f"chamados/{ticket.id}",
                        entity=ticket,
                        origin="tickets",
                    )
                    total_notified += 1

        self.stdout.write(self.style.SUCCESS(f"SLA check concluído. {total_notified} notificações enviadas."))
