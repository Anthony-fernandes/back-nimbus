import secrets
import threading

from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.viewsets import CompanyScopedModelViewSet
from .models import Webhook, WebhookDelivery, WEBHOOK_EVENTS
from .serializers import WebhookSerializer, WebhookDeliverySerializer


class WebhookViewSet(CompanyScopedModelViewSet):
    serializer_class = WebhookSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Webhook.objects.filter(company=self.request.user.company, deleted_at__isnull=True)

    def perform_create(self, serializer):
        if not serializer.validated_data.get('secret'):
            serializer.save(company=self.request.user.company, secret=secrets.token_hex(32))
        else:
            serializer.save(company=self.request.user.company)

    @action(detail=False, methods=["get"], url_path="available-events")
    def available_events(self, request):
        return Response([{"event": k, "label": v} for k, v in WEBHOOK_EVENTS])

    @action(detail=True, methods=["get"], url_path="deliveries")
    def deliveries(self, request, pk=None):
        webhook = self.get_object()
        deliveries = WebhookDelivery.objects.filter(webhook=webhook).order_by("-created_at")[:50]
        return Response(WebhookDeliverySerializer(deliveries, many=True).data)

    @action(detail=True, methods=["post"], url_path="test")
    def test(self, request, pk=None):
        webhook = self.get_object()
        from .services import _deliver
        t = threading.Thread(target=_deliver, args=(webhook, "test", {"message": "Teste de webhook Nimbus"}), daemon=True)
        t.start()
        return Response({"detail": "Teste enviado. Verifique o histórico de entregas."})
