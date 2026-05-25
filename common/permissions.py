from rest_framework.permissions import BasePermission, SAFE_METHODS


def is_admin_or_manager(user):
    return bool(
        user
        and user.is_authenticated
        and getattr(user, "role", "") in {"ADMIN", "MANAGER"}
    )


class IsAdminOrManager(BasePermission):
    def has_permission(self, request, view):
        return is_admin_or_manager(request.user)


class IsAdminOrManagerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)

        return is_admin_or_manager(request.user)
