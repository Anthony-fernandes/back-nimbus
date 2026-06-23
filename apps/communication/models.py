from django.db import models
from apps.companies.models import Company
from apps.users.models import User
from apps.knowledge.models import KnowledgeTag
from common.models import BaseModel


class ForumCategory(BaseModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="forum_categories")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    order = models.IntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class ForumTopic(BaseModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="forum_topics")
    category = models.ForeignKey(ForumCategory, on_delete=models.CASCADE, related_name="topics")
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True, default="")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="forum_topics")
    is_pinned = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    views_count = models.IntegerField(default=0)
    replies_count = models.IntegerField(default=0)
    best_answer = models.ForeignKey(
        "ForumReply",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="best_answer_for",
    )
    likes_count = models.IntegerField(default=0)
    downvotes_count = models.IntegerField(default=0)
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-is_pinned", "-created_at"]

    def __str__(self):
        return self.title


class ForumReply(BaseModel):
    topic = models.ForeignKey(ForumTopic, on_delete=models.CASCADE, related_name="replies")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="forum_replies")
    content = models.TextField(blank=True, default="")
    is_best_answer = models.BooleanField(default=False)
    likes_count = models.IntegerField(default=0)
    downvotes_count = models.IntegerField(default=0)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Reply to {self.topic}"


class ForumReplyLike(BaseModel):
    reply = models.ForeignKey(ForumReply, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="forum_reply_likes")

    class Meta:
        unique_together = ("reply", "user")


class ForumTopicLike(BaseModel):
    topic = models.ForeignKey(ForumTopic, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="forum_topic_likes")

    class Meta:
        unique_together = ("topic", "user")


class ForumTopicDownvote(BaseModel):
    topic = models.ForeignKey(ForumTopic, on_delete=models.CASCADE, related_name="downvotes")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="forum_topic_downvotes")

    class Meta:
        unique_together = ("topic", "user")


class ForumReplyDownvote(BaseModel):
    reply = models.ForeignKey(ForumReply, on_delete=models.CASCADE, related_name="downvotes")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="forum_reply_downvotes")

    class Meta:
        unique_together = ("reply", "user")


class ForumComment(BaseModel):
    topic = models.ForeignKey(ForumTopic, on_delete=models.CASCADE, null=True, blank=True, related_name="comments")
    reply = models.ForeignKey(ForumReply, on_delete=models.CASCADE, null=True, blank=True, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="forum_comments")
    content = models.TextField()

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author}"


class ContentFlag(BaseModel):
    REASON_CHOICES = [
        ("spam", "Spam"),
        ("inappropriate", "Conteúdo inadequado"),
        ("duplicate", "Duplicado"),
        ("other", "Outro"),
    ]
    content_type = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    reason = models.CharField(max_length=50, choices=REASON_CHOICES, default="other")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="content_flags")
    reviewed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Flag on {self.content_type}:{self.object_id}"


class DoubtsQuestionLike(BaseModel):
    question = models.ForeignKey("DoubtsQuestion", on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="doubts_question_likes")

    class Meta:
        unique_together = ("question", "user")


class DoubtsQuestionRating(BaseModel):
    question = models.ForeignKey("DoubtsQuestion", on_delete=models.CASCADE, related_name="ratings")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="doubts_ratings")
    rating = models.IntegerField(default=5)
    comment = models.TextField(blank=True, default="")

    class Meta:
        unique_together = ("question", "user")

    def __str__(self):
        return f"Rating {self.rating} for {self.question}"


class ChatMessageReaction(BaseModel):
    message = models.ForeignKey("ChatMessage", on_delete=models.CASCADE, related_name="reactions_set")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_reactions")
    emoji = models.CharField(max_length=10)

    class Meta:
        unique_together = ("message", "user", "emoji")

    def __str__(self):
        return f"{self.emoji} on {self.message}"


class ChatConversation(BaseModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="chat_conversations")
    participants = models.ManyToManyField(User, blank=True, related_name="chat_conversations")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_conversations")
    last_message_at = models.DateTimeField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ["-last_message_at", "-created_at"]

    def __str__(self):
        return str(self.id)


class ChatMessage(BaseModel):
    conversation = models.ForeignKey(ChatConversation, on_delete=models.CASCADE, related_name="messages")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="chat_messages")
    content = models.TextField(blank=True, default="")
    file = models.FileField(upload_to="chat/files/", null=True, blank=True)
    file_name = models.CharField(max_length=255, null=True, blank=True)
    reply_to = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="replies")
    is_pinned = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False)
    forward_from = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="forwards")
    read_by = models.ManyToManyField(User, blank=True, related_name="read_messages")

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message in {self.conversation}"


class DoubtsQuestion(BaseModel):
    STATUS_CHOICES = [
        ("OPEN", "Open"),
        ("ANSWERED", "Answered"),
        ("CLOSED", "Closed"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="doubts_questions")
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True, default="")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="doubts_questions")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="OPEN")
    views_count = models.IntegerField(default=0)
    answers_count = models.IntegerField(default=0)
    tags = models.ManyToManyField(KnowledgeTag, blank=True, related_name="doubts_questions")
    likes_count = models.IntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class DoubtsAnswer(BaseModel):
    question = models.ForeignKey(DoubtsQuestion, on_delete=models.CASCADE, related_name="answers")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="doubts_answers")
    content = models.TextField(blank=True, default="")
    is_accepted = models.BooleanField(default=False)
    likes_count = models.IntegerField(default=0)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Answer to {self.question}"


class DoubtsAnswerLike(BaseModel):
    answer = models.ForeignKey(DoubtsAnswer, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="doubts_answer_likes")

    class Meta:
        unique_together = ("answer", "user")
