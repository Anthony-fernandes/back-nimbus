from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("companies", "0001_initial"),
        ("users", "0005_permissionblock_user_permission_blocks_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Department",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("name", models.CharField(max_length=120)),
                ("description", models.TextField(blank=True, default="")),
                ("active", models.BooleanField(default=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="departments", to="companies.company")),
                ("manager", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="managed_departments", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["name"],
                "unique_together": {("company", "name")},
            },
        ),
        migrations.CreateModel(
            name="Position",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("name", models.CharField(max_length=120)),
                ("description", models.TextField(blank=True, default="")),
                ("auto_approval", models.BooleanField(default=False)),
                ("active", models.BooleanField(default=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="positions", to="companies.company")),
            ],
            options={
                "ordering": ["name"],
                "unique_together": {("company", "name")},
            },
        ),
        migrations.AddField(
            model_name="user",
            name="approval_mode",
            field=models.CharField(choices=[("INHERITED", "Aprovador vinculado"), ("SUPERVISOR", "Supervisor imediato"), ("MANAGER", "Gerente responsavel"), ("AUTO", "Aprovacao automatica"), ("SERVICE_DESK", "Equipe de chamados")], default="INHERITED", max_length=20),
        ),
        migrations.AddField(
            model_name="user",
            name="is_service_desk_approver",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="user",
            name="department",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="members", to="users.department"),
        ),
        migrations.AddField(
            model_name="user",
            name="position",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="users", to="users.position"),
        ),
        migrations.AddField(
            model_name="user",
            name="supervisor",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="supervised_users", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="user",
            name="manager",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="managed_users", to=settings.AUTH_USER_MODEL),
        ),
    ]
