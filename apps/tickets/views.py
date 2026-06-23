import logging

from django.db.models import Q

logger = logging.getLogger(__name__)
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.services import notify, notify_many
from common.access import (
    get_user_organization_ids,
    normalize_user_role,
    user_has_any_permission,
    user_has_permission,
)
from common.audit import record_audit
from common.viewsets import CompanyScopedModelViewSet
from .approvals import resolve_approval_plan, service_desk_approvers
from .models import (
    Ticket,
    TicketApproval,
    TicketAttachment,
    TicketCategory,
    TicketComment,
    TicketCustomField,
    TicketWorkflowStatus,
)
from .serializers import (
    TicketApprovalSerializer,
    TicketAttachmentSerializer,
    TicketCategorySerializer,
    TicketCommentSerializer,
    TicketCustomFieldSerializer,
    TicketSerializer,
    TicketWorkflowStatusSerializer,
)


def _ticket_link(ticket):
    return f"chamados/{ticket.id}"


class TicketViewSet(CompanyScopedModelViewSet):
    queryset = (
        Ticket.objects.all()
        .select_related('requester_user', 'responsible_technician', 'current_approver', 'client', 'project')
        .prefetch_related('approvals')
    )
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
        "approval_status",
        "approval_route",
        "current_approver",
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

    def _approval_scope(self, user):
        """Chamados que o usuario pode ver por ser aprovador (vinculado ou Service Desk)."""

        scope = Q(current_approver=user)
        if getattr(user, "is_service_desk_approver", False):
            scope |= Q(approval_route="SERVICE_DESK", approval_status="Aguardando Aprovacao")
        return scope

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        role = normalize_user_role(getattr(user, "role", None))
        approval_scope = self._approval_scope(user)

        if role == "CLIENT":
            filters = approval_scope
            if user_has_permission(user, "tickets.viewOwn"):
                filters |= Q(requester_user=user)
            if user_has_permission(user, "tickets.viewOrganization"):
                filters |= Q(client_id__in=get_user_organization_ids(user))
            return queryset.filter(filters).distinct()

        if role == "TECHNICIAN":
            if user_has_permission(user, "tickets.viewAll"):
                return queryset

            filters = approval_scope
            if user_has_permission(user, "tickets.viewAssigned"):
                filters |= Q(responsible_technician=user) | Q(technicians=user)
            if user_has_permission(user, "tickets.viewTeam") and getattr(user, "technical_group", ""):
                filters |= Q(team__iexact=user.technical_group)
            if user_has_permission(user, "tickets.viewOwn"):
                filters |= Q(requester_user=user)

            return queryset.filter(filters).distinct()

        if role == "ADMIN":
            if user_has_permission(user, "tickets.viewAll"):
                return queryset
            return queryset.filter(approval_scope).distinct()

        return queryset.filter(approval_scope).distinct()

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
            self._post_create(serializer.instance)
            if serializer.instance.company.auto_assign:
                from .services import auto_assign_ticket
                auto_assign_ticket(serializer.instance)
            return

        super().perform_create(serializer)
        self._post_create(serializer.instance)
        if serializer.instance.company.auto_assign:
            from .services import auto_assign_ticket
            auto_assign_ticket(serializer.instance)

    def perform_update(self, serializer):
        ticket = self.get_object()
        self._ensure_can_update(ticket)
        previous = {
            "status": ticket.status,
            "priority": ticket.priority,
            "responsible_technician_id": ticket.responsible_technician_id,
        }
        serializer.save()
        self._post_update(serializer.instance, previous)

    def perform_destroy(self, instance):
        self._ensure_can_delete()
        record_audit(
            action="ticket.deleted",
            instance=instance,
            request=self.request,
            description=f"Chamado {instance.code} excluido.",
            origin="tickets",
        )
        instance.delete()

    # ------------------------------------------------------------------
    # Fluxo de aprovacao e rastreabilidade
    # ------------------------------------------------------------------

    def _post_create(self, ticket):
        # Calcula SLA automaticamente
        try:
            from .sla import compute_sla_due_at
            compute_sla_due_at(ticket)
            ticket.save(update_fields=["sla_due_at", "updated_at"])
        except Exception as exc:
            logger.exception("Failed to compute SLA for ticket %s: %s", getattr(ticket, "id", "?"), exc)

        plan = resolve_approval_plan(ticket)
        ticket.approval_route = plan["route"]
        ticket.approval_status = plan["status"]
        ticket.approval_reason = plan["reason"]
        update_fields = ["approval_route", "approval_status", "approval_reason", "updated_at"]

        if plan["route"] == "AUTO":
            ticket.approved_at = timezone.now()
            ticket.current_approver = None
            if ticket.status in ("Aberto", "Triagem"):
                ticket.status = "Aprovado"
            update_fields += ["approved_at", "current_approver", "status"]
        elif plan["route"] in ("APPROVER", "SERVICE_DESK"):
            ticket.current_approver = plan["approver"]
            ticket.status = "Aguardando Aprovacao"
            update_fields += ["current_approver", "status"]
        else:
            ticket.current_approver = None
            update_fields += ["current_approver"]

        ticket.save(update_fields=update_fields)

        record_audit(
            action="ticket.created",
            actor=ticket.requester_user or self.request.user,
            instance=ticket,
            request=self.request,
            description=f"Chamado {ticket.code} aberto.",
            origin="tickets",
            metadata={"approval_route": plan["route"], "approval_status": plan["status"]},
        )

        try:
            from apps.webhooks.services import dispatch_webhook
            dispatch_webhook(ticket.company, "ticket.created", {
                "id": str(ticket.id), "code": ticket.code, "title": ticket.title,
                "status": ticket.status, "priority": ticket.priority,
            })
        except Exception as exc:
            logger.warning("Webhook dispatch failed for ticket %s: %s", getattr(ticket, "id", "?"), exc)

        if plan["route"] in ("APPROVER", "SERVICE_DESK"):
            approver = plan["approver"]
            TicketApproval.objects.create(
                company=ticket.company,
                ticket=ticket,
                approver=approver,
                approver_name=approver.full_name_or_username if approver else "",
                decision="PENDENTE",
                route=plan["route"],
                comment=plan["reason"],
            )
            if plan["route"] == "APPROVER" and approver:
                notify(
                    approver,
                    title=f"Aprovacao pendente: {ticket.code}",
                    message=f"O chamado '{ticket.title}' aguarda sua aprovacao.",
                    event="ticket.approval_requested",
                    actor=ticket.requester_user,
                    company=ticket.company,
                    link=_ticket_link(ticket),
                    entity=ticket,
                    origin="tickets",
                )
            elif plan["route"] == "SERVICE_DESK":
                notify_many(
                    service_desk_approvers(ticket.company),
                    title=f"Aprovacao pendente (Service Desk): {ticket.code}",
                    message=f"O chamado '{ticket.title}' aguarda aprovacao da equipe de chamados.",
                    event="ticket.approval_requested",
                    actor=ticket.requester_user,
                    company=ticket.company,
                    link=_ticket_link(ticket),
                    entity=ticket,
                    origin="tickets",
                )

    def _post_update(self, ticket, previous):
        changes = []
        if previous["status"] != ticket.status:
            changes.append({"field": "status", "old": previous["status"], "new": ticket.status})
        if previous["priority"] != ticket.priority:
            changes.append({"field": "priority", "old": previous["priority"], "new": ticket.priority})
        if previous["responsible_technician_id"] != ticket.responsible_technician_id:
            changes.append({"field": "responsible_technician", "old": str(previous["responsible_technician_id"] or ""), "new": str(ticket.responsible_technician_id or "")})

        if not changes:
            return

        record_audit(
            action="ticket.updated",
            instance=ticket,
            request=self.request,
            description=f"Chamado {ticket.code} atualizado.",
            origin="tickets",
            changes=changes,
        )

        if previous["priority"] != ticket.priority and ticket.requester_user:
            notify(
                ticket.requester_user,
                title=f"Prioridade alterada: {ticket.code}",
                message=f"Prioridade alterada para '{ticket.priority}'.",
                event="ticket.priority_changed",
                actor=self.request.user,
                company=ticket.company,
                link=_ticket_link(ticket),
                entity=ticket,
                origin="tickets",
            )

        if (
            previous["responsible_technician_id"] != ticket.responsible_technician_id
            and ticket.responsible_technician
        ):
            notify(
                ticket.responsible_technician,
                title=f"Chamado atribuido: {ticket.code}",
                message=f"Voce e o responsavel pelo chamado '{ticket.title}'.",
                event="ticket.assigned",
                actor=self.request.user,
                company=ticket.company,
                link=_ticket_link(ticket),
                entity=ticket,
                origin="tickets",
            )

    def _ensure_can_decide(self, ticket):
        user = self.request.user
        if ticket.approval_status not in ("Aguardando Aprovacao", "Ajustes Solicitados"):
            raise ValidationError("Este chamado nao esta aguardando aprovacao.")
        if ticket.current_approver_id and ticket.current_approver_id == user.id:
            return
        if ticket.approval_route == "SERVICE_DESK" and (
            getattr(user, "is_service_desk_approver", False)
            or user_has_permission(user, "tickets.approve")
        ):
            return
        if user_has_permission(user, "tickets.approve"):
            return
        raise PermissionDenied("Voce nao e o aprovador deste chamado.")

    def _record_decision(self, ticket, decision, comment):
        user = self.request.user
        pending = ticket.approvals.filter(decision="PENDENTE").order_by("-created_at").first()
        if pending:
            pending.decision = decision
            pending.approver = user
            pending.approver_name = user.full_name_or_username
            pending.comment = comment or pending.comment
            pending.decided_at = timezone.now()
            pending.save()
        else:
            TicketApproval.objects.create(
                company=ticket.company,
                ticket=ticket,
                approver=user,
                approver_name=user.full_name_or_username,
                decision=decision,
                route=ticket.approval_route,
                comment=comment,
                decided_at=timezone.now(),
            )

        update_fields = ["approval_status", "status", "current_approver", "updated_at"]
        if decision == "APROVADO":
            ticket.approval_status = "Aprovado"
            ticket.status = "Aprovado"
            ticket.approved_by = user
            ticket.approved_at = timezone.now()
            ticket.current_approver = None
            update_fields += ["approved_by", "approved_at"]
            event, title = "ticket.approved", f"Chamado aprovado: {ticket.code}"
        elif decision == "REPROVADO":
            ticket.approval_status = "Reprovado"
            ticket.status = "Reprovado"
            ticket.current_approver = None
            event, title = "ticket.rejected", f"Chamado reprovado: {ticket.code}"
        else:  # AJUSTES
            ticket.approval_status = "Ajustes Solicitados"
            ticket.status = "Ajustes Solicitados"
            event, title = "ticket.changes_requested", f"Ajustes solicitados: {ticket.code}"

        ticket.save(update_fields=update_fields)

        record_audit(
            action=event,
            instance=ticket,
            request=self.request,
            description=f"{title}. {comment}".strip(),
            origin="tickets",
            metadata={"decision": decision},
        )

        if ticket.requester_user:
            notify(
                ticket.requester_user,
                title=title,
                message=comment or ticket.approval_reason,
                event=event,
                actor=user,
                company=ticket.company,
                link=_ticket_link(ticket),
                entity=ticket,
                origin="tickets",
            )

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        ticket = self.get_object()
        self._ensure_can_decide(ticket)
        self._record_decision(ticket, "APROVADO", request.data.get("comment", ""))
        return Response(self.get_serializer(ticket).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        ticket = self.get_object()
        self._ensure_can_decide(ticket)
        self._record_decision(ticket, "REPROVADO", request.data.get("comment", ""))
        return Response(self.get_serializer(ticket).data)

    @action(detail=True, methods=["post"], url_path="request-changes")
    def request_changes(self, request, pk=None):
        ticket = self.get_object()
        self._ensure_can_decide(ticket)
        self._record_decision(ticket, "AJUSTES", request.data.get("comment", ""))
        return Response(self.get_serializer(ticket).data)

    @action(detail=True, methods=["get"], url_path="approvals")
    def approval_history(self, request, pk=None):
        ticket = self.get_object()
        data = TicketApprovalSerializer(ticket.approvals.all(), many=True).data
        return Response(data)

    @action(detail=True, methods=["post"])
    def rate(self, request, pk=None):
        ticket = self.get_object()
        # Only the requester (client) can rate
        if str(ticket.requester_id) != str(request.user.id) and str(ticket.client_user_id or "") != str(request.user.id):
            return Response({"detail": "Apenas o solicitante pode avaliar o chamado."}, status=403)
        # Only closed/resolved tickets
        closed_statuses = ["Resolvido", "Encerrado", "Fechado", "Concluido", "Convertido em Atividade de Projeto"]
        if ticket.status not in closed_statuses:
            return Response({"detail": "O chamado precisa estar encerrado para ser avaliado."}, status=400)
        if ticket.rated_at:
            return Response({"detail": "Este chamado ja foi avaliado."}, status=400)

        rating = request.data.get("rating")
        comment = request.data.get("comment", "")

        if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
            return Response({"detail": "Avaliacao deve ser entre 1 e 5."}, status=400)

        from django.utils import timezone
        ticket.rating = rating
        ticket.rating_comment = comment
        ticket.rated_at = timezone.now()
        ticket.save(update_fields=["rating", "rating_comment", "rated_at"])

        from common.audit import record_audit
        record_audit(request, "TICKET_RATED", ticket, label=ticket.title, changes={"rating": rating, "comment": comment})

        from apps.tickets.serializers import TicketSerializer
        return Response(TicketSerializer(ticket, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="convert-to-activity")
    def convert_to_activity(self, request, pk=None):
        from apps.activities.models import (
            Activity,
            ActivityAttachment,
            ActivityComment,
            ActivityTimeEntry,
        )

        ticket = self.get_object()
        if not user_has_any_permission(request.user, ["activities.create", "activities.manage"]):
            raise PermissionDenied("Seu perfil nao pode converter chamados em atividades.")
        if ticket.converted_activity_id:
            raise ValidationError("Chamado ja convertido em atividade de projeto.")

        project_id = request.data.get("project") or ticket.project_id
        sprint_id = request.data.get("sprint") or ticket.sprint_id
        assignee = ticket.responsible_technician

        activity = Activity.objects.create(
            company=ticket.company,
            title=ticket.title,
            description=ticket.description,
            type="Tarefa",
            status="Backlog",
            priority=ticket.priority,
            assignee=assignee,
            project_id=project_id,
            sprint_id=sprint_id,
            ticket=ticket,
            est_hours=ticket.est_hours,
            tags=list(ticket.tags or []),
            checklist=list(ticket.checklist or []),
        )

        # Transferir comentarios
        for comment in ticket.comments.all():
            ActivityComment.objects.create(
                company=ticket.company,
                activity=activity,
                author=comment.author,
                author_name=comment.author_name,
                body=comment.body,
                is_internal=comment.is_internal,
                source="ticket-conversion",
            )

        # Transferir anexos
        for attachment in ticket.attachments.all():
            ActivityAttachment.objects.create(
                company=ticket.company,
                activity=activity,
                uploaded_by=attachment.uploaded_by,
                name=attachment.name,
                url=attachment.url,
                content_type=attachment.content_type,
                size=attachment.size,
                source="ticket-conversion",
            )

        # Transferir horas executadas como apontamento
        if ticket.done_hours and ticket.done_hours > 0:
            ActivityTimeEntry.objects.create(
                company=ticket.company,
                activity=activity,
                project_id=project_id,
                sprint_id=sprint_id,
                collaborator=assignee,
                collaborator_name=assignee.full_name_or_username if assignee else "",
                date=timezone.now().date(),
                hours=ticket.done_hours,
                work_description=f"Horas transferidas do chamado {ticket.code}.",
            )

        reason = "Chamado convertido em atividade de projeto."
        ticket.converted_activity = activity
        ticket.converted_at = timezone.now()
        ticket.conversion_reason = reason
        ticket.status = "Convertido em Atividade de Projeto"
        ticket.finished_at = timezone.now()
        ticket.save(
            update_fields=[
                "converted_activity",
                "converted_at",
                "conversion_reason",
                "status",
                "finished_at",
                "updated_at",
            ]
        )

        record_audit(
            action="ticket.converted",
            instance=ticket,
            request=self.request,
            description=reason,
            origin="tickets",
            metadata={"activity_id": str(activity.id)},
        )
        record_audit(
            action="activity.created",
            instance=activity,
            request=self.request,
            description=f"Atividade criada a partir do chamado {ticket.code}.",
            origin="tickets",
            metadata={"ticket_id": str(ticket.id)},
        )

        recipients = [ticket.requester_user, assignee]
        notify_many(
            [r for r in recipients if r],
            title=f"Chamado convertido em atividade: {ticket.code}",
            message=reason,
            event="ticket.converted",
            actor=request.user,
            company=ticket.company,
            link=f"atividades/{activity.id}",
            entity=ticket,
            origin="tickets",
        )

        return Response(
            {
                "ticket": self.get_serializer(ticket).data,
                "activity_id": str(activity.id),
                "reason": reason,
            }
        )

    @action(detail=True, methods=["post"], url_path="convert-to-kb")
    def convert_to_kb(self, request, pk=None):
        ticket = self.get_object()
        from apps.knowledge.models import KnowledgeArticle
        category_id = request.data.get("category")
        category = None
        if category_id:
            from apps.knowledge.models import KnowledgeCategory
            try:
                category = KnowledgeCategory.objects.get(id=category_id, company=request.user.company)
            except KnowledgeCategory.DoesNotExist:
                pass
        content = ticket.description or ticket.title
        article = KnowledgeArticle.objects.create(
            company=request.user.company,
            title=ticket.title,
            slug=f"ticket-{str(ticket.id)[:8]}",
            content=content,
            summary=content[:300],
            category=category,
            status="DRAFT",
            visibility="INTERNAL",
            author=request.user,
            source_ticket=ticket,
        )
        from common.audit import record_audit
        record_audit(
            request=request,
            action="CONVERT_TICKET_TO_KB",
            instance=article,
            entity_label=article.title,
        )
        from apps.knowledge.serializers import KnowledgeArticleSerializer
        return Response(KnowledgeArticleSerializer(article).data, status=201)


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


class TicketCommentViewSet(CompanyScopedModelViewSet):
    queryset = TicketComment.objects.all()
    serializer_class = TicketCommentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["ticket", "is_internal", "author"]
    search_fields = ["body", "author_name"]
    ordering_fields = "__all__"

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        role = normalize_user_role(getattr(user, "role", None))
        if role == "CLIENT":
            # Cliente ve apenas comentarios publicos de chamados que pode acessar.
            return queryset.filter(is_internal=False, ticket__requester_user=user)
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        is_internal = bool(serializer.validated_data.get("is_internal"))
        if is_internal and not user_has_any_permission(user, ["tickets.commentInternal", "tickets.edit"]):
            raise PermissionDenied("Seu perfil nao pode adicionar comentarios internos.")
        if not is_internal and not user_has_any_permission(
            user, ["tickets.commentPublic", "tickets.commentOwn", "tickets.edit"]
        ):
            raise PermissionDenied("Seu perfil nao pode comentar chamados.")

        comment = serializer.save(
            company=user.company,
            author=user,
            author_name=user.full_name_or_username,
        )
        ticket = comment.ticket
        record_audit(
            action="ticket.comment",
            actor=user,
            instance=ticket,
            request=self.request,
            description="Comentario adicionado ao chamado.",
            origin="tickets",
        )

        recipients = [ticket.requester_user, ticket.responsible_technician]
        if comment.is_internal:
            recipients = [ticket.responsible_technician]
        notify_many(
            [r for r in recipients if r],
            title=f"Novo comentario: {ticket.code}",
            message=comment.body,
            event="ticket.comment",
            actor=user,
            company=ticket.company,
            link=_ticket_link(ticket),
            entity=ticket,
            origin="tickets",
        )

    def perform_update(self, serializer):
        if not user_has_any_permission(self.request.user, ["tickets.edit", "tickets.commentInternal"]):
            raise PermissionDenied("Seu perfil nao pode alterar comentarios.")
        serializer.save()

    def perform_destroy(self, instance):
        if not user_has_any_permission(self.request.user, ["tickets.edit"]):
            raise PermissionDenied("Seu perfil nao pode excluir comentarios.")
        instance.delete()


class TicketAttachmentViewSet(CompanyScopedModelViewSet):
    queryset = TicketAttachment.objects.all()
    serializer_class = TicketAttachmentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["ticket", "uploaded_by"]
    search_fields = ["name"]
    ordering_fields = "__all__"

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        role = normalize_user_role(getattr(user, "role", None))
        if role == "CLIENT":
            return queryset.filter(ticket__requester_user=user)
        return queryset

    def perform_create(self, serializer):
        if not user_has_any_permission(
            self.request.user, ["tickets.edit", "tickets.attachFiles", "tickets.create"]
        ):
            raise PermissionDenied("Seu perfil nao pode anexar arquivos.")
        attachment = serializer.save(company=self.request.user.company, uploaded_by=self.request.user)
        record_audit(
            action="ticket.attachment",
            actor=self.request.user,
            instance=attachment.ticket,
            request=self.request,
            description=f"Anexo '{attachment.name}' adicionado ao chamado.",
            origin="tickets",
        )

    def perform_update(self, serializer):
        if not user_has_any_permission(self.request.user, ["tickets.edit"]):
            raise PermissionDenied("Seu perfil nao pode alterar anexos.")
        serializer.save()

    def perform_destroy(self, instance):
        if not user_has_any_permission(self.request.user, ["tickets.edit"]):
            raise PermissionDenied("Seu perfil nao pode excluir anexos.")
        instance.delete()


class TicketApprovalViewSet(CompanyScopedModelViewSet):
    queryset = TicketApproval.objects.all()
    serializer_class = TicketApprovalSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "head", "options"]
    filterset_fields = ["ticket", "decision", "route", "approver"]
    search_fields = ["approver_name", "comment"]
    ordering_fields = "__all__"


class SLAPolicyViewSet(CompanyScopedModelViewSet):
    permission_classes = [IsAuthenticated]
    filterset_fields = ["active", "priority", "category"]
    ordering_fields = "__all__"

    def get_queryset(self):
        from .models import SLAPolicy
        return SLAPolicy.objects.filter(company=self.request.user.company, deleted_at__isnull=True)

    def get_serializer_class(self):
        from .serializers import SLAPolicySerializer
        return SLAPolicySerializer

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)

    @action(detail=False, methods=["get"], url_path="alerts")
    def alerts(self, request):
        from .sla import check_sla_alerts
        return Response(check_sla_alerts(request.user.company))


class TicketTemplateViewSet(CompanyScopedModelViewSet):
    permission_classes = [IsAuthenticated]
    filterset_fields = ['active', 'type', 'priority']
    ordering_fields = '__all__'

    def get_queryset(self):
        from .models import TicketTemplate
        return TicketTemplate.objects.filter(company=self.request.user.company, deleted_at__isnull=True)

    def get_serializer_class(self):
        from .serializers import TicketTemplateSerializer
        return TicketTemplateSerializer

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


class TicketCustomFieldViewSet(CompanyScopedModelViewSet):
    queryset = TicketCustomField.objects.all()
    serializer_class = TicketCustomFieldSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["active", "field_type", "required"]
    search_fields = ["name", "label"]
    ordering_fields = "__all__"

    def get_queryset(self):
        return TicketCustomField.objects.filter(
            company=self.request.user.company,
            deleted_at__isnull=True,
        )

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


class TicketReportsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.db.models import Avg, Count
        from django.db.models.functions import TruncDate
        import datetime

        company = request.user.company
        qs = Ticket.objects.filter(company=company, deleted_at__isnull=True)

        total = qs.count()
        open_count = qs.filter(status__in=["Aberto", "Triagem", "Em atendimento", "Aguardando cliente", "Aguardando atendimento"]).count()
        closed_count = qs.filter(status__in=["Finalizado", "Cancelado"]).count()
        pending_count = total - open_count - closed_count

        avg_csat = qs.filter(rating__isnull=False).aggregate(avg=Avg("rating"))["avg"]
        avg_csat = round(float(avg_csat), 2) if avg_csat is not None else None

        # Average response hours: created_at to first comment
        from apps.tickets.models import TicketComment
        first_comments = TicketComment.objects.filter(
            company=company, is_internal=False, deleted_at__isnull=True
        ).values("ticket_id").annotate(first_reply=__import__("django.db.models", fromlist=["Min"]).Min("created_at"))
        response_hours_list = []
        ticket_map = {t.id: t.created_at for t in qs.only("id", "created_at")}
        for fc in first_comments:
            tid = fc["ticket_id"]
            if tid in ticket_map:
                delta = fc["first_reply"] - ticket_map[tid]
                response_hours_list.append(delta.total_seconds() / 3600)
        avg_response_hours = round(sum(response_hours_list) / len(response_hours_list), 2) if response_hours_list else None

        # Volume last 30 days
        cutoff = timezone.now() - datetime.timedelta(days=30)
        volume_qs = (
            qs.filter(created_at__gte=cutoff)
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )
        volume_by_day_data = [{"date": str(item["date"]), "count": item["count"]} for item in volume_qs]

        # Top categories
        top_categories = list(
            qs.values("category").annotate(count=Count("id")).order_by("-count")[:10]
        )

        return Response({
            "total": total,
            "open": open_count,
            "closed": closed_count,
            "pending": pending_count,
            "avg_csat": avg_csat,
            "avg_response_hours": avg_response_hours,
            "volume_by_day": volume_by_day_data,
            "top_categories": top_categories,
        })
