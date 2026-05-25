from common.permissions import IsAdminOrManagerOrReadOnly
from common.viewsets import CompanyScopedModelViewSet
from .models import Ticket, TicketCategory, TicketWorkflowStatus
from .serializers import TicketSerializer, TicketCategorySerializer, TicketWorkflowStatusSerializer

class TicketViewSet(CompanyScopedModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    filterset_fields = ["company","client","project","priority","status","impact","urgency","category","type"]
    search_fields = ["code","title","description","requester","client__name"]
    ordering_fields = "__all__"


class TicketCategoryViewSet(CompanyScopedModelViewSet):
    queryset = TicketCategory.objects.all()
    serializer_class = TicketCategorySerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]
    filterset_fields = ["active", "approval_required", "allow_project_activity"]
    search_fields = ["name", "description", "default_team", "default_type"]
    ordering_fields = "__all__"


class TicketWorkflowStatusViewSet(CompanyScopedModelViewSet):
    queryset = TicketWorkflowStatus.objects.all()
    serializer_class = TicketWorkflowStatusSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]
    filterset_fields = ["active", "pauses_sla", "is_final", "allows_resume", "system"]
    search_fields = ["name", "slug", "description"]
    ordering_fields = "__all__"
