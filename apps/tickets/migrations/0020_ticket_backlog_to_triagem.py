"""Chamado não possui status 'Backlog' (Backlog é fila de planejamento, não status).

Migra chamados legados em 'Backlog' para 'Triagem'.
"""
from django.db import migrations


def forwards(apps, schema_editor):
    Ticket = apps.get_model("tickets", "Ticket")
    Ticket.objects.filter(status="Backlog").update(status="Triagem")


class Migration(migrations.Migration):
    dependencies = [("tickets", "0019_alter_ticket_status")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
