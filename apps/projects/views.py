from django.db.models import Q
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from common.access import (
    get_user_organization_ids,
    normalize_user_role,
    user_has_any_permission,
    user_has_permission,
)
from common.viewsets import CompanyScopedModelViewSet
from .models import Project
from .serializers import ProjectSerializer


class ProjectViewSet(CompanyScopedModelViewSet):
    queryset = (
        Project.objects.all()
        .select_related('owner', 'client', 'contact_principal')
    )
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["company", "client", "status", "owner", "contact_principal"]
    search_fields = ["name", "description", "client__name", "owner__first_name", "owner__last_name"]
    ordering_fields = "__all__"

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        role = normalize_user_role(getattr(user, "role", None))

        if role == "CLIENT":
            if not user_has_permission(user, "projects.view"):
                return queryset.none()
            return queryset.filter(client_id__in=get_user_organization_ids(user)).distinct()

        if role == "TECHNICIAN":
            if user_has_permission(user, "projects.manage"):
                return queryset
            if not user_has_permission(user, "projects.view"):
                return queryset.none()
            return queryset.filter(
                Q(owner=user) | Q(team=user) | Q(member_links__user=user)
            ).distinct()

        if role == "ADMIN":
            return queryset if user_has_permission(user, "projects.view") else queryset.none()

        return queryset.none()

    def perform_create(self, serializer):
        if not user_has_permission(self.request.user, "projects.create"):
            raise PermissionDenied("Seu perfil nao pode criar projetos.")
        super().perform_create(serializer)

    def perform_update(self, serializer):
        if not user_has_any_permission(self.request.user, ["projects.edit", "projects.manage"]):
            raise PermissionDenied("Seu perfil nao pode alterar projetos.")
        serializer.save()

    def perform_destroy(self, instance):
        if not user_has_permission(self.request.user, "projects.delete"):
            raise PermissionDenied("Seu perfil nao pode excluir projetos.")
        instance.delete()
