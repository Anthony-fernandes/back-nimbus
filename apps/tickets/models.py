from django.db import models

from apps.clients.models import Client
from apps.companies.models import Company
from apps.projects.models import Project
from apps.users.models import User
from common.models import BaseModel


class Ticket(BaseModel):
    PRIORITY = [
        ("Critica", "Critica"),
        ("Alta", "Alta"),
        ("Media", "Media"),
        ("Baixa", "Baixa"),
    ]
    STATUS = [
        ("Aberto", "Aberto"),
        ("Triagem", "Triagem"),
        ("Aguardando atendimento", "Aguardando atendimento"),
        ("Em atendimento", "Em atendimento"),
        ("Aguardando cliente", "Aguardando cliente"),
        ("Validacao", "Validacao"),
        ("Pausado", "Pausado"),
        ("Cancelado", "Cancelado"),
        ("Finalizado", "Finalizado"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="tickets")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="tickets")
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name="tickets")
    sprint = models.ForeignKey(
        "sprints.Sprint",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets",
    )
    code = models.CharField(max_length=30, unique=True, blank=True, default="")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    requester = models.CharField(max_length=255, blank=True, default="")
    requester_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requested_tickets",
    )
    contact_responsible = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contact_tickets",
    )
    contact_responsible_name = models.CharField(max_length=255, blank=True, default="")
    contact_responsible_phone = models.CharField(max_length=40, blank=True, default="")
    responsible_technician = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_tickets",
    )
    category = models.CharField(max_length=80, blank=True, default="Atendimento")
    type = models.CharField(max_length=80, blank=True, default="Incidente")
    priority = models.CharField(max_length=30, choices=PRIORITY, default="Media")
    impact = models.CharField(max_length=30, default="Medio")
    urgency = models.CharField(max_length=30, default="Media")
    status = models.CharField(max_length=40, choices=STATUS, default="Aberto")
    technicians = models.ManyToManyField(User, blank=True, related_name="tickets")
    team = models.CharField(max_length=120, blank=True, default="")
    sla = models.CharField(max_length=30, blank=True, default="8h")
    sla_due_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateField(null=True, blank=True)
    due_at = models.DateField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    est_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    done_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    tags = models.JSONField(default=list, blank=True)
    checklist = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.code:
            last = Ticket.objects.count() + 1
            self.code = f"NIM-{2000 + last}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code or self.title


class TicketCategory(BaseModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="ticket_categories")
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, default="")
    active = models.BooleanField(default=True)
    sla = models.CharField(max_length=30, blank=True, default="")
    sla_unit = models.CharField(max_length=20, blank=True, default="")
    approval_required = models.BooleanField(default=False)
    default_type = models.CharField(max_length=80, blank=True, default="")
    default_priority = models.CharField(max_length=30, blank=True, default="")
    default_impact = models.CharField(max_length=30, blank=True, default="")
    default_team = models.CharField(max_length=120, blank=True, default="")
    allow_project_activity = models.BooleanField(default=True)
    requires_technical_categorization = models.BooleanField(default=False)
    requires_client_validation = models.BooleanField(default=False)
    color = models.CharField(max_length=20, blank=True, default="")
    icon = models.CharField(max_length=60, blank=True, default="")

    class Meta:
        ordering = ["name"]
        unique_together = ("company", "name")

    def __str__(self):
        return self.name


class TicketWorkflowStatus(BaseModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="ticket_workflow_statuses")
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140)
    description = models.TextField(blank=True, default="")
    color = models.CharField(max_length=20, blank=True, default="")
    active = models.BooleanField(default=True)
    pauses_sla = models.BooleanField(default=False)
    is_final = models.BooleanField(default=False)
    allows_resume = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=999)
    origin_statuses = models.JSONField(default=list, blank=True)
    next_statuses = models.JSONField(default=list, blank=True)
    system = models.BooleanField(default=False)

    class Meta:
        ordering = ["order", "name"]
        unique_together = ("company", "slug")

    def __str__(self):
        return self.name
