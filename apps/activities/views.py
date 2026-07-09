from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

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
        from common.status_rules import validate_activity_update
        validate_activity_update(serializer.instance, self.request.data)
        instance = serializer.instance
        data = self.request.data
        previous_due = instance.due_at
        # Planejar via PATCH direto: atividade em Backlog vinculada a sprint vai para 'A fazer'
        if data.get("sprint") and instance.status == "Backlog" and not data.get("status"):
            activity = serializer.save(status="A fazer")
        else:
            activity = serializer.save()
        # Vencimento = prazo para terminar; toda alteração fica registrada na auditoria.
        if "due_at" in data and activity.due_at != previous_due:
            from common.audit import record_audit
            record_audit(
                action="activity.due_at_changed",
                actor=self.request.user,
                instance=activity,
                entity_type="activity",
                request=self.request,
                description=f"Vencimento alterado de '{previous_due or '—'}' para '{activity.due_at or '—'}'.",
                origin="activities",
                changes=[{"field": "due_at", "old": str(previous_due) if previous_due else None, "new": str(activity.due_at) if activity.due_at else None}],
            )

    def perform_destroy(self, instance):
        if not user_has_permission(self.request.user, "activities.delete"):
            raise PermissionDenied("Seu perfil nao pode excluir atividades.")
        instance.delete()

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        """Finaliza a atividade com resolução documentada obrigatória."""
        from django.utils import timezone as dj_tz
        from common.audit import record_audit

        activity = self.get_object()
        if not user_has_any_permission(request.user, ["activities.edit", "activities.manage"]):
            raise PermissionDenied("Seu perfil nao pode finalizar atividades.")

        if activity.status in ("Concluída", "Concluido", "Concluído", "Cancelada", "Cancelado"):
            return Response({"detail": "Esta atividade já está finalizada."}, status=400)
        if activity.status in ("Backlog", "A fazer"):
            return Response({"detail": "Inicie o atendimento antes de finalizar a atividade."}, status=400)

        resolution_type = (request.data.get("resolution_type") or "").strip()
        resolution_notes = (request.data.get("resolution_notes") or "").strip()
        if not resolution_type:
            return Response({"detail": "Informe o tipo de conclusão."}, status=400)
        if not resolution_notes:
            return Response({"detail": "Descreva a resolução aplicada antes de finalizar."}, status=400)

        pending_required = [
            item.get("text") for item in (activity.checklist or [])
            if item.get("required") and not item.get("done")
        ]
        if pending_required:
            return Response(
                {"detail": f"Subtarefas obrigatórias pendentes: {', '.join(pending_required[:5])}"},
                status=400,
            )

        final_status = "Cancelado" if resolution_type == "Cancelado" else "Concluída"
        previous_status = activity.status

        activity.resolution_type = resolution_type
        activity.resolution_notes = resolution_notes
        activity.resolved_by = request.user
        activity.resolved_at = dj_tz.now()
        activity.status = final_status
        activity.save(update_fields=[
            "resolution_type", "resolution_notes", "resolved_by", "resolved_at",
            "status", "updated_at",
        ])

        ActivityComment.objects.create(
            company=activity.company,
            activity=activity,
            author=request.user,
            author_name=getattr(request.user, "full_name_or_username", ""),
            body=f"**{resolution_type}** — {resolution_notes}",
            note_type="resolution",
        )
        record_audit(
            action="activity.resolved",
            actor=request.user,
            instance=activity,
            request=request,
            description=f"Atividade finalizada como '{resolution_type}' (era '{previous_status}').",
            origin="activities",
            metadata={"resolution_type": resolution_type},
        )
        return Response(self.get_serializer(activity).data)

    @action(detail=True, methods=["post"])
    def reopen(self, request, pk=None):
        """Reabre uma atividade finalizada — motivo obrigatório."""
        from django.utils import timezone as dj_tz
        from common.audit import record_audit

        activity = self.get_object()
        if not user_has_any_permission(request.user, ["activities.edit", "activities.manage"]):
            raise PermissionDenied("Seu perfil nao pode reabrir atividades.")

        if activity.status not in ("Concluída", "Concluido", "Concluído", "Cancelada", "Cancelado"):
            return Response({"detail": "Apenas atividades finalizadas podem ser reabertas."}, status=400)

        reason = (request.data.get("reason") or "").strip()
        if not reason:
            return Response({"detail": "Informe o motivo da reabertura."}, status=400)

        previous_status = activity.status
        activity.status = "Em progresso"
        activity.reopen_count = (activity.reopen_count or 0) + 1
        activity.last_reopened_at = dj_tz.now()
        activity.status_reason = f"Reaberto: {reason}"[:255]
        activity.save(update_fields=[
            "status", "reopen_count", "last_reopened_at", "status_reason", "updated_at",
        ])

        ActivityComment.objects.create(
            company=activity.company,
            activity=activity,
            author=request.user,
            author_name=getattr(request.user, "full_name_or_username", ""),
            body=f"Atividade reaberta. Motivo: {reason}",
            note_type="internal",
        )
        record_audit(
            action="activity.reopened",
            actor=request.user,
            instance=activity,
            request=request,
            description=f"Atividade reaberta (era '{previous_status}'): {reason}",
            origin="activities",
        )
        return Response(self.get_serializer(activity).data)


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
        activity = serializer.validated_data.get("activity")
        if activity and activity.status in ("Backlog", "A fazer"):
            raise PermissionDenied("Inicie o atendimento antes de apontar horas nesta atividade.")
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
