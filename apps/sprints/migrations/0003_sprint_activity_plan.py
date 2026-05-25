# Generated manually for integration hardening.

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("activities", "0003_activity_integrations"),
        ("companies", "0001_initial"),
        ("projects", "0002_initial"),
        ("sprints", "0002_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SprintActivityPlan",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("responsible_ids", models.JSONField(blank=True, default=list)),
                ("planned_hours", models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ("story_points", models.PositiveIntegerField(blank=True, null=True)),
                ("planned_start_date", models.DateField(blank=True, null=True)),
                ("planned_end_date", models.DateField(blank=True, null=True)),
                ("order", models.PositiveIntegerField(blank=True, null=True)),
                ("notes", models.TextField(blank=True, default="")),
                ("activity", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sprint_plans", to="activities.activity")),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sprint_activity_plans", to="companies.company")),
                ("project", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="sprint_activity_plans", to="projects.project")),
                ("sprint", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="activity_plans", to="sprints.sprint")),
            ],
            options={
                "ordering": ["order", "created_at"],
                "unique_together": {("sprint", "activity")},
            },
        ),
    ]
