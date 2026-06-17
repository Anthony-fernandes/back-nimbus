from rest_framework import serializers
from .models import Dashboard, DashboardVersion


class DashboardVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardVersion
        fields = [
            "id",
            "version_number",
            "config_snapshot",
            "created_by",
            "is_published",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class DashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dashboard
        fields = [
            "id",
            "name",
            "description",
            "type",
            "status",
            "is_active",
            "components_json",
            "filters_json",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
