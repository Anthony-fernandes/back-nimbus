class TicketService:

    @staticmethod
    def change_status(ticket, status):
        ticket.status = status
        ticket.save()


def auto_assign_ticket(ticket):
    """Assign ticket to the technician with fewest open tickets in the same company."""
    from apps.users.models import User
    from django.db.models import Count, Q

    if ticket.responsible_technician_id:
        return  # already assigned

    techs = User.objects.filter(
        company=ticket.company,
        role__in=["TECHNICIAN", "ADMIN"],
        is_active=True,
        deleted_at__isnull=True,
    ).annotate(
        open_count=Count(
            "owned_tickets",
            filter=Q(owned_tickets__status__in=["Aberto", "Em andamento", "Triagem"], owned_tickets__deleted_at__isnull=True)
        )
    ).order_by("open_count", "?")

    if techs.exists():
        ticket.responsible_technician = techs.first()
        ticket.save(update_fields=["responsible_technician", "updated_at"])
