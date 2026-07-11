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
        ("Aguardando atendimento", "Aguardando atendimento"),
        ("Em atendimento", "Em atendimento"),
        ("Aguardando cliente", "Aguardando cliente"),
        ("Validacao", "Validacao"),
        ("Pausado", "Pausado"),
        ("Cancelado", "Cancelado"),
        ("Finalizado", "Finalizado"),
        ("Convertido em Atividade de Projeto", "Convertido em Atividade de Projeto"),
    ]

    ITIL_TYPES = [
        ("Incidente", "Incidente"),
        ("Requisição", "Requisição"),
        ("Problema", "Problema"),
        ("Mudança", "Mudança"),
        ("Outro", "Outro"),
    ]

    IMPACT_CHOICES = [
        ("Alto", "Alto"),
        ("Médio", "Médio"),
        ("Baixo", "Baixo"),
    ]

    URGENCY_CHOICES = [
        ("Alta", "Alta"),
        ("Média", "Média"),
        ("Baixa", "Baixa"),
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

    SOURCE_CHOICES = [
        ("portal", "Portal"),
        ("email", "E-mail"),
        ("chat", "Chat"),
        ("telefone", "Telefone"),
        ("api", "API"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="tickets")
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True, related_name="tickets")
    department = models.ForeignKey(
        "users.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets",
    )
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="portal", blank=True)
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
    subcategory = models.CharField(max_length=120, blank=True, default="")
    # Serviço/módulo afetado informado na abertura (Portal do Cliente)
    affected_service = models.CharField(max_length=120, blank=True, default="")
    preferred_contact_time = models.CharField(max_length=60, blank=True, default="")
    preferred_contact_channel = models.CharField(max_length=30, blank=True, default="")
    type = models.CharField(max_length=80, choices=ITIL_TYPES, default="Incidente")
    priority = models.CharField(max_length=30, choices=PRIORITY, default="Media")
    impact = models.CharField(max_length=30, choices=IMPACT_CHOICES, default="Médio")
    urgency = models.CharField(max_length=30, choices=URGENCY_CHOICES, default="Média")
    status = models.CharField(max_length=40, choices=STATUS, default="Aberto")
    technicians = models.ManyToManyField(User, blank=True, related_name="tickets")
    # Campo legado (texto livre). Preferir team_ref (FK) daqui em diante.
    team = models.CharField(max_length=120, blank=True, default="")
    # Equipe canônica: FK para teams.Team (fonte única do conceito de equipe).
    team_ref = models.ForeignKey(
        "teams.Team",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets",
    )
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
    csat_sent_at = models.DateTimeField(null=True, blank=True)

    # Reabertura controlada
    reopen_count = models.PositiveIntegerField(default=0)
    last_reopened_at = models.DateTimeField(null=True, blank=True)
    reopen_deadline = models.DateTimeField(null=True, blank=True)  # prazo limite para reabrir

    # Resolução documentada (fluxo WorkItem)
    RESOLUTION_TYPES = [
        ("Resolvido", "Resolvido"),
        ("Resolvido parcialmente", "Resolvido parcialmente"),
        ("Não reproduzido", "Não reproduzido"),
        ("Duplicado", "Duplicado"),
        ("Encaminhado", "Encaminhado"),
        ("Cancelado", "Cancelado"),
    ]
    resolution_type = models.CharField(max_length=60, blank=True, default="")
    resolution_notes = models.TextField(blank=True, default="")
    resolved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="resolved_tickets"
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    # Matrix Impacto × Urgência → Prioridade
    _PRIORITY_MATRIX = {
        ("Alto",  "Alta"):  "Critica",
        ("Alto",  "Média"): "Alta",
        ("Alto",  "Baixa"): "Alta",
        ("Médio", "Alta"):  "Alta",
        ("Médio", "Média"): "Media",
        ("Médio", "Baixa"): "Baixa",
        ("Baixo", "Alta"):  "Media",
        ("Baixo", "Média"): "Baixa",
        ("Baixo", "Baixa"): "Baixa",
    }

    def compute_priority_from_matrix(self):
        return self._PRIORITY_MATRIX.get((self.impact, self.urgency))

    def save(self, *args, **kwargs):
        if not self.code:
            from django.db import transaction, connection
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT COALESCE(MAX(CAST(REPLACE(code, 'NIM-', '') AS INTEGER)), 1000) FROM tickets_ticket WHERE code LIKE 'NIM-%'"
                    )
                    row = cursor.fetchone()
                seq = (row[0] if row and row[0] else 1000) + 1
                self.code = f"NIM-{seq}"
        # Auto-calculate priority from impact × urgency if both set
        computed = self.compute_priority_from_matrix()
        if computed:
            self.priority = computed
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
    # public: cliente vê | internal: só equipe | technical: só técnicos/gestores | resolution: registro de finalização
    NOTE_TYPES = [
        ("public", "Resposta pública"),
        ("internal", "Comentário interno"),
        ("technical", "Nota técnica"),
        ("resolution", "Resolução"),
    ]
    note_type = models.CharField(max_length=20, choices=NOTE_TYPES, blank=True, default="")

    class Meta:
        ordering = ["created_at"]

    def save(self, *args, **kwargs):
        if not self.note_type:
            self.note_type = "internal" if self.is_internal else "public"
        self.is_internal = self.note_type != "public"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_id} - {self.author_name}"


class TicketTimeEntry(BaseModel):
    """Apontamento de horas por técnico em um chamado (espelha ActivityTimeEntry)."""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="ticket_time_entries")
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="time_entries")
    collaborator = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="ticket_time_entries"
    )
    collaborator_name = models.CharField(max_length=255, blank=True, default="")
    date = models.DateField()
    hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    work_description = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.ticket_id} - {self.date}"


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
    # Subcategorias desta categoria (lista de strings) — usadas no Portal do Cliente
    subcategories = models.JSONField(default=list, blank=True)
    # Regras próprias da categoria na abertura pelo Portal do Cliente
    subcategory_required = models.BooleanField(default=False)
    attachment_required = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]
        unique_together = ("company", "name")

    def __str__(self):
        return self.name


# Campos configuráveis do formulário de abertura no Portal do Cliente.
# Cada chave define {visible, required}; o backend valida com base nisso.
DEFAULT_PORTAL_FORM_FIELDS = {
    "title": {"visible": True, "required": True},
    "description": {"visible": True, "required": True},
    "category": {"visible": True, "required": False},
    "subcategory": {"visible": True, "required": False},
    "department": {"visible": True, "required": False},
    "request_type": {"visible": True, "required": False},
    "affected_service": {"visible": False, "required": False},
    "urgency": {"visible": True, "required": True},
    "impact": {"visible": True, "required": True},
    "contact_phone": {"visible": True, "required": False},
    "preferred_contact_time": {"visible": False, "required": False},
    "preferred_contact_channel": {"visible": False, "required": False},
    "attachments": {"visible": True, "required": False},
}


class TicketPortalFormConfig(BaseModel):
    """Configuração (por empresa) do formulário de abertura do Portal do Cliente."""

    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name="portal_form_config")
    fields = models.JSONField(default=dict, blank=True)

    def resolved_fields(self) -> dict:
        merged = {key: dict(value) for key, value in DEFAULT_PORTAL_FORM_FIELDS.items()}
        for key, value in (self.fields or {}).items():
            if key in merged and isinstance(value, dict):
                merged[key].update({k: bool(v) for k, v in value.items() if k in ("visible", "required")})
        return merged

    @classmethod
    def resolved_for_company(cls, company) -> dict:
        config = cls.objects.filter(company=company, deleted_at__isnull=True).first()
        if config:
            return config.resolved_fields()
        return {key: dict(value) for key, value in DEFAULT_PORTAL_FORM_FIELDS.items()}


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


class TicketCustomField(BaseModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="custom_fields")
    name = models.CharField(max_length=100)
    label = models.CharField(max_length=150)
    field_type = models.CharField(max_length=30, choices=[
        ("text", "Texto"), ("number", "Número"), ("date", "Data"),
        ("select", "Seleção"), ("boolean", "Sim/Não"),
    ])
    options = models.JSONField(default=list, blank=True)  # for select type
    required = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    # Campo extra vinculado a uma categoria (None = vale para todas)
    category = models.ForeignKey(
        "TicketCategory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="custom_fields",
    )
    # Exibido (e exigido, se required) no formulário do Portal do Cliente
    visible_to_client = models.BooleanField(default=False)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.label


class TicketCustomValue(BaseModel):
    ticket = models.ForeignKey("Ticket", on_delete=models.CASCADE, related_name="custom_values")
    field = models.ForeignKey(TicketCustomField, on_delete=models.CASCADE)
    value = models.TextField(blank=True, default="")

    class Meta:
        unique_together = [("ticket", "field")]

    def __str__(self):
        return f"{self.ticket_id} - {self.field.name}"


class SLAPolicy(BaseModel):
    """Per-company SLA policy: maps priority+category to a response time. Pode ser por cliente."""
    PRIORITY_CHOICES = [("Critica", "Critica"), ("Alta", "Alta"), ("Media", "Media"), ("Baixa", "Baixa"), ("", "Qualquer")]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="sla_policies")
    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sla_policies",
    )
    name = models.CharField(max_length=200)
    priority = models.CharField(max_length=30, choices=PRIORITY_CHOICES, blank=True, default="")
    category = models.CharField(max_length=80, blank=True, default="")
    subcategory = models.CharField(max_length=120, blank=True, default="")
    response_time = models.CharField(max_length=20, default="8h", help_text="Ex: 2h, 1d, 30m")
    priority_weight = models.IntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-priority_weight", "name"]

    def __str__(self):
        return f"{self.name} ({self.response_time})"


class TicketStatusHistory(BaseModel):
    """Registro imutável de cada transição de status de um chamado."""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="ticket_status_histories")
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="status_history")
    changed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="ticket_status_changes"
    )
    changed_by_name = models.CharField(max_length=255, blank=True, default="")
    status_from = models.CharField(max_length=60, blank=True, default="")
    status_to = models.CharField(max_length=60)
    reason = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.ticket_id}: {self.status_from} → {self.status_to}"


class TicketRelation(BaseModel):
    """Vínculo entre dois chamados (duplicado, relacionado, bloqueia)."""
    RELATION_TYPES = [
        ("duplicado", "Duplicado de"),
        ("relacionado", "Relacionado a"),
        ("bloqueia", "Bloqueia"),
        ("bloqueado_por", "Bloqueado por"),
        ("subchamado", "Subchamado de"),
    ]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="ticket_relations")
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="relations")
    related_ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="related_by")
    # Subchamado que trava a finalização do chamado pai enquanto estiver aberto
    blocks_parent = models.BooleanField(default=False)
    relation_type = models.CharField(max_length=30, choices=RELATION_TYPES, default="relacionado")
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_ticket_relations"
    )

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("ticket", "related_ticket", "relation_type")

    def __str__(self):
        return f"{self.ticket_id} {self.relation_type} {self.related_ticket_id}"


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

    # Regras de negócio configuráveis por status (workflow dinâmico)
    ITEM_TYPES = [("ticket", "Chamado"), ("activity", "Atividade")]
    PHASES = [
        ("entrada", "Entrada"),
        ("triagem", "Triagem"),
        ("aprovacao", "Aprovação"),
        ("atendimento", "Atendimento"),
        ("aguardando_terceiro", "Aguardando terceiro"),
        ("validacao", "Validação"),
        ("pausado", "Pausado"),
        ("final", "Final"),
    ]
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES, default="ticket")
    phase = models.CharField(max_length=30, choices=PHASES, blank=True, default="")
    # dicts allows_* / requires_* — vazios herdam os padrões da fase
    permissions = models.JSONField(default=dict, blank=True)
    requirements = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["order", "name"]
        unique_together = ("company", "slug")

    def __str__(self):
        return self.name

from apps.tickets.business_hours_models import BusinessHours, CompanyHoliday  # noqa: F401


class TicketAutomationRule(models.Model):
    TRIGGER_CHOICES = [
        ("on_create", "Ao criar chamado"),
        ("on_update", "Ao atualizar chamado"),
        ("on_status_change", "Ao mudar status"),
        ("on_sla_breach", "Ao violar SLA"),
    ]
    ACTION_CHOICES = [
        ("set_priority", "Definir prioridade"),
        ("set_status", "Definir status"),
        ("assign_technician", "Atribuir técnico"),
        ("assign_team", "Atribuir equipe"),
        ("add_tag", "Adicionar tag"),
        ("send_notification", "Enviar notificação"),
    ]
    company = models.ForeignKey("companies.Company", on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    trigger = models.CharField(max_length=40, choices=TRIGGER_CHOICES, default="on_create")
    conditions = models.JSONField(default=list, blank=True)
    action = models.CharField(max_length=40, choices=ACTION_CHOICES)
    action_value = models.CharField(max_length=500, blank=True)
    order = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "created_at"]


class InboundMailbox(models.Model):
    company = models.ForeignKey("companies.Company", on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    email_address = models.EmailField(unique=True)
    webhook_token = models.CharField(max_length=128, unique=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
