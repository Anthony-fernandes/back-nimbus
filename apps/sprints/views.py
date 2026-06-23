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


# ──────────────────────────────────────────────────────────────────────────────
# Sprint Retrospective & Review
# ──────────────────────────────────────────────────────────────────────────────
from apps.sprints.models import SprintRetrospective, SprintReview
from apps.sprints.serializers import SprintRetrospectiveSerializer, SprintReviewSerializer
from rest_framework.decorators import api_view, permission_classes as _pc
from rest_framework.permissions import IsAuthenticated as _IA
from rest_framework.response import Response as _R


class SprintRetrospectiveViewSet(CompanyScopedModelViewSet):
    serializer_class = SprintRetrospectiveSerializer

    def get_queryset(self):
        qs = SprintRetrospective.objects.filter(
            company=self.request.user.company,
            deleted_at__isnull=True,
        )
        sprint_id = self.request.query_params.get("sprint")
        if sprint_id:
            qs = qs.filter(sprint_id=sprint_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company, created_by=self.request.user)


class SprintReviewViewSet(CompanyScopedModelViewSet):
    serializer_class = SprintReviewSerializer

    def get_queryset(self):
        qs = SprintReview.objects.filter(
            company=self.request.user.company,
            deleted_at__isnull=True,
        )
        sprint_id = self.request.query_params.get("sprint")
        if sprint_id:
            qs = qs.filter(sprint_id=sprint_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company, created_by=self.request.user)


@api_view(["POST"])
@_pc([_IA])
def close_sprint(request, pk):
    """Encerra sprint: cria SprintReview e move atividades incompletas para o backlog."""
    from apps.sprints.models import Sprint
    from apps.activities.models import Activity
    from django.utils import timezone

    try:
        sprint = Sprint.objects.get(pk=pk, company=request.user.company)
    except Sprint.DoesNotExist:
        return _R({"detail": "Sprint não encontrada."}, status=404)

    # Find incomplete activities
    incomplete = Activity.objects.filter(
        sprint=sprint,
        deleted_at__isnull=True,
    ).exclude(status__in=["Concluída", "Concluido", "Done", "Cancelada", "Cancelado"])

    incomplete_ids = list(incomplete.values_list("id", flat=True))
    incomplete_ids_str = [str(i) for i in incomplete_ids]

    planned_pts = sprint.story_points or 0
    delivered_pts = sum(
        a.story_points
        for a in Activity.objects.filter(sprint=sprint, deleted_at__isnull=True).filter(
            status__in=["Concluída", "Concluido", "Done"]
        )
    )

    # Move incomplete items to backlog (remove from sprint)
    incomplete.update(sprint=None)

    # Create review
    review, _ = SprintReview.objects.get_or_create(
        sprint=sprint,
        company=sprint.company,
        defaults={
            "planned_points": planned_pts,
            "delivered_points": delivered_pts,
            "planned_items": Activity.objects.filter(sprint=sprint, deleted_at__isnull=True).count() + len(incomplete_ids),
            "delivered_items": Activity.objects.filter(sprint=sprint, deleted_at__isnull=True).count(),
            "incomplete_activity_ids": incomplete_ids_str,
            "notes": request.data.get("notes", ""),
            "created_by": request.user,
        }
    )

    sprint.status = "Concluída"
    sprint.save()

    return _R({
        "detail": "Sprint encerrada com sucesso.",
        "review_id": str(review.id),
        "incomplete_moved": len(incomplete_ids),
        "delivered_points": delivered_pts,
        "planned_points": planned_pts,
    })


@api_view(["GET"])
@_pc([_IA])
def sprint_velocity(request):
    """Retorna histórico de velocity (story_points entregues) das últimas sprints."""
    from apps.sprints.models import Sprint
    from apps.activities.models import Activity
    from django.db.models import Sum

    company = request.user.company
    project_id = request.query_params.get("project")
    limit = int(request.query_params.get("limit", 10))

    qs = Sprint.objects.filter(company=company, deleted_at__isnull=True)
    if project_id:
        qs = qs.filter(project_id=project_id)
    qs = qs.filter(status__in=["Concluída", "Concluido"]).order_by("-end_at")[:limit]

    result = []
    for sprint in reversed(list(qs)):
        delivered = Activity.objects.filter(
            sprint=sprint,
            deleted_at__isnull=True,
            status__in=["Concluída", "Concluido", "Done"],
        ).aggregate(pts=Sum("story_points"))["pts"] or 0
        result.append({
            "sprint_id": str(sprint.id),
            "sprint_name": sprint.name,
            "end_at": str(sprint.end_at) if sprint.end_at else None,
            "planned_points": sprint.story_points,
            "delivered_points": int(delivered),
        })

    avg_velocity = round(sum(r["delivered_points"] for r in result) / len(result), 1) if result else 0

    return _R({"sprints": result, "avg_velocity": avg_velocity})
