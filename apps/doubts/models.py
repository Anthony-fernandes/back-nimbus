from django.db import models
from common.models import BaseModel


class DoubtsQuestion(BaseModel):
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="doubts_app_questions",
    )
    author = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="doubts_app_questions",
    )
    title = models.CharField(max_length=300)
    content = models.TextField()
    tags = models.JSONField(default=list, blank=True)
    is_answered = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)
    upvotes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class DoubtsAnswer(BaseModel):
    question = models.ForeignKey(DoubtsQuestion, on_delete=models.CASCADE, related_name="answers")
    author = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="doubts_app_answers",
    )
    content = models.TextField()
    is_accepted = models.BooleanField(default=False)
    upvotes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-is_accepted", "created_at"]

    def __str__(self):
        return f"Answer to {self.question}"
