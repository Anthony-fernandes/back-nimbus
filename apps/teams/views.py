from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from common.access import normalize_user_role, user_has_any_permission
from common.viewsets import CompanyScopedModelViewSet
from .models import Team, TeamMember
from .serializers import TeamSerializer, TeamMemberSerializer

_MANAGE_PERMS = ["users.manage", "users.managePermissions", "teams.manage"]


def _ensure_can_manage_teams(user):
    if normalize_user_role(getattr(user, "role", None)) == "CLIENT":
        raise PermissionDenied("Clientes não podem gerenciar equipes.")
    if not user_has_any_permission(user, _MANAGE_PERMS):
        raise PermissionDenied("Seu perfil não pode gerenciar equipes.")


class TeamViewSet(CompanyScopedModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["company", "status", "leader"]
    search_fields = ["name", "description"]
    ordering_fields = "__all__"

    def get_queryset(self):
        qs = super().get_queryset()
        # Clientes não têm acesso a equipes internas.
        if normalize_user_role(getattr(self.request.user, "role", None)) == "CLIENT":
            return qs.none()
        return qs

    def perform_create(self, serializer):
        _ensure_can_manage_teams(self.request.user)
        super().perform_create(serializer)

    def perform_update(self, serializer):
        _ensure_can_manage_teams(self.request.user)
        serializer.save()

    def perform_destroy(self, instance):
        _ensure_can_manage_teams(self.request.user)
        instance.delete()


class TeamMemberViewSet(CompanyScopedModelViewSet):
    queryset = TeamMember.objects.all()
    serializer_class = TeamMemberSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["company", "team", "user"]
    search_fields = ["role"]
    ordering_fields = "__all__"

    def get_queryset(self):
        qs = super().get_queryset()
        if normalize_user_role(getattr(self.request.user, "role", None)) == "CLIENT":
            return qs.none()
        return qs

    def perform_update(self, serializer):
        _ensure_can_manage_teams(self.request.user)
        serializer.save()

    def perform_destroy(self, instance):
        _ensure_can_manage_teams(self.request.user)
        instance.delete()

    def perform_create(self, serializer):
        _ensure_can_manage_teams(self.request.user)
        team = serializer.validated_data.get("team")
        company = getattr(self.request.user, "company", None)
        kwargs = {}
        if company:
            kwargs["company"] = company
        if not kwargs.get("company") and team:
            kwargs["company"] = team.company
        serializer.save(**kwargs)
