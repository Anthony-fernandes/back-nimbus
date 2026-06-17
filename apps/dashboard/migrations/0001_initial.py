import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('companies', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Dashboard',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('type', models.CharField(default='custom', max_length=50)),
                ('status', models.CharField(default='draft', max_length=30)),
                ('is_active', models.BooleanField(default=False)),
                ('components_json', models.JSONField(default=list)),
                ('filters_json', models.JSONField(default=list)),
                ('created_by', models.CharField(blank=True, max_length=200)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dashboards', to='companies.company')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='DashboardVersion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('version_number', models.IntegerField(default=1)),
                ('config_snapshot', models.JSONField(default=dict)),
                ('created_by', models.CharField(blank=True, max_length=200)),
                ('is_published', models.BooleanField(default=False)),
                ('dashboard', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='versions', to='dashboard.dashboard')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
