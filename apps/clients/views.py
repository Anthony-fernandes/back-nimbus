from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from common.access import get_user_organization_ids, normalize_user_role, user_has_any_permission, user_has_permission
from common.viewsets import CompanyScopedModelViewSet
from .models import Client
from .serializers import ClientSerializer


class ClientViewSet(CompanyScopedModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = [
        "company",
        "status",
        "plan",
        "health",
        "organization_type",
        "active",
        "parent",
    ]
    search_fields = ["name", "email", "phone", "sector", "contact_name", "document"]
    ordering_fields = "__all__"

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        role = normalize_user_role(getattr(user, "role", None))

        if role == "CLIENT":
            if not user_has_permission(user, "clients.view"):
                return queryset.none()
            return queryset.filter(id__in=get_user_organization_ids(user))

        if not user_has_permission(user, "clients.view"):
            return queryset.none()

        return queryset

    def perform_create(self, serializer):
        if not user_has_permission(self.request.user, "clients.create"):
            raise PermissionDenied("Seu perfil nao pode criar organizacoes.")
        super().perform_create(serializer)

    def perform_update(self, serializer):
        if not user_has_any_permission(self.request.user, ["clients.edit", "clients.manage"]):
            raise PermissionDenied("Seu perfil nao pode alterar organizacoes.")
        serializer.save()

    def perform_destroy(self, instance):
        if not user_has_permission(self.request.user, "clients.delete"):
            raise PermissionDenied("Seu perfil nao pode excluir organizacoes.")
        instance.delete()
