from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("companies", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("actor_name", models.CharField(blank=True, default="", max_length=255)),
                ("category", models.CharField(choices=[("Chamados", "Chamados"), ("Aprovacoes", "Aprovacoes"), ("Projetos", "Projetos"), ("Atividades", "Atividades"), ("Comentarios", "Comentarios"), ("Sistema", "Sistema")], default="Sistema", max_length=30)),
                ("event", models.CharField(blank=True, default="", max_length=80)),
                ("origin", models.CharField(blank=True, default="", max_length=80)),
                ("title", models.CharField(max_length=255)),
                ("message", models.TextField(blank=True, default="")),
                ("link", models.CharField(blank=True, default="", max_length=255)),
                ("entity_type", models.CharField(blank=True, default="", max_length=80)),
                ("entity_id", models.CharField(blank=True, default="", max_length=120)),
                ("is_read", models.BooleanField(default=False)),
                ("is_favorite", models.BooleanField(default=False)),
                ("is_archived", models.BooleanField(default=False)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("email_sent", models.BooleanField(default=False)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="sent_notifications", to=settings.AUTH_USER_MODEL)),
                ("company", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to="companies.company")),
                ("recipient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="NotificationPreference",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("email_enabled", models.BooleanField(default=True)),
                ("inbox_enabled", models.BooleanField(default=True)),
                ("disabled_events", models.JSONField(blank=True, default=list)),
                ("email_disabled_events", models.JSONField(blank=True, default=list)),
                ("digest_frequency", models.CharField(blank=True, default="instant", max_length=20)),
                ("company", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="notification_preferences", to="companies.company")),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="notification_preference", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["user__username"],
            },
        ),
    ]
