# Generated manually for integration hardening.

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("activities", "0002_initial"),
        ("companies", "0001_initial"),
        ("projects", "0002_initial"),
        ("sprints", "0002_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="activity",
            name="calculate_hourly_cost",
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name="ActivityTag",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("name", models.CharField(max_length=120)),
                ("color", models.CharField(blank=True, default="", max_length=20)),
                ("description", models.TextField(blank=True, default="")),
                ("active", models.BooleanField(default=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="activity_tags", to="companies.company")),
            ],
            options={
                "ordering": ["name"],
                "unique_together": {("company", "name")},
            },
        ),
        migrations.CreateModel(
            name="ActivityTimeEntry",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("collaborator_name", models.CharField(blank=True, default="", max_length=255)),
                ("date", models.DateField()),
                ("hours", models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ("work_description", models.TextField(blank=True, default="")),
                ("generated_cost_id", models.CharField(blank=True, default="", max_length=120)),
                ("activity", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="time_entries", to="activities.activity")),
                ("collaborator", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="activity_time_entries", to=settings.AUTH_USER_MODEL)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="activity_time_entries", to="companies.company")),
                ("project", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="activity_time_entries", to="projects.project")),
                ("sprint", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="time_entries", to="sprints.sprint")),
            ],
            options={
                "ordering": ["-date", "-created_at"],
            },
        ),
    ]
