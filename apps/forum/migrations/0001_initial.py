import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("companies", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ForumCategory",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True, default="")),
                ("icon", models.CharField(blank=True, default="", max_length=50)),
                ("color", models.CharField(blank=True, default="", max_length=20)),
                ("order", models.PositiveIntegerField(default=0)),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="forum_app_categories",
                        to="companies.company",
                    ),
                ),
            ],
            options={
                "ordering": ["order", "name"],
            },
        ),
        migrations.CreateModel(
            name="ForumTopic",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("title", models.CharField(max_length=300)),
                ("content", models.TextField()),
                ("is_pinned", models.BooleanField(default=False)),
                ("is_locked", models.BooleanField(default=False)),
                ("views", models.PositiveIntegerField(default=0)),
                ("upvotes", models.PositiveIntegerField(default=0)),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="forum_app_topics",
                        to="companies.company",
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="topics",
                        to="forum.forumcategory",
                    ),
                ),
                (
                    "author",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="forum_app_topics",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-is_pinned", "-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ForumReply",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("content", models.TextField()),
                ("is_solution", models.BooleanField(default=False)),
                ("upvotes", models.PositiveIntegerField(default=0)),
                (
                    "topic",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="replies",
                        to="forum.forumtopic",
                    ),
                ),
                (
                    "author",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="forum_app_replies",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
    ]
