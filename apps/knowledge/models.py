from django.db import models
from apps.companies.models import Company
from apps.users.models import User
from common.models import BaseModel


class KnowledgeCategory(BaseModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="knowledge_categories")
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280)
    description = models.TextField(blank=True, default="")
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children")
    order = models.IntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class KnowledgeTag(BaseModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="knowledge_tags")
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class KnowledgeArticle(BaseModel):
    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("PUBLISHED", "Published"),
        ("ARCHIVED", "Archived"),
    ]
    VISIBILITY_CHOICES = [
        ("PUBLIC", "Public"),
        ("INTERNAL", "Internal"),
        ("RESTRICTED", "Restricted"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="knowledge_articles")
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280)
    content = models.TextField(blank=True, default="")
    summary = models.TextField(blank=True, default="")
    category = models.ForeignKey(KnowledgeCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="articles")
    tags = models.ManyToManyField(KnowledgeTag, blank=True, related_name="articles")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="DRAFT")
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default="INTERNAL")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="knowledge_articles")
    views_count = models.IntegerField(default=0)
    helpful_count = models.IntegerField(default=0)
    not_helpful_count = models.IntegerField(default=0)
    version = models.IntegerField(default=1)
    published_at = models.DateTimeField(null=True, blank=True)
    source_ticket = models.ForeignKey(
        "tickets.Ticket",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="knowledge_articles",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class ArticleVersion(BaseModel):
    article = models.ForeignKey(KnowledgeArticle, on_delete=models.CASCADE, related_name="versions")
    version = models.IntegerField()
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True, default="")
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="article_versions")
    change_summary = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        ordering = ["-version"]

    def __str__(self):
        return f"{self.article} v{self.version}"


class ArticleAttachment(BaseModel):
    article = models.ForeignKey(KnowledgeArticle, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="knowledge/attachments/")
    name = models.CharField(max_length=255)
    size = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class ArticleRating(BaseModel):
    article = models.ForeignKey(KnowledgeArticle, on_delete=models.CASCADE, related_name="ratings")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="article_ratings")
    helpful = models.BooleanField()

    class Meta:
        unique_together = ("article", "user")

    def __str__(self):
        return f"{self.article} - {self.user}"
