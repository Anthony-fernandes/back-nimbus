from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    actor_display = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "company",
            "actor",
            "actor_name",
            "actor_display",
            "action",
            "entity_type",
            "entity_id",
            "entity_label",
            "description",
            "changes",
            "origin",
            "ip_address",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields

    def get_actor_display(self, obj):
        if obj.actor_name:
            return obj.actor_name
        if obj.actor_id:
            return obj.actor.full_name_or_username
        return "Sistema"
