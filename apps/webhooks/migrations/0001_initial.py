import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("companies", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Webhook",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("name", models.CharField(max_length=200)),
                ("url", models.URLField(max_length=500)),
                ("secret", models.CharField(blank=True, help_text="HMAC secret for request signing", max_length=200)),
                ("events", models.JSONField(default=list, help_text="List of event keys to listen to")),
                ("active", models.BooleanField(default=True)),
                ("last_triggered_at", models.DateTimeField(blank=True, null=True)),
                ("last_status_code", models.IntegerField(blank=True, null=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="webhooks", to="companies.company")),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="WebhookDelivery",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("event", models.CharField(max_length=100)),
                ("payload", models.JSONField()),
                ("status_code", models.IntegerField(blank=True, null=True)),
                ("response_body", models.TextField(blank=True)),
                ("success", models.BooleanField(default=False)),
                ("error", models.TextField(blank=True)),
                ("webhook", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="deliveries", to="webhooks.webhook")),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
