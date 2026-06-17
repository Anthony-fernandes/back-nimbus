from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("companies", "0001_initial"),
        ("activities", "0003_activity_integrations"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ActivityComment",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("author_name", models.CharField(blank=True, default="", max_length=255)),
                ("body", models.TextField(blank=True, default="")),
                ("is_internal", models.BooleanField(default=False)),
                ("source", models.CharField(blank=True, default="", max_length=80)),
                ("activity", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="comments", to="activities.activity")),
                ("author", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="activity_comments", to=settings.AUTH_USER_MODEL)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="activity_comments", to="companies.company")),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
        migrations.CreateModel(
            name="ActivityAttachment",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("name", models.CharField(max_length=255)),
                ("url", models.CharField(blank=True, default="", max_length=500)),
                ("content_type", models.CharField(blank=True, default="", max_length=120)),
                ("size", models.PositiveIntegerField(default=0)),
                ("source", models.CharField(blank=True, default="", max_length=80)),
                ("activity", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attachments", to="activities.activity")),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="activity_attachments", to="companies.company")),
                ("uploaded_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="activity_attachments", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
