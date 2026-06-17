from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.activities.models import Activity
from apps.clients.models import Client
from apps.projects.models import Project
from apps.tickets.models import Ticket
from common.viewsets import CompanyScopedModelViewSet

from .models import Dashboard, DashboardVersion
from .serializers import DashboardSerializer, DashboardVersionSerializer


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
            "tickets_critical": tickets.filter(priority="Crítica").count(),
            "clients": clients.count(),
            "projects_active": projects.exclude(status="Concluído").count(),
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


class DashboardViewSet(CompanyScopedModelViewSet):
    serializer_class = DashboardSerializer
    queryset = Dashboard.objects.all()

    def get_queryset(self):
        company = getattr(self.request.user, "company", None)
        if not company:
            return Dashboard.objects.none()
        return Dashboard.objects.filter(company=company, deleted_at__isnull=True)

    def perform_create(self, serializer):
        company = getattr(self.request.user, "company", None)
        serializer.save(company=company)

    @action(detail=False, methods=["get"], url_path="active")
    def active(self, request):
        company = getattr(request.user, "company", None)
        if not company:
            return Response(None)
        dashboard = Dashboard.objects.filter(company=company, is_active=True, deleted_at__isnull=True).first()
        if not dashboard:
            return Response(None)
        serializer = self.get_serializer(dashboard)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="duplicate")
    def duplicate(self, request, pk=None):
        original = self.get_object()
        clone = Dashboard.objects.create(
            company=original.company,
            name=f"{original.name} (copia)",
            description=original.description,
            type=original.type,
            status="draft",
            is_active=False,
            components_json=original.components_json,
            filters_json=original.filters_json,
            created_by=original.created_by,
        )
        serializer = self.get_serializer(clone)
        return Response(serializer.data, status=201)

    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request, pk=None):
        dashboard = self.get_object()
        # Deactivate all other dashboards for this company
        Dashboard.objects.filter(company=dashboard.company, is_active=True).exclude(pk=dashboard.pk).update(is_active=False)
        dashboard.status = "active"
        dashboard.is_active = True
        dashboard.save()
        # Create a version snapshot
        last_version = DashboardVersion.objects.filter(dashboard=dashboard).order_by("-version_number").first()
        next_version = (last_version.version_number + 1) if last_version else 1
        DashboardVersion.objects.create(
            dashboard=dashboard,
            version_number=next_version,
            config_snapshot={
                "name": dashboard.name,
                "description": dashboard.description,
                "type": dashboard.type,
                "status": dashboard.status,
                "components_json": dashboard.components_json,
                "filters_json": dashboard.filters_json,
            },
            created_by=dashboard.created_by,
            is_published=True,
        )
        serializer = self.get_serializer(dashboard)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="set-active")
    def set_active(self, request, pk=None):
        dashboard = self.get_object()
        Dashboard.objects.filter(company=dashboard.company, is_active=True).exclude(pk=dashboard.pk).update(is_active=False)
        dashboard.status = "active"
        dashboard.is_active = True
        dashboard.save()
        serializer = self.get_serializer(dashboard)
        return Response(serializer.data)


class DashboardDataQueryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({})
