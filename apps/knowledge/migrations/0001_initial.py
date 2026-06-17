import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("companies", "0001_initial"),
        ("tickets", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="KnowledgeCategory",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("name", models.CharField(max_length=255)),
                ("slug", models.SlugField(max_length=280)),
                ("description", models.TextField(blank=True, default="")),
                ("order", models.IntegerField(default=0)),
                ("active", models.BooleanField(default=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="knowledge_categories", to="companies.company")),
                ("parent", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="children", to="knowledge.knowledgecategory")),
            ],
            options={"ordering": ["order", "name"]},
        ),
        migrations.CreateModel(
            name="KnowledgeTag",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("name", models.CharField(max_length=120)),
                ("slug", models.SlugField(max_length=140)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="knowledge_tags", to="companies.company")),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="KnowledgeArticle",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("title", models.CharField(max_length=255)),
                ("slug", models.SlugField(max_length=280)),
                ("content", models.TextField(blank=True, default="")),
                ("summary", models.TextField(blank=True, default="")),
                ("status", models.CharField(choices=[("DRAFT", "Draft"), ("PUBLISHED", "Published"), ("ARCHIVED", "Archived")], default="DRAFT", max_length=20)),
                ("visibility", models.CharField(choices=[("PUBLIC", "Public"), ("INTERNAL", "Internal"), ("RESTRICTED", "Restricted")], default="INTERNAL", max_length=20)),
                ("views_count", models.IntegerField(default=0)),
                ("helpful_count", models.IntegerField(default=0)),
                ("not_helpful_count", models.IntegerField(default=0)),
                ("version", models.IntegerField(default=1)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="knowledge_articles", to="companies.company")),
                ("category", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="articles", to="knowledge.knowledgecategory")),
                ("author", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="knowledge_articles", to=settings.AUTH_USER_MODEL)),
                ("tags", models.ManyToManyField(blank=True, related_name="articles", to="knowledge.knowledgetag")),
                ("source_ticket", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="knowledge_articles", to="tickets.ticket")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ArticleVersion",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("version", models.IntegerField()),
                ("title", models.CharField(max_length=255)),
                ("content", models.TextField(blank=True, default="")),
                ("change_summary", models.CharField(blank=True, default="", max_length=500)),
                ("article", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="versions", to="knowledge.knowledgearticle")),
                ("changed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="article_versions", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-version"]},
        ),
        migrations.CreateModel(
            name="ArticleAttachment",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("file", models.FileField(upload_to="knowledge/attachments/")),
                ("name", models.CharField(max_length=255)),
                ("size", models.IntegerField(blank=True, null=True)),
                ("article", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attachments", to="knowledge.knowledgearticle")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ArticleRating",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("helpful", models.BooleanField()),
                ("article", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ratings", to="knowledge.knowledgearticle")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="article_ratings", to=settings.AUTH_USER_MODEL)),
            ],
            options={"unique_together": {("article", "user")}},
        ),
    ]
