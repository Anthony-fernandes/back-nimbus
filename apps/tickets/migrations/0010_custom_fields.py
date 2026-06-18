import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0009_ticket_template'),
        ('companies', '0002_company_auto_assign'),
    ]

    operations = [
        migrations.CreateModel(
            name='TicketCustomField',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('name', models.CharField(max_length=100)),
                ('label', models.CharField(max_length=150)),
                ('field_type', models.CharField(choices=[('text', 'Texto'), ('number', 'Número'), ('date', 'Data'), ('select', 'Seleção'), ('boolean', 'Sim/Não')], max_length=30)),
                ('options', models.JSONField(blank=True, default=list)),
                ('required', models.BooleanField(default=False)),
                ('active', models.BooleanField(default=True)),
                ('order', models.PositiveIntegerField(default=0)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='custom_fields', to='companies.company')),
            ],
            options={
                'ordering': ['order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='TicketCustomValue',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('value', models.TextField(blank=True, default='')),
                ('field', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tickets.ticketcustomfield')),
                ('ticket', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='custom_values', to='tickets.ticket')),
            ],
            options={
                'unique_together': {('ticket', 'field')},
            },
        ),
    ]
