from django.db import models

from apps.companies.models import Company
from apps.users.models import User
from common.models import BaseModel


class Notification(BaseModel):
    """Mensagem da caixa de entrada interna de um usuario."""

    CATEGORY_CHOICES = [
        ("Chamados", "Chamados"),
        ("Aprovacoes", "Aprovacoes"),
        ("Projetos", "Projetos"),
        ("Atividades", "Atividades"),
        ("Comentarios", "Comentarios"),
        ("Sistema", "Sistema"),
        ("Forum", "Forum"),
        ("Chat", "Chat"),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_notifications",
    )
    actor_name = models.CharField(max_length=255, blank=True, default="")
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default="Sistema")
    event = models.CharField(max_length=80, blank=True, default="")
    origin = models.CharField(max_length=80, blank=True, default="")
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True, default="")
    link = models.CharField(max_length=255, blank=True, default="")
    entity_type = models.CharField(max_length=80, blank=True, default="")
    entity_id = models.CharField(max_length=120, blank=True, default="")
    is_read = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    email_sent = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.recipient_id} - {self.title}"


class NotificationPreference(BaseModel):
    """Preferencias de recebimento de notificacoes por usuario."""

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notification_preferences",
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="notification_preference",
    )
    email_enabled = models.BooleanField(default=True)
    inbox_enabled = models.BooleanField(default=True)
    disabled_events = models.JSONField(default=list, blank=True)
    email_disabled_events = models.JSONField(default=list, blank=True)
    digest_frequency = models.CharField(max_length=20, blank=True, default="instant")

    class Meta:
        ordering = ["user__username"]

    def __str__(self):
        return f"Preferencias de {self.user_id}"


class EmailTemplate(BaseModel):
    company = models.ForeignKey("companies.Company", on_delete=models.CASCADE, related_name="email_templates")
    event = models.CharField(max_length=100)
    subject = models.CharField(max_length=300)
    body = models.TextField()
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = [["company", "event"]]

    def __str__(self):
        return f"{self.company_id} - {self.event}"
