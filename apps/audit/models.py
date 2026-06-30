from django.db import models

from apps.companies.models import Company
from apps.users.models import User
from common.models import BaseModel


class AuditLog(BaseModel):
    """Trilha de auditoria imutavel de toda acao critica da plataforma."""

    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    department = models.ForeignKey(
        "users.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    actor_name = models.CharField(max_length=255, blank=True, default="")
    action = models.CharField(max_length=120)
    entity_type = models.CharField(max_length=120, blank=True, default="")
    entity_id = models.CharField(max_length=120, blank=True, default="")
    entity_label = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    changes = models.JSONField(default=list, blank=True)
    origin = models.CharField(max_length=120, blank=True, default="")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} - {self.entity_label}"
