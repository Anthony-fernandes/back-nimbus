from common.permissions import IsAdminOrManager
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from .models import Company
from .serializers import CompanySerializer

class CompanyViewSet(ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsAdminOrManager]
    filterset_fields = ["is_active"]
    search_fields = ["name","document","email"]
    ordering_fields = "__all__"

    def get_queryset(self):
        company = getattr(self.request.user, "company", None)
        if not company:
            return Company.objects.none()
        return Company.objects.filter(id=company.id)

    @action(detail=False, methods=["get"], url_path="stats")
    def stats(self, request):
        company = request.user.company
        from apps.tickets.models import Ticket
        from apps.users.models import User
        return Response({
            "total_tickets": Ticket.objects.filter(company=company, deleted_at__isnull=True).count(),
            "total_members": User.objects.filter(company=company).count(),
            "open_tickets": Ticket.objects.filter(company=company, deleted_at__isnull=True, status__in=["Aberto", "Em atendimento", "Triagem"]).count(),
        })
