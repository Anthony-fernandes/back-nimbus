from rest_framework import serializers

from .models import Client


class ClientSerializer(serializers.ModelSerializer):
    tickets = serializers.SerializerMethodField()
    projects = serializers.SerializerMethodField()
    type = serializers.CharField(source="organization_type", read_only=True)
    organization_parent_id = serializers.CharField(source="parent_id", read_only=True)
    organization_parent_name = serializers.CharField(source="parent.name", read_only=True)

    class Meta:
        model = Client
        fields = [
            "id",
            "company",
            "name",
            "organization_type",
            "type",
            "document",
            "email",
            "phone",
            "address",
            "sector",
            "contact_name",
            "active",
            "parent",
            "organization_parent_id",
            "organization_parent_name",
            "plan",
            "mrr",
            "health",
            "notes",
            "status",
            "tickets",
            "projects",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {"company": {"required": False, "read_only": True}}

    def get_tickets(self, obj):
        return obj.tickets.count()

    def get_projects(self, obj):
        return obj.projects.count()

    def validate_parent(self, value):
        if value is None:
            return value

        request = self.context.get("request")
        request_company = getattr(getattr(request, "user", None), "company", None)
        target_company = request_company or getattr(self.instance, "company", None)

        if target_company and value.company_id != target_company.id:
            raise serializers.ValidationError(
                "Selecione uma organizacao pai da mesma empresa do usuario autenticado."
            )

        return value
