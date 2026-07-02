from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from common.access import user_has_any_permission
from common.viewsets import CompanyScopedModelViewSet

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(CompanyScopedModelViewSet):
    """Consulta somente-leitura da trilha de auditoria da empresa."""

    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "head", "options"]
    filterset_fields = ["action", "entity_type", "entity_id", "actor", "origin", "company"]
    search_fields = ["action", "entity_label", "description", "actor_name"]
    ordering_fields = "__all__"

    def get_queryset(self):
        if not user_has_any_permission(
            self.request.user,
            ["reports.view", "settings.view", "users.manage"],
        ):
            raise PermissionDenied("Seu perfil nao pode consultar a auditoria.")
        qs = super().get_queryset()
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        return qs
