from common.models import BaseModel
from django.db import models


class Dashboard(BaseModel):
    company = models.ForeignKey("companies.Company", on_delete=models.CASCADE, related_name="dashboards")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=50, default="custom")
    status = models.CharField(max_length=30, default="draft")  # draft, active, inactive
    is_active = models.BooleanField(default=False)
    components_json = models.JSONField(default=list)
    filters_json = models.JSONField(default=list)
    created_by = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-created_at"]


class DashboardVersion(BaseModel):
    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name="versions")
    version_number = models.IntegerField(default=1)
    config_snapshot = models.JSONField(default=dict)
    created_by = models.CharField(max_length=200, blank=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
