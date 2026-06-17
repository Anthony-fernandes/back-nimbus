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

    class Meta:
        ordering = ["-created_at"]

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
