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
        ("Aguardando Aprovacao", "Aguardando Aprovacao"),
        ("Aprovado", "Aprovado"),
        ("Reprovado", "Reprovado"),
        ("Ajustes Solicitados", "Ajustes Solicitados"),
        ("Triagem", "Triagem"),
        ("Backlog", "Backlog"),
        ("Aguardando atendimento", "Aguardando atendimento"),
        ("Em atendimento", "Em atendimento"),
        ("Aguardando cliente", "Aguardando cliente"),
        ("Validacao", "Validacao"),
        ("Pausado", "Pausado"),
        ("Cancelado", "Cancelado"),
        ("Finalizado", "Finalizado"),
        ("Convertido em Atividade de Projeto", "Convertido em Atividade de Projeto"),
    ]

    APPROVAL_STATUS = [
        ("Nao requerido", "Nao requerido"),
        ("Aguardando Aprovacao", "Aguardando Aprovacao"),
        ("Aprovado", "Aprovado"),
        ("Reprovado", "Reprovado"),
        ("Ajustes Solicitados", "Ajustes Solicitados"),
    ]

    APPROVAL_ROUTE = [
        ("NONE", "Sem aprovacao"),
        ("APPROVER", "Aprovador vinculado"),
        ("SERVICE_DESK", "Equipe de chamados"),
        ("AUTO", "Automatica por cargo"),
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

    # Fluxo de aprovacao
    approval_status = models.CharField(max_length=40, choices=APPROVAL_STATUS, default="Nao requerido")
    approval_route = models.CharField(max_length=20, choices=APPROVAL_ROUTE, default="NONE")
    approval_reason = models.TextField(blank=True, default="")
    current_approver = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets_awaiting_approval",
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_tickets",
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    # Conversao em atividade de projeto
    converted_activity = models.ForeignKey(
        "activities.Activity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="source_tickets",
    )
    converted_at = models.DateTimeField(null=True, blank=True)
    conversion_reason = models.CharField(max_length=255, blank=True, default="")

    # Avaliacao do chamado pelo solicitante
    rating = models.IntegerField(null=True, blank=True)  # 1-5
    rating_comment = models.TextField(blank=True)
    rated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.code:
            last = Ticket.objects.count() + 1
            self.code = f"NIM-{2000 + last}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code or self.title


class TicketApproval(BaseModel):
    """Historico de cada decisao de aprovacao de um chamado."""

    DECISION = [
        ("PENDENTE", "Pendente"),
        ("APROVADO", "Aprovado"),
        ("REPROVADO", "Reprovado"),
        ("AJUSTES", "Ajustes solicitados"),
    ]
    ROUTE = Ticket.APPROVAL_ROUTE

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="ticket_approvals")
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="approvals")
    approver = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ticket_approval_decisions",
    )
    approver_name = models.CharField(max_length=255, blank=True, default="")
    decision = models.CharField(max_length=20, choices=DECISION, default="PENDENTE")
    route = models.CharField(max_length=20, choices=ROUTE, default="APPROVER")
    comment = models.TextField(blank=True, default="")
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.ticket_id} - {self.decision}"


class TicketComment(BaseModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="ticket_comments")
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ticket_comments",
    )
    author_name = models.CharField(max_length=255, blank=True, default="")
    body = models.TextField(blank=True, default="")
    is_internal = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.ticket_id} - {self.author_name}"


class TicketAttachment(BaseModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="ticket_attachments")
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="attachments")
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ticket_attachments",
    )
    name = models.CharField(max_length=255)
    url = models.CharField(max_length=500, blank=True, default="")
    content_type = models.CharField(max_length=120, blank=True, default="")
    size = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


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


class TicketTemplate(BaseModel):
    """Pre-filled ticket template for common request types."""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="ticket_templates")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    # Pre-filled fields
    title = models.CharField(max_length=300, blank=True, default="")
    type = models.CharField(max_length=80, blank=True, default="")
    priority = models.CharField(max_length=30, blank=True, default="")
    category = models.ForeignKey("TicketCategory", on_delete=models.SET_NULL, null=True, blank=True, related_name="templates")
    description_template = models.TextField(blank=True, default="", help_text="Template de descricao do chamado")
    tags = models.JSONField(default=list, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class SLAPolicy(BaseModel):
    """Per-company SLA policy: maps priority+category to a response time."""
    PRIORITY_CHOICES = [("Critica", "Critica"), ("Alta", "Alta"), ("Media", "Media"), ("Baixa", "Baixa"), ("", "Qualquer")]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="sla_policies")
    name = models.CharField(max_length=200)
    priority = models.CharField(max_length=30, choices=PRIORITY_CHOICES, blank=True, default="")
    category = models.CharField(max_length=80, blank=True, default="")
    response_time = models.CharField(max_length=20, default="8h", help_text="Ex: 2h, 1d, 30m")
    priority_weight = models.IntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-priority_weight", "name"]

    def __str__(self):
        return f"{self.name} ({self.response_time})"


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
