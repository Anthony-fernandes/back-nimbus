from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from common.access import user_has_any_permission, user_has_permission
from common.viewsets import CompanyScopedModelViewSet
from .models import PermissionBlock, User
from .serializers import PermissionBlockSerializer, UserSerializer


class UserViewSet(CompanyScopedModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["role", "company", "client", "is_active"]
    search_fields = [
        "first_name",
        "last_name",
        "email",
        "username",
        "job_title",
        "specialty",
        "client__name",
    ]
    ordering_fields = "__all__"

    def _ensure_can_view(self):
        if user_has_any_permission(self.request.user, ["users.view", "users.manage", "users.managePermissions"]):
            return

        raise PermissionDenied("Seu perfil nao pode consultar usuarios.")

    def _ensure_can_manage(self):
        if user_has_permission(self.request.user, "users.manage"):
            return

        raise PermissionDenied("Seu perfil nao pode gerenciar usuarios.")

    def _ensure_can_manage_permissions(self):
        if user_has_permission(self.request.user, "users.managePermissions"):
            return

        raise PermissionDenied("Seu perfil nao pode alterar permissoes de usuarios.")

    def _payload_changes_permissions(self):
        return any(
            field in self.request.data
            for field in ["permission_blocks", "granted_permissions", "denied_permissions", "permissions_json"]
        )

    def get_queryset(self):
        self._ensure_can_view()
        return super().get_queryset()

    def perform_create(self, serializer):
        self._ensure_can_manage()
        if self._payload_changes_permissions():
            self._ensure_can_manage_permissions()
        super().perform_create(serializer)

    def perform_update(self, serializer):
        self._ensure_can_manage()
        if self._payload_changes_permissions():
            self._ensure_can_manage_permissions()
        serializer.save()

    def perform_destroy(self, instance):
        self._ensure_can_manage()
        instance.delete()


class PermissionBlockViewSet(CompanyScopedModelViewSet):
    queryset = PermissionBlock.objects.all()
    serializer_class = PermissionBlockSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["active", "company"]
    search_fields = ["name", "description"]
    ordering_fields = "__all__"

    def _ensure_can_view(self):
        if user_has_any_permission(
            self.request.user,
            ["permissionBlocks.view", "permissionBlocks.manage", "users.managePermissions"],
        ):
            return

        raise PermissionDenied("Seu perfil nao pode consultar blocos de permissoes.")

    def _ensure_can_manage(self):
        if user_has_any_permission(
            self.request.user,
            ["permissionBlocks.manage", "users.managePermissions"],
        ):
            return

        raise PermissionDenied("Seu perfil nao pode gerenciar blocos de permissoes.")

    def get_queryset(self):
        self._ensure_can_view()
        return super().get_queryset()

    def perform_create(self, serializer):
        self._ensure_can_manage()
        super().perform_create(serializer)

    def perform_update(self, serializer):
        self._ensure_can_manage()
        serializer.save()

    def perform_destroy(self, instance):
        self._ensure_can_manage()
        instance.delete()
