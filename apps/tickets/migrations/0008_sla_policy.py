import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("companies", "0001_initial"),
        ("tickets", "0007_ticket_rating"),
    ]

    operations = [
        migrations.CreateModel(
            name="SLAPolicy",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("name", models.CharField(max_length=200)),
                ("priority", models.CharField(blank=True, choices=[("Critica", "Critica"), ("Alta", "Alta"), ("Media", "Media"), ("Baixa", "Baixa"), ("", "Qualquer")], default="", max_length=30)),
                ("category", models.CharField(blank=True, default="", max_length=80)),
                ("response_time", models.CharField(default="8h", help_text="Ex: 2h, 1d, 30m", max_length=20)),
                ("priority_weight", models.IntegerField(default=0)),
                ("active", models.BooleanField(default=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sla_policies", to="companies.company")),
            ],
            options={"ordering": ["-priority_weight", "name"]},
        ),
    ]
