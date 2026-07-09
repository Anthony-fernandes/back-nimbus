import datetime

from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.access import (
    get_user_organization_ids,
    normalize_user_role,
    user_has_any_permission,
    user_has_permission,
)
from common.viewsets import CompanyScopedModelViewSet
from .models import Project, ProjectCustomField, ProjectCustomValue
from .serializers import ProjectSerializer, ProjectCustomFieldSerializer, ProjectCustomValueSerializer


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
        # Bloqueia concluir projeto sem base de cálculo ou com itens pendentes.
        new_status = self.request.data.get("status")
        if new_status in ("Concluido", "Concluído"):
            from rest_framework.exceptions import ValidationError
            from common.project_metrics import compute_project_metrics
            m = compute_project_metrics(serializer.instance)
            if not m["has_calculation_basis"]:
                raise ValidationError({"detail": "Não é possível concluir este projeto porque ele "
                                       "não possui atividades ou etapas cadastradas para validar a conclusão."})
            if not m["can_complete"]:
                raise ValidationError({"detail": "Este projeto ainda possui itens pendentes. Conclua ou "
                                       "remova os itens antes de finalizar o projeto."})
        serializer.save()

    def perform_destroy(self, instance):
        if not user_has_permission(self.request.user, "projects.delete"):
            raise PermissionDenied("Seu perfil nao pode excluir projetos.")
        instance.delete()

    @action(detail=True, methods=["get"])
    def health(self, request, pk=None):
        """Retorna status de saúde do projeto com métricas de atividades."""
        from apps.activities.models import Activity

        project = self.get_object()
        today = datetime.date.today()

        activities_qs = Activity.objects.filter(
            project=project,
            deleted_at__isnull=True,
        )
        total_activities = activities_qs.count()
        open_activities = activities_qs.exclude(status__in=["Concluido", "Cancelado"]).count()
        overdue_activities = activities_qs.filter(
            due_at__lt=today,
        ).exclude(status__in=["Concluido", "Cancelado"]).count()

        done = total_activities - open_activities
        completion_pct = round((done / total_activities * 100), 1) if total_activities > 0 else 0

        if project.due_at and project.due_at < today and project.status != "Concluido":
            status = "delayed"
        elif overdue_activities > 0:
            status = "at_risk"
        else:
            status = "on_track"

        return Response({
            "status": status,
            "open_activities": open_activities,
            "total_activities": total_activities,
            "overdue_activities": overdue_activities,
            "completion_pct": completion_pct,
        })


class ProjectCustomFieldViewSet(CompanyScopedModelViewSet):
    serializer_class = ProjectCustomFieldSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProjectCustomField.objects.filter(company=self.request.user.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


class ProjectCustomValueViewSet(CompanyScopedModelViewSet):
    serializer_class = ProjectCustomValueSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = ProjectCustomValue.objects.filter(project__company=self.request.user.company)
        project_id = self.request.query_params.get("project")
        if project_id:
            qs = qs.filter(project_id=project_id)
        return qs
