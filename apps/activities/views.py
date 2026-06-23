from django.db.models import Q
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from common.access import normalize_user_role, user_has_any_permission, user_has_permission
from common.viewsets import CompanyScopedModelViewSet
from .models import (
    Activity,
    ActivityAttachment,
    ActivityComment,
    ActivityTag,
    ActivityTimeEntry,
)
from .serializers import (
    ActivityAttachmentSerializer,
    ActivityCommentSerializer,
    ActivitySerializer,
    ActivityTagSerializer,
    ActivityTimeEntrySerializer,
)


class ActivityViewSet(CompanyScopedModelViewSet):
    queryset = (
        Activity.objects.all()
        .select_related('assignee', 'project', 'sprint', 'ticket')
    )
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


class ActivityCommentViewSet(CompanyScopedModelViewSet):
    queryset = ActivityComment.objects.all()
    serializer_class = ActivityCommentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["activity", "is_internal", "author"]
    search_fields = ["body", "author_name"]
    ordering_fields = "__all__"

    def get_queryset(self):
        if not user_has_any_permission(self.request.user, ["activities.view", "activities.manage"]):
            raise PermissionDenied("Seu perfil nao pode consultar comentarios de atividades.")
        return super().get_queryset()

    def perform_create(self, serializer):
        if not user_has_any_permission(
            self.request.user, ["activities.edit", "activities.manage", "activities.create"]
        ):
            raise PermissionDenied("Seu perfil nao pode comentar atividades.")
        from common.audit import record_audit
        from apps.notifications.services import notify

        comment = serializer.save(
            company=self.request.user.company,
            author=self.request.user,
            author_name=self.request.user.full_name_or_username,
        )
        record_audit(
            action="activity.comment",
            actor=self.request.user,
            instance=comment.activity,
            description="Comentario adicionado a atividade.",
            origin="activities",
            request=self.request,
        )
        assignee = getattr(comment.activity, "assignee", None)
        if assignee:
            notify(
                assignee,
                title=f"Novo comentario na atividade: {comment.activity.title}",
                message=comment.body,
                event="activity.comment",
                actor=self.request.user,
                company=self.request.user.company,
                link=f"atividades/{comment.activity_id}",
                entity=comment.activity,
                origin="activities",
            )

    def perform_update(self, serializer):
        if not user_has_any_permission(self.request.user, ["activities.edit", "activities.manage"]):
            raise PermissionDenied("Seu perfil nao pode alterar comentarios de atividades.")
        serializer.save()

    def perform_destroy(self, instance):
        if not user_has_any_permission(self.request.user, ["activities.edit", "activities.manage"]):
            raise PermissionDenied("Seu perfil nao pode excluir comentarios de atividades.")
        instance.delete()


class ActivityAttachmentViewSet(CompanyScopedModelViewSet):
    queryset = ActivityAttachment.objects.all()
    serializer_class = ActivityAttachmentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["activity", "uploaded_by"]
    search_fields = ["name"]
    ordering_fields = "__all__"

    def get_queryset(self):
        if not user_has_any_permission(self.request.user, ["activities.view", "activities.manage"]):
            raise PermissionDenied("Seu perfil nao pode consultar anexos de atividades.")
        return super().get_queryset()

    def perform_create(self, serializer):
        if not user_has_any_permission(
            self.request.user, ["activities.edit", "activities.manage", "activities.create"]
        ):
            raise PermissionDenied("Seu perfil nao pode anexar arquivos a atividades.")
        serializer.save(company=self.request.user.company, uploaded_by=self.request.user)

    def perform_update(self, serializer):
        if not user_has_any_permission(self.request.user, ["activities.edit", "activities.manage"]):
            raise PermissionDenied("Seu perfil nao pode alterar anexos de atividades.")
        serializer.save()

    def perform_destroy(self, instance):
        if not user_has_any_permission(self.request.user, ["activities.edit", "activities.manage"]):
            raise PermissionDenied("Seu perfil nao pode excluir anexos de atividades.")
        instance.delete()


# ──────────────────────────────────────────────────────────────────────────────
# ActivityDependency
# ──────────────────────────────────────────────────────────────────────────────
from apps.activities.models import ActivityDependency, ActivityCustomField, ActivityCustomValue
from apps.activities.serializers import ActivityDependencySerializer, ActivityCustomFieldSerializer, ActivityCustomValueSerializer


class ActivityDependencyViewSet(CompanyScopedModelViewSet):
    serializer_class = ActivityDependencySerializer

    def get_queryset(self):
        qs = ActivityDependency.objects.filter(
            company=self.request.user.company,
            deleted_at__isnull=True,
        ).select_related("activity", "depends_on")
        activity_id = self.request.query_params.get("activity")
        if activity_id:
            qs = qs.filter(activity_id=activity_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company, created_by=self.request.user)


class ActivityCustomFieldViewSet(CompanyScopedModelViewSet):
    serializer_class = ActivityCustomFieldSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ActivityCustomField.objects.filter(company=self.request.user.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


class ActivityCustomValueViewSet(CompanyScopedModelViewSet):
    serializer_class = ActivityCustomValueSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = ActivityCustomValue.objects.filter(activity__company=self.request.user.company)
        activity_id = self.request.query_params.get("activity")
        if activity_id:
            qs = qs.filter(activity_id=activity_id)
        return qs
