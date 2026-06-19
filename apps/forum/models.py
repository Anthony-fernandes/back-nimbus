from django.db import models
from common.models import BaseModel


class ForumCategory(BaseModel):
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="forum_app_categories",
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    icon = models.CharField(max_length=50, blank=True, default="")
    color = models.CharField(max_length=20, blank=True, default="")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class ForumTopic(BaseModel):
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="forum_app_topics",
    )
    category = models.ForeignKey(
        ForumCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="topics",
    )
    author = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="forum_app_topics",
    )
    title = models.CharField(max_length=300)
    content = models.TextField()
    is_pinned = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)
    upvotes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-is_pinned", "-created_at"]

    def __str__(self):
        return self.title


class ForumReply(BaseModel):
    topic = models.ForeignKey(ForumTopic, on_delete=models.CASCADE, related_name="replies")
    author = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="forum_app_replies",
    )
    content = models.TextField()
    is_solution = models.BooleanField(default=False)
    upvotes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Reply to {self.topic}"
