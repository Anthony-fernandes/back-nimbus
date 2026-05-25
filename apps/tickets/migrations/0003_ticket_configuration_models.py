# Generated manually for integration hardening.

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("companies", "0001_initial"),
        ("tickets", "0002_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="TicketCategory",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("name", models.CharField(max_length=120)),
                ("description", models.TextField(blank=True, default="")),
                ("active", models.BooleanField(default=True)),
                ("sla", models.CharField(blank=True, default="", max_length=30)),
                ("sla_unit", models.CharField(blank=True, default="", max_length=20)),
                ("approval_required", models.BooleanField(default=False)),
                ("default_type", models.CharField(blank=True, default="", max_length=80)),
                ("default_priority", models.CharField(blank=True, default="", max_length=30)),
                ("default_impact", models.CharField(blank=True, default="", max_length=30)),
                ("default_team", models.CharField(blank=True, default="", max_length=120)),
                ("allow_project_activity", models.BooleanField(default=True)),
                ("requires_technical_categorization", models.BooleanField(default=False)),
                ("requires_client_validation", models.BooleanField(default=False)),
                ("color", models.CharField(blank=True, default="", max_length=20)),
                ("icon", models.CharField(blank=True, default="", max_length=60)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ticket_categories", to="companies.company")),
            ],
            options={
                "ordering": ["name"],
                "unique_together": {("company", "name")},
            },
        ),
        migrations.CreateModel(
            name="TicketWorkflowStatus",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("name", models.CharField(max_length=120)),
                ("slug", models.SlugField(max_length=140)),
                ("description", models.TextField(blank=True, default="")),
                ("color", models.CharField(blank=True, default="", max_length=20)),
                ("active", models.BooleanField(default=True)),
                ("pauses_sla", models.BooleanField(default=False)),
                ("is_final", models.BooleanField(default=False)),
                ("allows_resume", models.BooleanField(default=False)),
                ("order", models.PositiveIntegerField(default=999)),
                ("origin_statuses", models.JSONField(blank=True, default=list)),
                ("next_statuses", models.JSONField(blank=True, default=list)),
                ("system", models.BooleanField(default=False)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ticket_workflow_statuses", to="companies.company")),
            ],
            options={
                "ordering": ["order", "name"],
                "unique_together": {("company", "slug")},
            },
        ),
    ]
