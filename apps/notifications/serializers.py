from rest_framework import serializers

from .models import EmailTemplate, Notification, NotificationPreference


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


class EmailTemplateSerializer(serializers.ModelSerializer):
    event_label = serializers.SerializerMethodField()

    class Meta:
        model = EmailTemplate
        fields = ["id", "event", "event_label", "subject", "body", "active", "created_at", "updated_at"]
        read_only_fields = ["id", "event_label", "created_at", "updated_at"]

    def get_event_label(self, obj):
        from apps.notifications.email_templates import EVENT_LABEL
        return EVENT_LABEL.get(obj.event, obj.event)
