from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("companies", "0001_initial"),
        ("activities", "0003_activity_integrations"),
        ("tickets", "0005_ticket_contact_responsible_name_and_phone"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="ticket",
            name="approval_status",
            field=models.CharField(choices=[("Nao requerido", "Nao requerido"), ("Aguardando Aprovacao", "Aguardando Aprovacao"), ("Aprovado", "Aprovado"), ("Reprovado", "Reprovado"), ("Ajustes Solicitados", "Ajustes Solicitados")], default="Nao requerido", max_length=40),
        ),
        migrations.AddField(
            model_name="ticket",
            name="approval_route",
            field=models.CharField(choices=[("NONE", "Sem aprovacao"), ("APPROVER", "Aprovador vinculado"), ("SERVICE_DESK", "Equipe de chamados"), ("AUTO", "Automatica por cargo")], default="NONE", max_length=20),
        ),
        migrations.AddField(
            model_name="ticket",
            name="approval_reason",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="ticket",
            name="current_approver",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="tickets_awaiting_approval", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="ticket",
            name="approved_by",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="approved_tickets", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="ticket",
            name="approved_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="ticket",
            name="converted_activity",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="source_tickets", to="activities.activity"),
        ),
        migrations.AddField(
            model_name="ticket",
            name="converted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="ticket",
            name="conversion_reason",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AlterField(
            model_name="ticket",
            name="status",
            field=models.CharField(choices=[("Aberto", "Aberto"), ("Aguardando Aprovacao", "Aguardando Aprovacao"), ("Aprovado", "Aprovado"), ("Reprovado", "Reprovado"), ("Ajustes Solicitados", "Ajustes Solicitados"), ("Triagem", "Triagem"), ("Backlog", "Backlog"), ("Aguardando atendimento", "Aguardando atendimento"), ("Em atendimento", "Em atendimento"), ("Aguardando cliente", "Aguardando cliente"), ("Validacao", "Validacao"), ("Pausado", "Pausado"), ("Cancelado", "Cancelado"), ("Finalizado", "Finalizado"), ("Convertido em Atividade de Projeto", "Convertido em Atividade de Projeto")], default="Aberto", max_length=40),
        ),
        migrations.CreateModel(
            name="TicketApproval",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("approver_name", models.CharField(blank=True, default="", max_length=255)),
                ("decision", models.CharField(choices=[("PENDENTE", "Pendente"), ("APROVADO", "Aprovado"), ("REPROVADO", "Reprovado"), ("AJUSTES", "Ajustes solicitados")], default="PENDENTE", max_length=20)),
                ("route", models.CharField(choices=[("NONE", "Sem aprovacao"), ("APPROVER", "Aprovador vinculado"), ("SERVICE_DESK", "Equipe de chamados"), ("AUTO", "Automatica por cargo")], default="APPROVER", max_length=20)),
                ("comment", models.TextField(blank=True, default="")),
                ("decided_at", models.DateTimeField(blank=True, null=True)),
                ("approver", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="ticket_approval_decisions", to=settings.AUTH_USER_MODEL)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ticket_approvals", to="companies.company")),
                ("ticket", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="approvals", to="tickets.ticket")),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="TicketComment",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("author_name", models.CharField(blank=True, default="", max_length=255)),
                ("body", models.TextField(blank=True, default="")),
                ("is_internal", models.BooleanField(default=False)),
                ("author", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="ticket_comments", to=settings.AUTH_USER_MODEL)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ticket_comments", to="companies.company")),
                ("ticket", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="comments", to="tickets.ticket")),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
        migrations.CreateModel(
            name="TicketAttachment",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("name", models.CharField(max_length=255)),
                ("url", models.CharField(blank=True, default="", max_length=500)),
                ("content_type", models.CharField(blank=True, default="", max_length=120)),
                ("size", models.PositiveIntegerField(default=0)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ticket_attachments", to="companies.company")),
                ("ticket", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attachments", to="tickets.ticket")),
                ("uploaded_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="ticket_attachments", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
