from django.db import models
from common.models import BaseModel

WEBHOOK_EVENTS = [
    ("ticket.created", "Chamado criado"),
    ("ticket.status_changed", "Status do chamado alterado"),
    ("ticket.approved", "Chamado aprovado"),
    ("ticket.rejected", "Chamado reprovado"),
    ("ticket.assigned", "Chamado atribuído"),
    ("ticket.rated", "Chamado avaliado"),
    ("ticket.sla_breached", "SLA violado"),
    ("activity.created", "Atividade criada"),
    ("activity.status_changed", "Status de atividade alterado"),
]


class Webhook(BaseModel):
    company = models.ForeignKey("companies.Company", on_delete=models.CASCADE, related_name="webhooks")
    name = models.CharField(max_length=200)
    url = models.URLField(max_length=500)
    secret = models.CharField(max_length=200, blank=True, help_text="HMAC secret for request signing")
    events = models.JSONField(default=list, help_text="List of event keys to listen to")
    active = models.BooleanField(default=True)
    last_triggered_at = models.DateTimeField(null=True, blank=True)
    last_status_code = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} → {self.url}"


class WebhookDelivery(BaseModel):
    webhook = models.ForeignKey(Webhook, on_delete=models.CASCADE, related_name="deliveries")
    event = models.CharField(max_length=100)
    payload = models.JSONField()
    status_code = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    success = models.BooleanField(default=False)
    error = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
