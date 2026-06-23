from django.db import models
from common.models import BaseModel
from apps.companies.models import Company
from apps.projects.models import Project
from apps.users.models import User

class Sprint(BaseModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="sprints")
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name="sprints")
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

    class Meta:
        ordering = ["-start_at", "-created_at"]

    def __str__(self):
        return self.name


class SprintRetrospective(BaseModel):
    """Registro da retrospectiva de uma sprint."""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="sprint_retrospectives")
    sprint = models.OneToOneField(Sprint, on_delete=models.CASCADE, related_name="retrospective")
    went_well = models.TextField(blank=True, default="")
    to_improve = models.TextField(blank=True, default="")
    action_items = models.JSONField(default=list, blank=True)  # [{text, owner, done}]
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
    planned_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    story_points = models.PositiveIntegerField(null=True, blank=True)
    planned_start_date = models.DateField(null=True, blank=True)
    planned_end_date = models.DateField(null=True, blank=True)
    order = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["order", "created_at"]
        unique_together = ("sprint", "activity")

    def __str__(self):
        return f"{self.sprint_id} - {self.activity_id}"
