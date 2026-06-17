from django.db.models import Q
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from common.access import normalize_user_role, user_has_any_permission, user_has_permission
from common.viewsets import CompanyScopedModelViewSet
from .models import Activity, ActivityTag, ActivityTimeEntry
from .serializers import ActivitySerializer, ActivityTagSerializer, ActivityTimeEntrySerializer


class ActivityViewSet(CompanyScopedModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["company", "type", "status", "priority", "assignee", "project", "sprint", "ticket"]
    search_fields = ["title", "description", "project__name", "ticket__code"]
    ordering_fields = "__all__"

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        role = normalize_user_role(getattr(user, "role", None))

        if role == "CLIENT":
            return queryset.none()

        if role == "TECHNICIAN":
            if user_has_permission(user, "activities.manage"):
                return queryset
            if not user_has_permission(user, "activities.view"):
                return queryset.none()
            return queryset.filter(
                Q(assignee=user) | Q(project__owner=user) | Q(project__team=user)
            ).distinct()

        if role == "ADMIN":
            return queryset if user_has_permission(user, "activities.view") else queryset.none()

        return queryset.none()

    def perform_create(self, serializer):
        if not user_has_permission(self.request.user, "activities.create"):
            raise PermissionDenied("Seu perfil nao pode criar atividades.")
        super().perform_create(serializer)

    def perform_update(self, serializer):
        if not user_has_any_permission(self.request.user, ["activities.edit", "activities.manage"]):
            raise PermissionDenied("Seu perfil nao pode alterar atividades.")
        serializer.save()

    def perform_destroy(self, instance):
        if not user_has_permission(self.request.user, "activities.delete"):
            raise PermissionDenied("Seu perfil nao pode excluir atividades.")
        instance.delete()


class ActivityTagViewSet(CompanyScopedModelViewSet):
    queryset = ActivityTag.objects.all()
    serializer_class = ActivityTagSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["active"]
    search_fields = ["name", "description"]
    ordering_fields = "__all__"

    def get_queryset(self):
        if not user_has_any_permission(self.request.user, ["settings.view", "settings.edit"]):
            raise PermissionDenied("Seu perfil nao pode consultar tags de atividades.")
        return super().get_queryset()

    def perform_create(self, serializer):
        if not user_has_permission(self.request.user, "settings.edit"):
            raise PermissionDenied("Seu perfil nao pode criar tags de atividades.")
        super().perform_create(serializer)

    def perform_update(self, serializer):
        if not user_has_permission(self.request.user, "settings.edit"):
            raise PermissionDenied("Seu perfil nao pode alterar tags de atividades.")
        serializer.save()

    def perform_destroy(self, instance):
        if not user_has_permission(self.request.user, "settings.edit"):
            raise PermissionDenied("Seu perfil nao pode excluir tags de atividades.")
        instance.delete()


class ActivityTimeEntryViewSet(CompanyScopedModelViewSet):
    queryset = ActivityTimeEntry.objects.all()
    serializer_class = ActivityTimeEntrySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["activity", "sprint", "project", "collaborator"]
    search_fields = ["collaborator_name", "work_description"]
    ordering_fields = "__all__"

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        role = normalize_user_role(getattr(user, "role", None))

        if role == "CLIENT":
            return queryset.none()

        if role == "TECHNICIAN":
            if user_has_permission(user, "activities.manage"):
                return queryset
            if not user_has_permission(user, "activities.trackTime"):
                return queryset.none()
            return queryset.filter(Q(collaborator=user) | Q(activity__assignee=user)).distinct()

        if role == "ADMIN":
            return queryset if user_has_permission(user, "activities.view") else queryset.none()

        return queryset.none()

    def perform_create(self, serializer):
        if not user_has_permission(self.request.user, "activities.trackTime"):
            raise PermissionDenied("Seu perfil nao pode apontar horas.")
        super().perform_create(serializer)

    def perform_update(self, serializer):
        if not user_has_permission(self.request.user, "activities.trackTime"):
            raise PermissionDenied("Seu perfil nao pode alterar apontamentos.")
        serializer.save()

    def perform_destroy(self, instance):
        if not user_has_permission(self.request.user, "activities.trackTime"):
            raise PermissionDenied("Seu perfil nao pode excluir apontamentos.")
        instance.delete()
