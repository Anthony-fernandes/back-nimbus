from rest_framework import serializers

from apps.users.models import User, UserOrganization
from common.access import normalize_user_role
from .models import Project, ProjectMember, ProjectCustomField, ProjectCustomValue


INTERNAL_PROJECT_ROLES = {
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


class ProjectMemberSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name_or_username", read_only=True)

    class Meta:
        model = ProjectMember
        fields = ["id", "user", "user_name", "role", "active"]
        extra_kwargs = {"user": {"queryset": User.objects.all()}}


class ProjectSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.name", read_only=True, default="")
    organization_id = serializers.CharField(source="client_id", read_only=True, default="")
    organization_name = serializers.CharField(source="client.name", read_only=True, default="")
    department_name = serializers.CharField(source="department.name", read_only=True, default="")
    owner_name = serializers.CharField(source="owner.full_name_or_username", read_only=True)
    leader_name = serializers.CharField(source="owner.full_name_or_username", read_only=True)
    contact_principal_name = serializers.CharField(
        source="contact_principal.full_name_or_username",
        read_only=True,
    )
    team_names = serializers.SerializerMethodField()
    member_links = ProjectMemberSerializer(many=True, required=False)
    # Métricas calculadas — fonte ÚNICA (mesma para lista, detalhe, dashboard).
    progress = serializers.SerializerMethodField()
    health = serializers.SerializerMethodField()
    calculated_status = serializers.SerializerMethodField()
    metrics = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "company",
            "client",
            "client_name",
            "organization_id",
            "organization_name",
            "department",
            "department_name",
            "tipo",
            "metodologia",
            "name",
            "description",
            "status",
            "calculated_status",
            "owner",
            "owner_name",
            "leader_name",
            "contact_principal",
            "contact_principal_name",
            "team",
            "team_names",
            "member_links",
            "budget",
            "real_cost",
            "progress",
            "health",
            "metrics",
            "start_at",
            "due_at",
            "tags",
            "checklist",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {"company": {"required": False, "read_only": True}}

    def _metrics(self, obj):
        # cache por instância para não recalcular em cada método
        if not hasattr(obj, "_metrics_cache"):
            from common.project_metrics import compute_project_metrics
            obj._metrics_cache = compute_project_metrics(obj)
        return obj._metrics_cache

    def get_progress(self, obj):
        return self._metrics(obj)["progress"]

    def get_health(self, obj):
        return self._metrics(obj)["health"]

    def get_calculated_status(self, obj):
        return self._metrics(obj)["calculated_status"]

    def get_metrics(self, obj):
        return self._metrics(obj)

    def get_team_names(self, obj):
        return [user.full_name_or_username for user in obj.team.all()]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Clientes não enxergam dados financeiros internos do projeto.
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user is not None and normalize_user_role(getattr(user, "role", None)) == "CLIENT":
            for field in ("budget", "real_cost", "cost_entries", "costs"):
                data.pop(field, None)
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
        owner = attrs.get("owner", getattr(self.instance, "owner", None))
        contact_principal = attrs.get(
            "contact_principal",
            getattr(self.instance, "contact_principal", None),
        )
        team = attrs.get("team")
        member_links = attrs.get("member_links")

        if organization is None:
            raise serializers.ValidationError({"client": "Informe a organizacao atendida do projeto."})

        if owner:
            self._validate_company_user(owner, "owner")
            if normalize_user_role(owner.role) not in INTERNAL_PROJECT_ROLES:
                raise serializers.ValidationError(
                    {"owner": "O lider do projeto deve ser um usuario interno ou tecnico."}
                )

        if contact_principal:
            self._validate_company_user(contact_principal, "contact_principal")
            if not user_has_organization_link(contact_principal, organization):
                raise serializers.ValidationError(
                    {
                        "contact_principal": (
                            "O contato principal precisa estar vinculado a organizacao atendida."
                        )
                    }
                )

        if team is not None:
            for user in team:
                self._validate_company_user(user, "team")

        if member_links:
            for link in member_links:
                self._validate_company_user(link["user"], "member_links")

        return attrs

    def _sync_project_members(self, project, member_links):
        existing_roles = {
            str(link.user_id): link.role
            for link in project.member_links.all()
        }
        selected_user_ids = {str(user.id) for user in project.team.all()}

        if project.owner_id:
            selected_user_ids.add(str(project.owner_id))

        role_by_user_id = {user_id: existing_roles.get(user_id, "DESENVOLVEDOR") for user_id in selected_user_ids}

        if project.owner_id:
            role_by_user_id[str(project.owner_id)] = "LIDER"

        if member_links is not None:
            role_by_user_id = {}
            for link_data in member_links:
                role_by_user_id[str(link_data["user"].id)] = link_data.get("role", "DESENVOLVEDOR")
            if project.owner_id:
                role_by_user_id[str(project.owner_id)] = "LIDER"
            selected_user_ids = set(role_by_user_id.keys())

        for user in project.team.all():
            ProjectMember.objects.update_or_create(
                project=project,
                user=user,
                defaults={
                    "company": project.company,
                    "role": role_by_user_id.get(str(user.id), "DESENVOLVEDOR"),
                    "active": True,
                },
            )

        if project.owner_id:
            ProjectMember.objects.update_or_create(
                project=project,
                user=project.owner,
                defaults={"company": project.company, "role": "LIDER", "active": True},
            )

        ProjectMember.objects.filter(project=project).exclude(
            user_id__in=selected_user_ids
        ).delete()

    def create(self, validated_data):
        member_links = validated_data.pop("member_links", None)
        team = validated_data.pop("team", [])
        project = Project.objects.create(**validated_data)
        project.team.set(team)
        self._sync_project_members(project, member_links)
        return project

    def update(self, instance, validated_data):
        member_links = validated_data.pop("member_links", None)
        team = validated_data.pop("team", None)

        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        if team is not None:
            instance.team.set(team)

        self._sync_project_members(instance, member_links)
        return instance


class ProjectCustomFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectCustomField
        fields = "__all__"
        extra_kwargs = {"company": {"required": False, "read_only": True}}


class ProjectCustomValueSerializer(serializers.ModelSerializer):
    field_label = serializers.CharField(source="field.label", read_only=True)
    field_type = serializers.CharField(source="field.field_type", read_only=True)
    field_options = serializers.JSONField(source="field.options", read_only=True)

    class Meta:
        model = ProjectCustomValue
        fields = ["id", "project", "field", "field_label", "field_type", "field_options", "value"]
        extra_kwargs = {"project": {"required": False}}
