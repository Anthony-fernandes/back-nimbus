import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("companies", "0001_initial"),
        ("tickets", "0008_sla_policy"),
    ]

    operations = [
        migrations.CreateModel(
            name="TicketTemplate",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("name", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True, default="")),
                ("title", models.CharField(blank=True, default="", max_length=300)),
                ("type", models.CharField(blank=True, default="", max_length=80)),
                ("priority", models.CharField(blank=True, default="", max_length=30)),
                ("description_template", models.TextField(blank=True, default="", help_text="Template de descricao do chamado")),
                ("tags", models.JSONField(blank=True, default=list)),
                ("active", models.BooleanField(default=True)),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ticket_templates",
                        to="companies.company",
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="templates",
                        to="tickets.ticketcategory",
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
            },
        ),
    ]
