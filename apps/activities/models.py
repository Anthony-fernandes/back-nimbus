from django.db import models
from common.models import BaseModel
from apps.companies.models import Company
from apps.projects.models import Project
from apps.sprints.models import Sprint
from apps.tickets.models import Ticket
from apps.users.models import User

class Activity(BaseModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="activities")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    type = models.CharField(max_length=80, default="Tarefa")
    status = models.CharField(max_length=80, default="Backlog")
    priority = models.CharField(max_length=30, default="Média")
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="activities")
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name="activities")
    sprint = models.ForeignKey(Sprint, on_delete=models.SET_NULL, null=True, blank=True, related_name="activities")
    ticket = models.ForeignKey(Ticket, on_delete=models.SET_NULL, null=True, blank=True, related_name="activities")
    start_at = models.DateField(null=True, blank=True)
    due_at = models.DateField(null=True, blank=True)
    est_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    calculate_hourly_cost = models.BooleanField(default=False)
    story_points = models.PositiveIntegerField(default=0)
    tags = models.JSONField(default=list, blank=True)
    checklist = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class ActivityTag(BaseModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="activity_tags")
    name = models.CharField(max_length=120)
    color = models.CharField(max_length=20, blank=True, default="")
    description = models.TextField(blank=True, default="")
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        unique_together = ("company", "name")

    def __str__(self):
        return self.name


class ActivityTimeEntry(BaseModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="activity_time_entries")
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="time_entries")
    sprint = models.ForeignKey(Sprint, on_delete=models.SET_NULL, null=True, blank=True, related_name="time_entries")
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name="activity_time_entries")
    collaborator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="activity_time_entries")
    collaborator_name = models.CharField(max_length=255, blank=True, default="")
    date = models.DateField()
    hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    work_description = models.TextField(blank=True, default="")
    generated_cost_id = models.CharField(max_length=120, blank=True, default="")

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.activity_id} - {self.date}"
