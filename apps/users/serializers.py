from rest_framework import serializers

from apps.clients.models import Client
from common.access import (
    flatten_granted_permissions,
    normalize_permission_map,
    normalize_user_role,
    permission_map_from_keys,
    resolve_user_permissions,
)
from .models import Department, PermissionBlock, Position, User, UserOrganization


class DepartmentSerializer(serializers.ModelSerializer):
    manager_name = serializers.CharField(source="manager.full_name_or_username", read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = [
            "id",
            "company",
            "name",
            "description",
            "manager",
            "manager_name",
            "member_count",
            "active",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {"company": {"required": False, "read_only": True}}

    def get_member_count(self, obj):
        return obj.members.count()


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = [
            "id",
            "company",
            "name",
            "description",
            "auto_approval",
            "active",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {"company": {"required": False, "read_only": True}}


class UserOrganizationSerializer(serializers.ModelSerializer):
    organization_id = serializers.CharField(read_only=True)
    organization_name = serializers.CharField(source="organization.name", read_only=True)

    class Meta:
        model = UserOrganization
        fields = [
            "id",
            "organization",
            "organization_id",
            "organization_name",
            "role",
            "active",
        ]
        extra_kwargs = {"organization": {"queryset": Client.objects.all()}}


class PermissionBlockSerializer(serializers.ModelSerializer):
    def validate_permissions(self, value):
        return normalize_permission_map(value)

    class Meta:
        model = PermissionBlock
        fields = [
            "id",
            "name",
            "description",
            "permissions",
            "active",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {"permissions": {"required": False}}


class UserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    client_id = serializers.CharField(read_only=True)
    client_name = serializers.CharField(source="client.name", read_only=True)
    organization_id = serializers.CharField(source="client_id", read_only=True)
    organization_name = serializers.CharField(source="client.name", read_only=True)
    organization_links = UserOrganizationSerializer(many=True, required=False)
    permission_blocks = serializers.PrimaryKeyRelatedField(
        queryset=PermissionBlock.objects.all(),
        many=True,
        required=False,
    )
    permission_blocks_data = PermissionBlockSerializer(
        source="permission_blocks",
        many=True,
        read_only=True,
    )
    granted_permissions = serializers.JSONField(required=False)
    denied_permissions = serializers.JSONField(required=False)
    resolved_permissions = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    department_name = serializers.CharField(source="department.name", read_only=True)
    position_name = serializers.CharField(source="position.name", read_only=True)
    supervisor_name = serializers.CharField(source="supervisor.full_name_or_username", read_only=True)
    manager_name = serializers.CharField(source="manager.full_name_or_username", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "name",
            "role",
            "client",
            "client_id",
            "client_name",
            "organization_id",
            "organization_name",
            "organization_links",
            "job_title",
            "specialty",
            "phone",
            "total_hours",
            "used_hours",
            "hourly_cost",
            "technical_group",
            "department",
            "department_name",
            "position",
            "position_name",
            "supervisor",
            "supervisor_name",
            "manager",
            "manager_name",
            "approval_mode",
            "is_service_desk_approver",
            "permissions_json",
            "granted_permissions",
            "denied_permissions",
            "permission_blocks",
            "permission_blocks_data",
            "resolved_permissions",
            "company",
            "password",
            "is_active",
        ]
        read_only_fields = ["id", "name", "resolved_permissions"]
        extra_kwargs = {"company": {"required": False}}

    def get_name(self, obj):
        return obj.full_name_or_username

    def get_resolved_permissions(self, obj):
        return resolve_user_permissions(obj)

    def _get_request_company(self):
        request = self.context.get("request")
        return getattr(getattr(request, "user", None), "company", None)

    def _validate_client_scope(self, organization):
        if organization is None:
            return None

        request_company = self._get_request_company()
        target_company = self.initial_data.get("company") or getattr(self.instance, "company_id", None)

        if request_company and organization.company_id != request_company.id:
            raise serializers.ValidationError(
                "Selecione uma organizacao da mesma empresa do usuario autenticado."
            )

        if target_company and str(organization.company_id) != str(target_company):
            raise serializers.ValidationError(
                "A organizacao selecionada nao pertence a empresa informada."
            )

        return organization

    def _validate_permission_block_scope(self, block):
        request_company = self._get_request_company()
        target_company = self.initial_data.get("company") or getattr(self.instance, "company_id", None)

        if request_company and block.company_id != request_company.id:
            raise serializers.ValidationError(
                "Selecione um bloco de permissoes da mesma empresa do usuario autenticado."
            )

        if target_company and str(block.company_id) != str(target_company):
            raise serializers.ValidationError(
                "O bloco de permissoes selecionado nao pertence a empresa informada."
            )

        return block

    def validate_client(self, value):
        return self._validate_client_scope(value)

    def validate_granted_permissions(self, value):
        return normalize_permission_map(value)

    def validate_denied_permissions(self, value):
        return normalize_permission_map(value)

    def validate(self, attrs):
        raw_role = attrs.get("role") or getattr(self.instance, "role", None)
        role = normalize_user_role(raw_role)
        organization = attrs.get("client", getattr(self.instance, "client", None))
        organization_links = attrs.get("organization_links")
        permission_blocks = attrs.get("permission_blocks")
        legacy_permissions = attrs.get("permissions_json")
        granted_permissions = attrs.get("granted_permissions")

        if role:
            attrs["role"] = role

        if not organization and organization_links:
            first_link = next((link for link in organization_links if link.get("organization")), None)
            if first_link:
                attrs["client"] = first_link["organization"]
                organization = attrs["client"]

        if role == "CLIENT" and not organization:
            raise serializers.ValidationError(
                {"client": "Usuarios do tipo cliente precisam estar vinculados a uma organizacao."}
            )

        if organization_links:
            for link in organization_links:
                self._validate_client_scope(link["organization"])

        if permission_blocks is not None:
            for block in permission_blocks:
                self._validate_permission_block_scope(block)

        if granted_permissions is None and legacy_permissions:
            attrs["granted_permissions"] = permission_map_from_keys(legacy_permissions)
        elif granted_permissions is not None:
            attrs["granted_permissions"] = normalize_permission_map(granted_permissions)

        if "denied_permissions" in attrs:
            attrs["denied_permissions"] = normalize_permission_map(attrs.get("denied_permissions"))

        return attrs

    def _sync_organization_links(self, user, links_data):
        request_company = self._get_request_company()
        current_company = user.company or request_company
        retained_org_ids = set()

        if links_data is not None:
            for link_data in links_data:
                organization = link_data["organization"]
                retained_org_ids.add(str(organization.id))
                UserOrganization.objects.update_or_create(
                    user=user,
                    organization=organization,
                    defaults={
                        "company": current_company or organization.company,
                        "role": link_data.get("role", ""),
                        "active": link_data.get("active", True),
                    },
                )

            UserOrganization.objects.filter(user=user).exclude(
                organization_id__in=retained_org_ids
            ).delete()

        primary_organization = user.client
        if primary_organization:
            UserOrganization.objects.update_or_create(
                user=user,
                organization=primary_organization,
                defaults={
                    "company": current_company or primary_organization.company,
                    "role": "PRIMARY",
                    "active": True,
                },
            )

    def _sync_permission_blocks(self, user, blocks):
        if blocks is None:
            return

        user.permission_blocks.set(blocks)

    def _sync_legacy_permissions(self, user):
        next_permissions = flatten_granted_permissions(getattr(user, "granted_permissions", {}))
        user.permissions_json = next_permissions
        user.save(update_fields=["permissions_json", "updated_at"])

    def create(self, validated_data):
        links_data = validated_data.pop("organization_links", None)
        permission_blocks = validated_data.pop("permission_blocks", None)
        password = validated_data.pop("password", None) or "123456"
        request_company = self._get_request_company()
        selected_client = validated_data.get("client")
        user = User(**validated_data)

        if not user.username:
            user.username = user.email
        if not user.company:
            user.company = request_company or getattr(selected_client, "company", None)

        user.set_password(password)
        user.save()
        self._sync_organization_links(user, links_data)
        self._sync_permission_blocks(user, permission_blocks)
        self._sync_legacy_permissions(user)
        return user

    def update(self, instance, validated_data):
        links_data = validated_data.pop("organization_links", None)
        permission_blocks = validated_data.pop("permission_blocks", None)
        password = validated_data.pop("password", None)

        for key, value in validated_data.items():
            setattr(instance, key, value)

        if password:
            instance.set_password(password)

        instance.save()
        self._sync_organization_links(instance, links_data)
        self._sync_permission_blocks(instance, permission_blocks)
        self._sync_legacy_permissions(instance)
        return instance
