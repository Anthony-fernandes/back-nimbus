class TicketService:

    @staticmethod
    def change_status(ticket, status):
        ticket.status = status
        ticket.save()
