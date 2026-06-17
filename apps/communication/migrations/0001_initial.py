import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("companies", "0001_initial"),
        ("knowledge", "0001_initial"),
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
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, default="")),
                ("order", models.IntegerField(default=0)),
                ("active", models.BooleanField(default=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="forum_categories", to="companies.company")),
            ],
            options={"ordering": ["order", "name"]},
        ),
        migrations.CreateModel(
            name="ForumTopic",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("title", models.CharField(max_length=255)),
                ("content", models.TextField(blank=True, default="")),
                ("is_pinned", models.BooleanField(default=False)),
                ("is_locked", models.BooleanField(default=False)),
                ("views_count", models.IntegerField(default=0)),
                ("replies_count", models.IntegerField(default=0)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="forum_topics", to="companies.company")),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="topics", to="communication.forumcategory")),
                ("author", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="forum_topics", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-is_pinned", "-created_at"]},
        ),
        migrations.CreateModel(
            name="ForumReply",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("content", models.TextField(blank=True, default="")),
                ("is_best_answer", models.BooleanField(default=False)),
                ("likes_count", models.IntegerField(default=0)),
                ("topic", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="replies", to="communication.forumtopic")),
                ("author", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="forum_replies", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.AddField(
            model_name="forumtopic",
            name="best_answer",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="best_answer_for", to="communication.forumreply"),
        ),
        migrations.CreateModel(
            name="ForumReplyLike",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("reply", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="likes", to="communication.forumreply")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="forum_reply_likes", to=settings.AUTH_USER_MODEL)),
            ],
            options={"unique_together": {("reply", "user")}},
        ),
        migrations.CreateModel(
            name="ChatConversation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("last_message_at", models.DateTimeField(blank=True, null=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="chat_conversations", to="companies.company")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_conversations", to=settings.AUTH_USER_MODEL)),
                ("participants", models.ManyToManyField(blank=True, related_name="chat_conversations", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-last_message_at", "-created_at"]},
        ),
        migrations.CreateModel(
            name="ChatMessage",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("content", models.TextField(blank=True, default="")),
                ("file", models.FileField(blank=True, null=True, upload_to="chat/files/")),
                ("file_name", models.CharField(blank=True, max_length=255, null=True)),
                ("conversation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="communication.chatconversation")),
                ("author", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="chat_messages", to=settings.AUTH_USER_MODEL)),
                ("read_by", models.ManyToManyField(blank=True, related_name="read_messages", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.CreateModel(
            name="DoubtsQuestion",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("title", models.CharField(max_length=255)),
                ("content", models.TextField(blank=True, default="")),
                ("status", models.CharField(choices=[("OPEN", "Open"), ("ANSWERED", "Answered"), ("CLOSED", "Closed")], default="OPEN", max_length=20)),
                ("views_count", models.IntegerField(default=0)),
                ("answers_count", models.IntegerField(default=0)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="doubts_questions", to="companies.company")),
                ("author", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="doubts_questions", to=settings.AUTH_USER_MODEL)),
                ("tags", models.ManyToManyField(blank=True, related_name="doubts_questions", to="knowledge.knowledgetag")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="DoubtsAnswer",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("content", models.TextField(blank=True, default="")),
                ("is_accepted", models.BooleanField(default=False)),
                ("likes_count", models.IntegerField(default=0)),
                ("question", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="answers", to="communication.doubtsquestion")),
                ("author", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="doubts_answers", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.CreateModel(
            name="DoubtsAnswerLike",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("answer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="likes", to="communication.doubtsanswer")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="doubts_answer_likes", to=settings.AUTH_USER_MODEL)),
            ],
            options={"unique_together": {("answer", "user")}},
        ),
    ]
