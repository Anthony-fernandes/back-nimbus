"""
Signals do módulo de tickets:
- TicketStatusHistory: registra toda transição de status
- CSAT: envia notificação ao solicitante quando ticket é Finalizado
- Reopen deadline: define prazo de reabertura ao finalizar
"""
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone


@receiver(pre_save, sender="tickets.Ticket")
def track_status_change(sender, instance, **kwargs):
    """Cria TicketStatusHistory sempre que o status mudar."""
    if not instance.pk:
        return
    try:
        old = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    if old.status != instance.status:
        from apps.tickets.models import TicketStatusHistory
        TicketStatusHistory.objects.create(
            company_id=instance.company_id,
            ticket=instance,
            changed_by=getattr(instance, "_changed_by", None),
            changed_by_name=getattr(instance, "_changed_by_name", ""),
            status_from=old.status,
            status_to=instance.status,
            reason=getattr(instance, "_status_change_reason", ""),
        )

        # CSAT: enviar notificação ao finalizar
        if instance.status == "Finalizado" and old.status != "Finalizado":
            _send_csat_notification(instance)
            instance.csat_sent_at = timezone.now()
            # Set reopen deadline: 5 dias após finalização
            instance.reopen_deadline = timezone.now() + timezone.timedelta(days=5)
            instance.finished_at = timezone.now()


def _send_csat_notification(ticket):
    """Cria notificação inbox pedindo avaliação do chamado."""
    try:
        from apps.notifications.models import Notification
        recipient = ticket.requester_user or ticket.contact_responsible
        if not recipient:
            return
        Notification.objects.create(
            company_id=ticket.company_id,
            recipient=recipient,
            category="Chamados",
            event="ticket.csat_request",
            title=f"Como foi o atendimento? Avalie o chamado {ticket.code}",
            message=f"O chamado '{ticket.title}' foi finalizado. Por favor, avalie o atendimento de 1 a 5.",
            link=f"/tickets/{ticket.id}?rate=1",
            entity_type="ticket",
            entity_id=str(ticket.id),
        )
    except Exception:
        pass


def connect_signals():
    pass  # signals are auto-connected via decorator
