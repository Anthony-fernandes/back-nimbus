from django.db.models import Q
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from common.access import get_user_organization_ids, normalize_user_role, user_has_any_permission, user_has_permission
from common.viewsets import CompanyScopedModelViewSet
from .models import Sprint, SprintActivityPlan
from .serializers import SprintSerializer, SprintActivityPlanSerializer


class SprintViewSet(CompanyScopedModelViewSet):
    queryset = Sprint.objects.all()
    serializer_class = SprintSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["company", "project", "status", "lead"]
    search_fields = ["name", "goal", "project__name"]
    ordering_fields = "__all__"

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        role = normalize_user_role(getattr(user, "role", None))

        if role == "CLIENT":
            if not user_has_permission(user, "sprints.view"):
                return queryset.none()
            return queryset.filter(project__client_id__in=get_user_organization_ids(user)).distinct()

        if role == "TECHNICIAN":
            if user_has_permission(user, "sprints.manage"):
                return queryset
            if not user_has_permission(user, "sprints.view"):
                return queryset.none()
            return queryset.filter(
                Q(lead=user) | Q(project__owner=user) | Q(project__team=user)
            ).distinct()

        if role == "ADMIN":
            return queryset if user_has_permission(user, "sprints.view") else queryset.none()

        return queryset.none()

    def perform_create(self, serializer):
        if not user_has_permission(self.request.user, "sprints.create"):
            raise PermissionDenied("Seu perfil nao pode criar sprints.")
        super().perform_create(serializer)

    def perform_update(self, serializer):
        if not user_has_any_permission(self.request.user, ["sprints.edit", "sprints.manage"]):
            raise PermissionDenied("Seu perfil nao pode alterar sprints.")
        serializer.save()

    def perform_destroy(self, instance):
        if not user_has_permission(self.request.user, "sprints.delete"):
            raise PermissionDenied("Seu perfil nao pode excluir sprints.")
        instance.delete()


class SprintActivityPlanViewSet(CompanyScopedModelViewSet):
    queryset = SprintActivityPlan.objects.all()
    serializer_class = SprintActivityPlanSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["sprint", "activity", "project"]
    search_fields = ["notes"]
    ordering_fields = "__all__"

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        role = normalize_user_role(getattr(user, "role", None))

        if role == "CLIENT":
            if not user_has_permission(user, "sprints.view"):
                return queryset.none()
            return queryset.filter(project__client_id__in=get_user_organization_ids(user)).distinct()

        if role == "TECHNICIAN":
            if user_has_permission(user, "sprints.manage"):
                return queryset
            if not user_has_permission(user, "sprints.view"):
                return queryset.none()
            return queryset.filter(
                Q(sprint__lead=user) | Q(project__owner=user) | Q(project__team=user)
            ).distinct()

        if role == "ADMIN":
            return queryset if user_has_permission(user, "sprints.view") else queryset.none()

        return queryset.none()

    def perform_create(self, serializer):
        if not user_has_any_permission(self.request.user, ["sprints.edit", "sprints.manage"]):
            raise PermissionDenied("Seu perfil nao pode planejar atividades em sprints.")
        super().perform_create(serializer)

    def perform_update(self, serializer):
        if not user_has_any_permission(self.request.user, ["sprints.edit", "sprints.manage"]):
            raise PermissionDenied("Seu perfil nao pode alterar planejamentos de sprint.")
        serializer.save()

    def perform_destroy(self, instance):
        if not user_has_permission(self.request.user, "sprints.delete"):
            raise PermissionDenied("Seu perfil nao pode excluir planejamentos de sprint.")
        instance.delete()
