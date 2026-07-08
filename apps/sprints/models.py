from django.db import models
from common.models import BaseModel
from apps.companies.models import Company
from apps.projects.models import Project
from apps.users.models import User
from apps.teams.models import Team

PRIORITY_CHOICES = [
    ("Crítica", "Crítica"),
    ("Alta", "Alta"),
    ("Média", "Média"),
    ("Baixa", "Baixa"),
]

COMPLEXITY_CHOICES = [
    (1, "1"),
    (2, "2"),
    (3, "3"),
    (5, "5"),
    (8, "8"),
    (13, "13"),
    (21, "21"),
]


class Sprint(BaseModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="sprints")
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name="sprints")
    team = models.ForeignKey("teams.Team", on_delete=models.SET_NULL, null=True, blank=True, related_name="sprints")
    name = models.CharField(max_length=255)
    goal = models.TextField(blank=True, default="")
    lead = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="lead_sprints")
    status = models.CharField(max_length=40, default="Planejada")
    start_at = models.DateField(null=True, blank=True)
    end_at = models.DateField(null=True, blank=True)
    capacity = models.PositiveIntegerField(default=0)
    story_points = models.PositiveIntegerField(default=0)
    backlog = models.JSONField(default=list, blank=True)
    tasks = models.JSONField(default=list, blank=True)
    observations = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-start_at", "-created_at"]

    def __str__(self):
        return self.name

    @property
    def total_capacity(self):
        """Soma da capacidade de todos os participantes. Falls back to self.capacity if no participants."""
        participants = self.participants.all()
        if not participants.exists():
            return self.capacity
        return sum(p.capacity for p in participants)


class SprintRetrospective(BaseModel):
    """Registro da retrospectiva de uma sprint."""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="sprint_retrospectives")
    sprint = models.OneToOneField(Sprint, on_delete=models.CASCADE, related_name="retrospective")
    went_well = models.TextField(blank=True, default="")
    to_improve = models.TextField(blank=True, default="")
    action_items = models.JSONField(default=list, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_retrospectives")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Retrospectiva: {self.sprint}"


class SprintReview(BaseModel):
    """Registro do sprint review: planejado vs entregue."""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="sprint_reviews")
    sprint = models.OneToOneField(Sprint, on_delete=models.CASCADE, related_name="review")
    planned_points = models.PositiveIntegerField(default=0)
    delivered_points = models.PositiveIntegerField(default=0)
    planned_items = models.PositiveIntegerField(default=0)
    delivered_items = models.PositiveIntegerField(default=0)
    incomplete_activity_ids = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_sprint_reviews")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Review: {self.sprint}"


class SprintActivityPlan(BaseModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="sprint_activity_plans")
    sprint = models.ForeignKey(Sprint, on_delete=models.CASCADE, related_name="activity_plans")
    activity = models.ForeignKey("activities.Activity", on_delete=models.CASCADE, related_name="sprint_plans")
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name="sprint_activity_plans")
    responsible_ids = models.JSONField(default=list, blank=True)
    user_hours = models.JSONField(default=dict, blank=True)
    planned_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    story_points = models.PositiveIntegerField(null=True, blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="Média", blank=True)
    complexity = models.PositiveSmallIntegerField(choices=COMPLEXITY_CHOICES, null=True, blank=True)
    planned_start_date = models.DateField(null=True, blank=True)
    planned_end_date = models.DateField(null=True, blank=True)
    order = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["order", "created_at"]
        unique_together = ("sprint", "activity")

    def __str__(self):
        return f"{self.sprint_id} - {self.activity_id}"


class SprintTicketPlan(BaseModel):
    """Planejamento de chamado dentro de uma sprint (responsáveis + horas)."""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="sprint_ticket_plans")
    sprint = models.ForeignKey(Sprint, on_delete=models.CASCADE, related_name="ticket_plans")
    ticket = models.ForeignKey("tickets.Ticket", on_delete=models.CASCADE, related_name="sprint_plans")
    responsible_ids = models.JSONField(default=list, blank=True)
    user_hours = models.JSONField(default=dict, blank=True)
    planned_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    story_points = models.PositiveIntegerField(null=True, blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="Média", blank=True)
    complexity = models.PositiveSmallIntegerField(choices=COMPLEXITY_CHOICES, null=True, blank=True)
    planned_end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["created_at"]
        unique_together = ("sprint", "ticket")

    def __str__(self):
        return f"{self.sprint_id} - {self.ticket_id}"


class SprintParticipant(BaseModel):
    """Participante da sprint com sua capacidade individual."""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="sprint_participants")
    sprint = models.ForeignKey(Sprint, on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sprint_participations")
    hours_per_day = models.DecimalField(max_digits=4, decimal_places=1, default=8)
    working_days = models.PositiveIntegerField(default=0)
    availability_factor = models.DecimalField(max_digits=5, decimal_places=2, default=100)  # percentage 0-100
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name="sprint_participants")
    inclusion_mode = models.CharField(max_length=20, default="manual", choices=[
        ("team", "Equipe"),
        ("manual", "Manual"),
    ])
    story_points_planned = models.PositiveIntegerField(default=0)
    story_points_completed = models.PositiveIntegerField(default=0)
    hours_planned = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    hours_executed = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    is_available = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["created_at"]
        unique_together = ("sprint", "user")

    def __str__(self):
        return f"{self.sprint_id} - {self.user_id}"

    @property
    def capacity(self):
        """Horas disponíveis = hours_per_day * working_days * (availability_factor / 100)"""
        return float(self.hours_per_day) * int(self.working_days) * (float(self.availability_factor) / 100)
