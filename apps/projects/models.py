from django.db import models

from apps.clients.models import Client
from apps.companies.models import Company
from apps.users.models import User
from common.models import BaseModel


class Project(BaseModel):
    STATUS_CHOICES = [
        ("Planejado", "Planejado"),
        ("Em andamento", "Em andamento"),
        ("Em risco", "Em risco"),
        ("Pausado", "Pausado"),
        ("Concluido", "Concluido"),
    ]

    HEALTH_CHOICES = [
        ("on_track", "No prazo"),
        ("at_risk", "Em risco"),
        ("delayed", "Atrasado"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="projects")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="projects")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default="Planejado")
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_projects",
    )
    contact_principal = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contact_projects",
    )
    team = models.ManyToManyField(User, blank=True, related_name="projects")
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    real_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    progress = models.IntegerField(default=0)
    start_at = models.DateField(null=True, blank=True)
    due_at = models.DateField(null=True, blank=True)
    tags = models.JSONField(default=list, blank=True)
    checklist = models.JSONField(default=list, blank=True)
    health = models.CharField(max_length=20, choices=HEALTH_CHOICES, default="on_track")

    class Meta:
        ordering = ["-created_at"]

    def compute_health(self):
        """Calcula saúde automaticamente baseado em progresso vs tempo decorrido."""
        import datetime
        if self.status in ("Concluido", "Cancelado"):
            return "on_track"
        if not self.start_at or not self.due_at:
            return "on_track"
        today = datetime.date.today()
        total_days = (self.due_at - self.start_at).days
        if total_days <= 0:
            return "delayed" if today > self.due_at else "on_track"
        elapsed_days = (today - self.start_at).days
        elapsed_pct = max(0, elapsed_days / total_days * 100)
        if today > self.due_at:
            return "delayed"
        if elapsed_pct > self.progress + 15:
            return "delayed"
        if elapsed_pct > self.progress + 5:
            return "at_risk"
        return "on_track"

    def save(self, *args, **kwargs):
        self.health = self.compute_health()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProjectMember(BaseModel):
    ROLE_CHOICES = [
        ("LIDER", "Lider"),
        ("DESENVOLVEDOR", "Desenvolvedor"),
        ("ANALISTA", "Analista"),
        ("TESTER", "Tester"),
        ("OBSERVADOR", "Observador"),
        ("CLIENTE_APROVADOR", "Cliente aprovador"),
        ("PRODUCT_OWNER", "Product owner"),
        ("SCRUM_MASTER", "Scrum master"),
        ("SUPORTE", "Suporte"),
        ("OUTRO", "Outro"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="project_members")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="member_links")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="project_links")
    role = models.CharField(max_length=40, choices=ROLE_CHOICES, default="DESENVOLVEDOR")
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["project__name", "user__username"]
        unique_together = ("project", "user")

    def __str__(self):
        return f"{self.project.name} - {self.user.full_name_or_username}"


class ProjectCustomField(BaseModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="project_custom_fields")
    name = models.CharField(max_length=100)
    label = models.CharField(max_length=150)
    field_type = models.CharField(max_length=30, choices=[
        ("text", "Texto"), ("number", "Número"), ("date", "Data"),
        ("select", "Seleção"), ("boolean", "Sim/Não"),
    ])
    options = models.JSONField(default=list, blank=True)
    required = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.label


class ProjectCustomValue(BaseModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="custom_values")
    field = models.ForeignKey(ProjectCustomField, on_delete=models.CASCADE)
    value = models.TextField(blank=True, default="")

    class Meta:
        unique_together = [("project", "field")]

    def __str__(self):
        return f"{self.project_id} - {self.field.name}"
