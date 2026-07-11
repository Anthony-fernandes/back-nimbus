from rest_framework import serializers

from apps.users.models import UserOrganization
from common.access import normalize_user_role
from .models import (
    SLAPolicy,
    Ticket,
    TicketApproval,
    TicketAttachment,
    TicketCategory,
    TicketComment,
    TicketCustomField,
    TicketCustomValue,
    TicketRelation,
    TicketStatusHistory,
    TicketTemplate,
    TicketTimeEntry,
    TicketWorkflowStatus,
    TicketAutomationRule,
    InboundMailbox,
)
from .business_hours_models import BusinessHours, CompanyHoliday


INTERNAL_TICKET_ROLES = {
    "ADMIN",
    "TECHNICIAN",
}


def user_has_organization_link(user, organization):
    if not user or not organization:
        return False

    if getattr(user, "client_id", None) == organization.id:
        return True

    return UserOrganization.objects.filter(
        user=user,
        organization=organization,
        active=True,
    ).exists()


class TicketCustomFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketCustomField
        fields = "__all__"
        extra_kwargs = {"company": {"required": False, "read_only": True}}


class TicketCustomValueSerializer(serializers.ModelSerializer):
    field_label = serializers.CharField(source="field.label", read_only=True)

    class Meta:
        model = TicketCustomValue
        fields = ["id", "field", "field_id", "field_label", "value"]
        extra_kwargs = {"field": {"write_only": True}}


class TicketSerializer(serializers.ModelSerializer):
    resolved_by_name = serializers.CharField(source="resolved_by.full_name_or_username", read_only=True, default="")
    client_name = serializers.CharField(source="client.name", read_only=True, default="")
    organization_id = serializers.CharField(source="client_id", read_only=True, default="")
    organization_name = serializers.CharField(source="client.name", read_only=True, default="")
    department_name = serializers.CharField(source="department.name", read_only=True, default="")
    team_ref_name = serializers.CharField(source="team_ref.name", read_only=True, default="")
    project_name = serializers.CharField(source="project.name", read_only=True)
    sprint_name = serializers.CharField(source="sprint.name", read_only=True)
    requester_user_name = serializers.CharField(
        source="requester_user.full_name_or_username",
        read_only=True,
    )
    contact_responsible_user_name = serializers.CharField(
        source="contact_responsible.full_name_or_username",
        read_only=True,
    )
    responsible_technician_name = serializers.CharField(
        source="responsible_technician.full_name_or_username",
        read_only=True,
    )
    technician_names = serializers.SerializerMethodField()
    custom_values = TicketCustomValueSerializer(many=True, read_only=True)
    current_approver_name = serializers.CharField(
        source="current_approver.full_name_or_username",
        read_only=True,
    )
    approved_by_name = serializers.CharField(
        source="approved_by.full_name_or_username",
        read_only=True,
    )
    classification_pending = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            "id",
            "company",
            "client",
            "client_name",
            "organization_id",
            "organization_name",
            "department",
            "department_name",
            "source",
            "project",
            "project_name",
            "sprint",
            "sprint_name",
            "code",
            "title",
            "description",
            "requester",
            "requester_user",
            "requester_user_name",
            "contact_responsible",
            "contact_responsible_user_name",
            "contact_responsible_name",
            "contact_responsible_phone",
            "responsible_technician",
            "responsible_technician_name",
            "category",
            "subcategory",
            "affected_service",
            "preferred_contact_time",
            "preferred_contact_channel",
            "classification_pending",
            "type",
            "priority",
            "impact",
            "urgency",
            "status",
            "technicians",
            "technician_names",
            "team",
            "team_ref",
            "team_ref_name",
            "sla",
            "sla_due_at",
            "opened_at",
            "due_at",
            "finished_at",
            "est_hours",
            "done_hours",
            "tags",
            "checklist",
            "approval_status",
            "approval_route",
            "approval_reason",
            "current_approver",
            "current_approver_name",
            "approved_by",
            "approved_by_name",
            "approved_at",
            "converted_activity",
            "converted_at",
            "conversion_reason",
            "rating",
            "rating_comment",
            "rated_at",
            "reopen_count",
            "last_reopened_at",
            "resolution_type",
            "resolution_notes",
            "resolved_by",
            "resolved_by_name",
            "resolved_at",
            "custom_values",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "company": {"required": False, "read_only": True},
            "reopen_count": {"read_only": True},
            "last_reopened_at": {"read_only": True},
            "resolution_type": {"read_only": True},
            "resolution_notes": {"read_only": True},
            "resolved_by": {"read_only": True},
            "resolved_at": {"read_only": True},
            "approval_status": {"read_only": True},
            "approval_route": {"read_only": True},
            "approval_reason": {"read_only": True},
            "current_approver": {"read_only": True},
            "approved_by": {"read_only": True},
            "approved_at": {"read_only": True},
            "converted_activity": {"read_only": True},
            "converted_at": {"read_only": True},
            "conversion_reason": {"read_only": True},
            "rating": {"read_only": True},
            "rating_comment": {"read_only": True},
            "rated_at": {"read_only": True},
        }

    def get_technician_names(self, obj):
        return [user.full_name_or_username for user in obj.technicians.all()]

    def get_classification_pending(self, obj):
        """Chamado do portal ainda sem classificação de triagem (categoria ausente)."""
        return obj.status in ("Aberto", "Triagem") and not (obj.category or "").strip()

    def to_representation(self, instance):
        data = super().to_representation(instance)

        if not data.get("contact_responsible_name") and instance.contact_responsible_id:
            data["contact_responsible_name"] = instance.contact_responsible.full_name_or_username

        if not data.get("contact_responsible_phone") and instance.contact_responsible_id:
            data["contact_responsible_phone"] = getattr(instance.contact_responsible, "phone", "") or ""

        return data

    def _get_request_company(self):
        request = self.context.get("request")
        return getattr(getattr(request, "user", None), "company", None)

    def _validate_company_user(self, user, field_name):
        if user is None:
            return None

        request_company = self._get_request_company()
        if request_company and user.company_id != request_company.id:
            raise serializers.ValidationError(
                {field_name: "Selecione um usuario da mesma empresa do usuario autenticado."}
            )

        return user

    def validate(self, attrs):
        organization = attrs.get("client", getattr(self.instance, "client", None))
        requester_user = attrs.get("requester_user", getattr(self.instance, "requester_user", None))
        contact_responsible = attrs.get(
            "contact_responsible",
            getattr(self.instance, "contact_responsible", None),
        )
        responsible_technician = attrs.get(
            "responsible_technician",
            getattr(self.instance, "responsible_technician", None),
        )
        technicians = attrs.get("technicians")

        if organization is None:
            raise serializers.ValidationError({"client": "Informe a organizacao atendida do chamado."})

        if requester_user:
            self._validate_company_user(requester_user, "requester_user")
            if (
                normalize_user_role(requester_user.role) not in INTERNAL_TICKET_ROLES
                and not user_has_organization_link(requester_user, organization)
            ):
                raise serializers.ValidationError(
                    {
                        "requester_user": (
                            "O solicitante precisa estar vinculado a organizacao atendida."
                        )
                    }
                )

        if contact_responsible:
            self._validate_company_user(contact_responsible, "contact_responsible")
            if not user_has_organization_link(contact_responsible, organization):
                raise serializers.ValidationError(
                    {
                        "contact_responsible": (
                            "O contato responsavel precisa estar vinculado a organizacao atendida."
                        )
                    }
                )
            attrs["contact_responsible_name"] = (
                attrs.get("contact_responsible_name")
                or contact_responsible.full_name_or_username
            )
            attrs["contact_responsible_phone"] = (
                attrs.get("contact_responsible_phone")
                or getattr(contact_responsible, "phone", "")
                or ""
            )

        if responsible_technician:
            self._validate_company_user(responsible_technician, "responsible_technician")
            if normalize_user_role(responsible_technician.role) not in INTERNAL_TICKET_ROLES:
                raise serializers.ValidationError(
                    {
                        "responsible_technician": (
                            "O responsavel tecnico deve ser um usuario interno ou tecnico."
                        )
                    }
                )

        if technicians is not None:
            for technician in technicians:
                self._validate_company_user(technician, "technicians")

        if requester_user and not attrs.get("requester"):
            attrs["requester"] = requester_user.full_name_or_username

        return attrs

    def _sync_ticket_relations(self, ticket):
        if ticket.requester_user and ticket.requester != ticket.requester_user.full_name_or_username:
            ticket.requester = ticket.requester_user.full_name_or_username
            ticket.save(update_fields=["requester", "updated_at"])

        contact_fields_to_update = []
        if ticket.contact_responsible_id:
            if not ticket.contact_responsible_name:
                ticket.contact_responsible_name = ticket.contact_responsible.full_name_or_username
                contact_fields_to_update.append("contact_responsible_name")
            if not ticket.contact_responsible_phone:
                ticket.contact_responsible_phone = getattr(ticket.contact_responsible, "phone", "") or ""
                contact_fields_to_update.append("contact_responsible_phone")

        if contact_fields_to_update:
            ticket.save(update_fields=[*contact_fields_to_update, "updated_at"])

        if ticket.responsible_technician_id:
            ticket.technicians.add(ticket.responsible_technician)

    def _save_custom_values(self, ticket, custom_values_data):
        if custom_values_data is None:
            return
        for entry in custom_values_data:
            field_id = entry.get("field_id") or (entry.get("field").id if entry.get("field") else None)
            value = entry.get("value", "")
            if field_id:
                TicketCustomValue.objects.update_or_create(
                    ticket=ticket,
                    field_id=field_id,
                    defaults={"value": value},
                )

    def create(self, validated_data):
        technicians = validated_data.pop("technicians", [])
        custom_values_data = self.initial_data.get("custom_values") if hasattr(self, "initial_data") else None
        ticket = Ticket.objects.create(**validated_data)
        if technicians:
            ticket.technicians.set(technicians)
        self._save_custom_values(ticket, custom_values_data)
        self._sync_ticket_relations(ticket)
        return ticket

    def update(self, instance, validated_data):
        technicians = validated_data.pop("technicians", None)
        custom_values_data = self.initial_data.get("custom_values") if hasattr(self, "initial_data") else None

        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        if technicians is not None:
            instance.technicians.set(technicians)

        self._save_custom_values(instance, custom_values_data)
        self._sync_ticket_relations(instance)
        return instance


class TicketApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketApproval
        fields = [
            "id",
            "company",
            "ticket",
            "approver",
            "approver_name",
            "decision",
            "route",
            "comment",
            "decided_at",
            "created_at",
        ]
        read_only_fields = fields


class TicketCommentSerializer(serializers.ModelSerializer):
    author_display = serializers.CharField(source="author.full_name_or_username", read_only=True)

    class Meta:
        model = TicketComment
        fields = [
            "id",
            "company",
            "ticket",
            "author",
            "author_name",
            "author_display",
            "body",
            "is_internal",
            "note_type",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "company": {"required": False, "read_only": True},
            "author": {"required": False, "read_only": True},
            "author_name": {"required": False},
            "is_internal": {"required": False},
            "note_type": {"required": False},
        }


class TicketTimeEntrySerializer(serializers.ModelSerializer):
    collaborator_display = serializers.CharField(source="collaborator.full_name_or_username", read_only=True)

    class Meta:
        model = TicketTimeEntry
        fields = [
            "id",
            "company",
            "ticket",
            "collaborator",
            "collaborator_name",
            "collaborator_display",
            "date",
            "hours",
            "work_description",
            "created_at",
        ]
        extra_kwargs = {
            "company": {"required": False, "read_only": True},
            "collaborator": {"required": False},
            "collaborator_name": {"required": False},
        }


class TicketAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketAttachment
        fields = [
            "id",
            "company",
            "ticket",
            "uploaded_by",
            "name",
            "url",
            "content_type",
            "size",
            "created_at",
        ]
        extra_kwargs = {
            "company": {"required": False, "read_only": True},
            "uploaded_by": {"required": False, "read_only": True},
        }


class TicketCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketCategory
        fields = "__all__"
        extra_kwargs = {"company": {"required": False, "read_only": True}}


class TicketWorkflowStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketWorkflowStatus
        fields = "__all__"
        extra_kwargs = {"company": {"required": False, "read_only": True}}


class SLAPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = SLAPolicy
        fields = "__all__"
        extra_kwargs = {"company": {"required": False, "read_only": True}}


class TicketTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketTemplate
        fields = '__all__'
        read_only_fields = ['id', 'company', 'created_at', 'updated_at', 'deleted_at']


class TicketStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketStatusHistory
        fields = "__all__"


class TicketRelationSerializer(serializers.ModelSerializer):
    related_ticket_code = serializers.CharField(source="related_ticket.code", read_only=True)
    related_ticket_title = serializers.CharField(source="related_ticket.title", read_only=True)
    related_ticket_status = serializers.CharField(source="related_ticket.status", read_only=True)
    related_ticket_responsible = serializers.CharField(
        source="related_ticket.responsible_technician.full_name_or_username", read_only=True, default=""
    )
    related_ticket_category = serializers.CharField(source="related_ticket.category", read_only=True, default="")

    class Meta:
        model = TicketRelation
        fields = "__all__"
        extra_kwargs = {"company": {"required": False, "read_only": True}, "created_by": {"required": False, "read_only": True}}


class BusinessHoursSerializer(serializers.ModelSerializer):
    weekday_display = serializers.CharField(source="get_weekday_display", read_only=True)

    class Meta:
        model = BusinessHours
        fields = "__all__"
        extra_kwargs = {"company": {"required": False, "read_only": True}}


class CompanyHolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyHoliday
        fields = "__all__"
        extra_kwargs = {"company": {"required": False, "read_only": True}}


class TicketAutomationRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketAutomationRule
        fields = "__all__"
        read_only_fields = ["company", "created_at", "updated_at"]


class InboundMailboxSerializer(serializers.ModelSerializer):
    class Meta:
        model = InboundMailbox
        fields = "__all__"
        read_only_fields = ["company", "created_at", "webhook_token"]
