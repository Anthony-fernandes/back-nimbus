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
from .models import Ticket, TicketCategory, TicketWorkflowStatus
from .serializers import TicketSerializer, TicketCategorySerializer, TicketWorkflowStatusSerializer


class TicketViewSet(CompanyScopedModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = [
        "company",
        "client",
        "project",
        "sprint",
        "priority",
        "status",
        "impact",
        "urgency",
        "category",
        "type",
        "requester_user",
        "contact_responsible",
        "responsible_technician",
    ]
    search_fields = [
        "code",
        "title",
        "description",
        "requester",
        "requester_user__first_name",
        "requester_user__last_name",
        "client__name",
    ]
    ordering_fields = "__all__"

    def _is_client_with_org_scope(self):
        role = normalize_user_role(getattr(self.request.user, "role", None))
        return role == "CLIENT" and user_has_permission(self.request.user, "tickets.viewOrganization")

    def _ensure_can_create(self):
        if user_has_permission(self.request.user, "tickets.create"):
            return
        raise PermissionDenied("Seu perfil nao pode criar chamados.")

    def _ensure_can_update(self, ticket):
        role = normalize_user_role(getattr(self.request.user, "role", None))
        status_to = str(self.request.data.get("status") or "").strip()

        if role == "CLIENT":
            can_validate = user_has_any_permission(
                self.request.user,
                ["tickets.validateOwn", "tickets.validateOrganization"],
            )
            can_edit_own = user_has_permission(self.request.user, "tickets.editOwnBeforeStart")
            public_editable_statuses = {"Aberto", "Triagem", "Aguardando atendimento"}
            public_editable_fields = {
                "title",
                "description",
                "requester",
                "contact_responsible_name",
                "contact_responsible_phone",
            }

            if (
                can_edit_own
                and ticket.requester_user_id == self.request.user.id
                and ticket.status in public_editable_statuses
                and set(self.request.data.keys()).issubset(public_editable_fields)
            ):
                return

            if (
                can_validate
                and ticket.status == "Validacao"
                and status_to in {"Finalizado", "Em atendimento"}
            ):
                return

            raise PermissionDenied("Seu perfil nao pode alterar esse chamado.")

        if user_has_any_permission(
            self.request.user,
            [
                "tickets.edit",
                "tickets.assign",
                "tickets.categorize",
                "tickets.approve",
                "tickets.finish",
                "tickets.manageChecklist",
                "tickets.manageTags",
                "tickets.manageSla",
                "tickets.manageEffort",
            ],
        ):
            return

        raise PermissionDenied("Seu perfil nao pode alterar chamados.")

    def _ensure_can_delete(self):
        if user_has_permission(self.request.user, "tickets.delete"):
            return
        raise PermissionDenied("Seu perfil nao pode excluir chamados.")

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        role = normalize_user_role(getattr(user, "role", None))

        if role == "CLIENT":
            filters = Q()
            if user_has_permission(user, "tickets.viewOwn"):
                filters |= Q(requester_user=user)
            if user_has_permission(user, "tickets.viewOrganization"):
                filters |= Q(client_id__in=get_user_organization_ids(user))
            return queryset.filter(filters).distinct() if filters else queryset.none()

        if role == "TECHNICIAN":
            if user_has_permission(user, "tickets.viewAll"):
                return queryset

            filters = Q()
            if user_has_permission(user, "tickets.viewAssigned"):
                filters |= Q(responsible_technician=user) | Q(technicians=user)
            if user_has_permission(user, "tickets.viewTeam") and getattr(user, "technical_group", ""):
                filters |= Q(team__iexact=user.technical_group)
            if user_has_permission(user, "tickets.viewOwn"):
                filters |= Q(requester_user=user)

            return queryset.filter(filters).distinct() if filters else queryset.none()

        if role == "ADMIN":
            return queryset if user_has_permission(user, "tickets.viewAll") else queryset.none()

        return queryset.none()

    def perform_create(self, serializer):
        self._ensure_can_create()
        role = normalize_user_role(getattr(self.request.user, "role", None))

        if role == "CLIENT":
            organization = serializer.validated_data.get("client")
            if not organization or str(organization.id) not in get_user_organization_ids(self.request.user):
                raise PermissionDenied(
                    "Usuarios do portal do cliente so podem abrir chamados na propria organizacao."
                )

            serializer.save(
                company=self.request.user.company,
                requester_user=self.request.user,
                requester=self.request.user.full_name_or_username,
                contact_responsible_name=serializer.validated_data.get("contact_responsible_name")
                or self.request.user.full_name_or_username,
                contact_responsible_phone=serializer.validated_data.get("contact_responsible_phone")
                or getattr(self.request.user, "phone", ""),
            )
            return

        super().perform_create(serializer)

    def perform_update(self, serializer):
        self._ensure_can_update(self.get_object())
        serializer.save()

    def perform_destroy(self, instance):
        self._ensure_can_delete()
        instance.delete()


class TicketCategoryViewSet(CompanyScopedModelViewSet):
    queryset = TicketCategory.objects.all()
    serializer_class = TicketCategorySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["active", "approval_required", "allow_project_activity"]
    search_fields = ["name", "description", "default_team", "default_type"]
    ordering_fields = "__all__"

    def _ensure_can_view(self):
        if user_has_any_permission(self.request.user, ["categories.view", "categories.manage", "settings.view"]):
            return
        raise PermissionDenied("Seu perfil nao pode consultar categorias.")

    def _ensure_can_manage(self):
        if user_has_any_permission(self.request.user, ["categories.manage", "settings.edit"]):
            return
        raise PermissionDenied("Seu perfil nao pode alterar categorias.")

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


class TicketWorkflowStatusViewSet(CompanyScopedModelViewSet):
    queryset = TicketWorkflowStatus.objects.all()
    serializer_class = TicketWorkflowStatusSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["active", "pauses_sla", "is_final", "allows_resume", "system"]
    search_fields = ["name", "slug", "description"]
    ordering_fields = "__all__"

    def _ensure_can_view(self):
        if user_has_any_permission(self.request.user, ["settings.view", "categories.view", "categories.manage"]):
            return
        raise PermissionDenied("Seu perfil nao pode consultar o workflow dos chamados.")

    def _ensure_can_manage(self):
        if user_has_any_permission(self.request.user, ["settings.edit", "categories.manage"]):
            return
        raise PermissionDenied("Seu perfil nao pode alterar o workflow dos chamados.")

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
