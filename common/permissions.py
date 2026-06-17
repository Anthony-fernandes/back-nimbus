from rest_framework.permissions import BasePermission, SAFE_METHODS

from .access import normalize_user_role, user_has_permission


def is_admin_user(user):
    return bool(user and user.is_authenticated and normalize_user_role(getattr(user, "role", None)) == "ADMIN")


def is_internal_user(user):
    return bool(
        user
        and user.is_authenticated
        and normalize_user_role(getattr(user, "role", None)) in {"ADMIN", "TECHNICIAN"}
    )


class HasConfiguredPermission(BasePermission):
    read_permission = None
    write_permission = None

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        required_permission = self.read_permission if request.method in SAFE_METHODS else self.write_permission
        if not required_permission:
            return True

        return user_has_permission(request.user, required_permission)


class IsAdminOnly(BasePermission):
    def has_permission(self, request, view):
        return is_admin_user(request.user)


class IsInternalPortalUser(BasePermission):
    def has_permission(self, request, view):
        return is_internal_user(request.user)


class IsAdminOrManager(BasePermission):
    def has_permission(self, request, view):
        return is_admin_user(request.user)


class IsAdminOrManagerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)

        return is_admin_user(request.user)
