from rest_framework import serializers
from .models import Webhook, WebhookDelivery


class WebhookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Webhook
        fields = ["id", "name", "url", "secret", "events", "active", "last_triggered_at", "last_status_code", "created_at"]
        read_only_fields = ["id", "last_triggered_at", "last_status_code", "created_at"]
        extra_kwargs = {"secret": {"write_only": True}}


class WebhookDeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookDelivery
        fields = ["id", "event", "status_code", "success", "error", "created_at"]
        read_only_fields = ["id", "event", "status_code", "success", "error", "created_at"]
