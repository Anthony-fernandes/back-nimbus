from django.db import models
from common.models import BaseModel
from apps.users.models import User
from apps.companies.models import Company


class Team(BaseModel):
    TIPO_CHOICES = [
        ("equipe", "Equipe de execução (Sprint/Projeto)"),
        ("grupo", "Grupo organizacional (Atribuição/Permissão)"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="teams")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    leader = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="led_teams")
    status = models.CharField(max_length=50, default="Ativa", choices=[
        ("Ativa", "Ativa"),
        ("Inativa", "Inativa"),
        ("Arquivada", "Arquivada"),
    ])
    color = models.CharField(max_length=20, blank=True, default="#6366f1")
    icon = models.CharField(max_length=50, blank=True, default="")
    default_capacity = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    settings = models.JSONField(default=dict, blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default="equipe")
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subgroups",
    )
    clients = models.ManyToManyField(
        "clients.Client",
        blank=True,
        related_name="assigned_teams",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class TeamMember(BaseModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="team_members")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="team_memberships")
    role = models.CharField(max_length=100, blank=True, default="")
    default_hours_per_day = models.DecimalField(max_digits=4, decimal_places=2, default=8)
    default_capacity = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    class Meta:
        unique_together = ("team", "user")
        ordering = ["user__first_name", "user__last_name"]

    def __str__(self):
        return f"{self.team.name} — {self.user}"
