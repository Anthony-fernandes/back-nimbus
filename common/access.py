from __future__ import annotations

from copy import deepcopy
from typing import Any


PermissionMap = dict[str, Any]


DEFAULT_ROLE_PERMISSIONS: dict[str, PermissionMap] = {
    "ADMIN": {
        "tickets": {
            "viewAll": True,
            "viewOwn": True,
            "create": True,
            "edit": True,
            "assign": True,
            "categorize": True,
            "approve": True,
            "finish": True,
            "delete": True,
            "commentInternal": True,
            "commentPublic": True,
            "manageChecklist": True,
            "manageTags": True,
            "manageSla": True,
            "manageEffort": True,
        },
        "activities": {
            "view": True,
            "create": True,
            "edit": True,
            "manage": True,
            "delete": True,
            "trackTime": True,
        },
        "projects": {"view": True, "create": True, "edit": True, "manage": True, "delete": True},
        "sprints": {"view": True, "create": True, "edit": True, "manage": True, "delete": True},
        "clients": {"view": True, "create": True, "edit": True, "manage": True, "delete": True},
        "users": {
            "view": True,
            "create": True,
            "edit": True,
            "manage": True,
            "delete": True,
            "managePermissions": True,
        },
        "reports": {"view": True, "export": True},
        "settings": {"view": True, "edit": True},
        "categories": {"view": True, "create": True, "edit": True, "manage": True, "delete": True},
        "permissionBlocks": {
            "view": True,
            "create": True,
            "edit": True,
            "manage": True,
            "delete": True,
        },
    },
    "TECHNICIAN": {
        "tickets": {
            "viewAssigned": True,
            "viewTeam": True,
            "viewOwn": True,
            "create": True,
            "edit": True,
            "categorize": True,
            "finish": True,
            "commentInternal": True,
            "commentPublic": True,
            "manageChecklist": True,
            "manageEffort": True,
        },
        "activities": {"view": True, "create": True, "edit": True, "trackTime": True},
        "projects": {"view": True},
        "sprints": {"view": True},
        "clients": {"view": True},
        "categories": {"view": True},
    },
    "CLIENT": {
        "tickets": {
            "viewOwn": True,
            "create": True,
            "editOwnBeforeStart": True,
            "commentOwn": True,
            "validateOwn": True,
            "rateOwn": True,
            "attachFiles": True,
        }
    },
}


INITIAL_PERMISSION_BLOCKS: list[dict[str, Any]] = [
    {
        "name": "Dev",
        "description": "Fluxo tecnico para desenvolvimento e manutencao.",
        "permissions": {
            "tickets": {
                "viewAssigned": True,
                "edit": True,
                "commentInternal": True,
                "manageChecklist": True,
                "manageEffort": True,
            },
            "activities": {"view": True, "edit": True, "trackTime": True},
            "projects": {"view": True},
            "sprints": {"view": True, "manage": True},
        },
    },
    {
        "name": "Suporte N1",
        "description": "Atendimento inicial e atualizacao operacional.",
        "permissions": {
            "tickets": {
                "viewAssigned": True,
                "create": True,
                "commentPublic": True,
                "commentInternal": True,
                "manageChecklist": True,
            }
        },
    },
    {
        "name": "Suporte N2",
        "description": "Atendimento tecnico com categorizacao e encerramento.",
        "permissions": {
            "tickets": {
                "viewAssigned": True,
                "viewTeam": True,
                "create": True,
                "edit": True,
                "categorize": True,
                "finish": True,
                "manageChecklist": True,
                "manageEffort": True,
            }
        },
    },
    {
        "name": "Gestor Cliente",
        "description": "Acompanha, valida e aprova chamados da propria organizacao.",
        "permissions": {
            "tickets": {
                "viewOrganization": True,
                "validateOrganization": True,
                "approve": True,
                "rateOwn": True,
            }
        },
    },
    {
        "name": "Administrador de permissoes",
        "description": "Gerencia usuarios, permissoes e blocos.",
        "permissions": {
            "users": {"view": True, "edit": True, "manage": True, "managePermissions": True},
            "permissionBlocks": {"view": True, "create": True, "edit": True, "manage": True},
        },
    },
]


def _slugify_role(value: Any) -> str:
    return (
        str(value or "")
        .strip()
        .upper()
        .replace("-", "_")
        .replace(" ", "_")
    )


def normalize_user_role(role: Any) -> str | None:
    normalized = _slugify_role(role)

    if normalized in {"ADMIN", "ADMINISTRADOR", "ADMINISTRATOR", "SUPERUSER", "SUPER_USER"}:
        return "ADMIN"

    if normalized in {
        "TECHNICIAN",
        "TECH",
        "TECNICO",
        "SUPORTE",
        "SUPPORT",
        "MANAGER",
        "GESTOR",
        "PROJECT_LEAD",
        "LIDER_PROJETO",
        "LIDER_DE_PROJETO",
        "COLLABORATOR",
        "COLABORADOR",
    }:
        return "TECHNICIAN"

    if normalized in {
        "CLIENT",
        "CLIENTE",
        "CUSTOMER",
        "REQUESTER",
        "SOLICITANTE",
        "OBSERVER",
        "OBSERVADOR",
        "APPROVER",
        "APROVADOR",
    }:
        return "CLIENT"

    return normalized or None


def normalize_permission_map(value: Any) -> PermissionMap:
    if not isinstance(value, dict):
        return {}

    normalized: PermissionMap = {}
    for key, entry in value.items():
        if isinstance(entry, bool):
            normalized[str(key)] = entry
        elif isinstance(entry, dict):
            normalized[str(key)] = normalize_permission_map(entry)

    return normalized


def merge_permission_maps(*maps: Any) -> PermissionMap:
    result: PermissionMap = {}

    for raw_map in maps:
        current = normalize_permission_map(raw_map)
        result = _merge_two_permission_maps(result, current)

    return result


def _merge_two_permission_maps(base: PermissionMap, extra: PermissionMap) -> PermissionMap:
    result = deepcopy(base)

    for key, value in extra.items():
        if isinstance(value, bool):
            result[key] = value
            continue

        current = result.get(key, {})
        if not isinstance(current, dict):
            current = {}

        result[key] = _merge_two_permission_maps(current, value)

    return result


def apply_denied_permissions(base_permissions: Any, denied_permissions: Any) -> PermissionMap:
    result = normalize_permission_map(base_permissions)

    for key, value in normalize_permission_map(denied_permissions).items():
        if isinstance(value, bool):
            if value:
                result[key] = False
            continue

        current = result.get(key, {})
        if not isinstance(current, dict):
            current = {}

        result[key] = apply_denied_permissions(current, value)

    return result


def permission_map_from_keys(permission_keys: list[str] | tuple[str, ...] | None) -> PermissionMap:
    result: PermissionMap = {}

    for permission_key in permission_keys or []:
        set_permission_value(result, permission_key, True)

    return result


def set_permission_value(permission_map: PermissionMap, path: str, value: bool) -> PermissionMap:
    current = permission_map
    segments = [segment for segment in str(path).split(".") if segment]

    for index, segment in enumerate(segments):
        if index == len(segments) - 1:
            current[segment] = value
            break

        nested = current.get(segment)
        if not isinstance(nested, dict):
            nested = {}
            current[segment] = nested

        current = nested

    return permission_map


def flatten_granted_permissions(permission_map: Any, prefix: str = "") -> list[str]:
    result: list[str] = []

    for key, value in normalize_permission_map(permission_map).items():
        current_path = f"{prefix}.{key}" if prefix else key

        if isinstance(value, bool):
            if value:
                result.append(current_path)
            continue

        result.extend(flatten_granted_permissions(value, current_path))

    return result


def permission_enabled(permission_map: Any, path: str) -> bool:
    current: Any = normalize_permission_map(permission_map)

    for segment in str(path).split("."):
        if not isinstance(current, dict):
            return False
        current = current.get(segment)

    return current is True


def get_user_organization_ids(user: Any) -> list[str]:
    organization_ids: set[str] = set()
    primary_id = getattr(user, "client_id", None)

    if primary_id:
        organization_ids.add(str(primary_id))

    links = getattr(user, "organization_links", None)
    if links is None:
        return list(organization_ids)

    iterable = links.all() if hasattr(links, "all") else links
    for link in iterable or []:
        organization_id = getattr(link, "organization_id", None)
        if organization_id:
            organization_ids.add(str(organization_id))

    return list(organization_ids)


def get_user_permission_blocks(user: Any) -> list[Any]:
    blocks = getattr(user, "permission_blocks", None)
    if blocks is None:
        return []

    if hasattr(blocks, "filter"):
        return list(blocks.filter(active=True))

    return [block for block in blocks if getattr(block, "active", True)]


def resolve_user_permissions(user: Any) -> PermissionMap:
    role = normalize_user_role(getattr(user, "role", None))
    base_permissions = deepcopy(DEFAULT_ROLE_PERMISSIONS.get(role or "", {}))
    block_permissions = merge_permission_maps(
        *[getattr(block, "permissions", {}) for block in get_user_permission_blocks(user)]
    )
    granted_permissions = normalize_permission_map(getattr(user, "granted_permissions", {}))

    if not granted_permissions:
        granted_permissions = permission_map_from_keys(getattr(user, "permissions_json", []) or [])

    denied_permissions = normalize_permission_map(getattr(user, "denied_permissions", {}))

    return apply_denied_permissions(
        merge_permission_maps(base_permissions, block_permissions, granted_permissions),
        denied_permissions,
    )


def user_has_permission(user: Any, path: str) -> bool:
    return permission_enabled(resolve_user_permissions(user), path)


def user_has_any_permission(user: Any, paths: list[str] | tuple[str, ...]) -> bool:
    return any(user_has_permission(user, path) for path in paths)
