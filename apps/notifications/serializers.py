from rest_framework import serializers

from .models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "company",
            "recipient",
            "actor",
            "actor_name",
            "category",
            "event",
            "origin",
            "title",
            "message",
            "link",
            "entity_type",
            "entity_id",
            "is_read",
            "is_favorite",
            "is_archived",
            "read_at",
            "email_sent",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "company",
            "recipient",
            "actor",
            "actor_name",
            "category",
            "event",
            "origin",
            "title",
            "message",
            "link",
            "entity_type",
            "entity_id",
            "read_at",
            "email_sent",
            "metadata",
            "created_at",
            "updated_at",
        ]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            "id",
            "company",
            "user",
            "email_enabled",
            "inbox_enabled",
            "disabled_events",
            "email_disabled_events",
            "digest_frequency",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "company", "user", "created_at", "updated_at"]
