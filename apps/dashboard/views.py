from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.activities.models import Activity
from apps.clients.models import Client
from apps.projects.models import Project
from apps.tickets.models import Ticket


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = getattr(request.user, "company", None)

        if not company:
            return Response({
                "tickets_open": 0,
                "tickets_critical": 0,
                "clients": 0,
                "projects_active": 0,
                "activities": 0,
                "recent_tickets": [],
                "projects_at_risk": [],
            })

        tickets = Ticket.objects.filter(company=company)
        projects = Project.objects.filter(company=company)
        clients = Client.objects.filter(company=company)
        activities = Activity.objects.filter(company=company)

        return Response({
            "tickets_open": tickets.exclude(status="Finalizado").count(),
            "tickets_critical": tickets.filter(priority="CrÃ­tica").count(),
            "clients": clients.count(),
            "projects_active": projects.exclude(status="ConcluÃ­do").count(),
            "activities": activities.count(),
            "recent_tickets": list(
                tickets.order_by("-created_at")[:8].values(
                    "id",
                    "code",
                    "title",
                    "priority",
                    "status",
                    "sla",
                )
            ),
            "projects_at_risk": list(
                projects.filter(status="Em risco")[:5].values("id", "name", "progress", "due_at")
            ),
        })
