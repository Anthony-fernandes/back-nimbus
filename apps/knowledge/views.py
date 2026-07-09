from django.db import models
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

import logging

logger = logging.getLogger(__name__)

from common.access import normalize_user_role, user_has_any_permission
from common.viewsets import CompanyScopedModelViewSet
from .models import ArticleAttachment, ArticleRating, ArticleVersion, KnowledgeArticle, KnowledgeCategory, KnowledgeInternalComment, KnowledgeTag


def _is_client(user) -> bool:
    return normalize_user_role(getattr(user, "role", None)) == "CLIENT"


def _can_manage_knowledge(user) -> bool:
    return user_has_any_permission(user, ["knowledge.manage", "knowledge.edit", "settings.edit"]) or \
        normalize_user_role(getattr(user, "role", None)) == "ADMIN"
from .serializers import (
    ArticleAttachmentSerializer,
    ArticleRatingSerializer,
    ArticleVersionSerializer,
    KnowledgeArticleSerializer,
    KnowledgeCategorySerializer,
    KnowledgeInternalCommentSerializer,
    KnowledgeTagSerializer,
)


class KnowledgeCategoryViewSet(CompanyScopedModelViewSet):
    queryset = KnowledgeCategory.objects.all()
    serializer_class = KnowledgeCategorySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["active", "parent"]
    search_fields = ["name", "description", "slug"]
    ordering_fields = "__all__"


class KnowledgeTagViewSet(CompanyScopedModelViewSet):
    queryset = KnowledgeTag.objects.all()
    serializer_class = KnowledgeTagSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["name", "slug"]
    ordering_fields = "__all__"


class KnowledgeArticleViewSet(CompanyScopedModelViewSet):
    queryset = KnowledgeArticle.objects.all()
    serializer_class = KnowledgeArticleSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["status", "visibility", "category", "author"]
    search_fields = ["title", "summary", "content", "slug"]
    ordering_fields = "__all__"

    def get_queryset(self):
        qs = super().get_queryset()
        # Isolamento por papel: clientes só enxergam artigos PUBLICADOS e PÚBLICOS.
        if _is_client(self.request.user):
            qs = qs.filter(status="PUBLISHED", visibility="PUBLIC")
        q = self.request.query_params.get('q', '').strip()
        if q:
            try:
                from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
                search_query = SearchQuery(q, config='portuguese')
                search_vector = (
                    SearchVector('title', weight='A', config='portuguese') +
                    SearchVector('content', weight='B', config='portuguese') +
                    SearchVector('summary', weight='C', config='portuguese')
                )
                qs = (
                    qs.annotate(rank=SearchRank(search_vector, search_query))
                    .filter(rank__gt=0.01)
                    .order_by('-rank')
                )
            except Exception as exc:
                logger.warning("FTS search failed, falling back to icontains: %s", exc)
                qs = qs.filter(
                    models.Q(title__icontains=q) |
                    models.Q(content__icontains=q) |
                    models.Q(summary__icontains=q)
                )
        return qs

    def perform_create(self, serializer):
        if _is_client(self.request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Clientes não podem criar artigos da base de conhecimento.")
        serializer.save(company=self.request.user.company, author=self.request.user)

    def perform_update(self, serializer):
        if _is_client(self.request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Clientes não podem editar artigos da base de conhecimento.")
        article = self.get_object()
        # Save a version snapshot before updating
        last_version = article.versions.order_by("-version").first()
        next_version_num = (last_version.version + 1) if last_version else article.version
        change_summary = self.request.data.get("change_summary", "")
        ArticleVersion.objects.create(
            article=article,
            version=article.version,
            title=article.title,
            content=article.content,
            changed_by=self.request.user,
            change_summary=change_summary,
        )
        serializer.save(version=next_version_num)

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        article = self.get_object()
        if article.status == "PUBLISHED":
            raise ValidationError("Article is already published.")
        article.status = "PUBLISHED"
        article.published_at = timezone.now()
        article.save(update_fields=["status", "published_at", "updated_at"])
        return Response(self.get_serializer(article).data)

    @action(detail=True, methods=["post"])
    def rate(self, request, pk=None):
        article = self.get_object()
        helpful = request.data.get("helpful")
        if helpful is None:
            raise ValidationError("'helpful' field is required.")
        helpful = bool(helpful)
        rating, created = ArticleRating.objects.get_or_create(
            article=article,
            user=request.user,
            defaults={"helpful": helpful},
        )
        if not created:
            old_helpful = rating.helpful
            if old_helpful != helpful:
                rating.helpful = helpful
                rating.save(update_fields=["helpful", "updated_at"])
                if helpful:
                    article.helpful_count = max(0, article.helpful_count + 1)
                    article.not_helpful_count = max(0, article.not_helpful_count - 1)
                else:
                    article.not_helpful_count = max(0, article.not_helpful_count + 1)
                    article.helpful_count = max(0, article.helpful_count - 1)
                article.save(update_fields=["helpful_count", "not_helpful_count", "updated_at"])
        else:
            if helpful:
                article.helpful_count += 1
            else:
                article.not_helpful_count += 1
            article.save(update_fields=["helpful_count", "not_helpful_count", "updated_at"])
        return Response(self.get_serializer(article).data)

    @action(detail=True, methods=["post"], url_path="increment-views")
    def increment_views(self, request, pk=None):
        article = self.get_object()
        article.views_count += 1
        article.save(update_fields=["views_count", "updated_at"])
        return Response({"views_count": article.views_count})

    @action(detail=True, methods=["post"], url_path="request-review")
    def request_review(self, request, pk=None):
        article = self.get_object()
        article.status = "REVIEW"
        article.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(article).data)


class ArticleVersionViewSet(CompanyScopedModelViewSet):
    queryset = ArticleVersion.objects.all()
    serializer_class = ArticleVersionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["article"]
    ordering_fields = "__all__"
    company_field_name = "article__company"

    def get_queryset(self):
        user = self.request.user
        company = getattr(user, "company", None)
        if not company:
            return self.queryset.none()
        return self.queryset.filter(article__company=company)

    def perform_create(self, serializer):
        serializer.save(changed_by=self.request.user)


class ArticleAttachmentViewSet(CompanyScopedModelViewSet):
    queryset = ArticleAttachment.objects.all()
    serializer_class = ArticleAttachmentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["article"]
    ordering_fields = "__all__"
    company_field_name = "article__company"

    def get_queryset(self):
        user = self.request.user
        company = getattr(user, "company", None)
        if not company:
            return self.queryset.none()
        return self.queryset.filter(article__company=company)


class ArticleRatingViewSet(CompanyScopedModelViewSet):
    queryset = ArticleRating.objects.all()
    serializer_class = ArticleRatingSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["article", "helpful"]
    ordering_fields = "__all__"
    company_field_name = "article__company"

    def get_queryset(self):
        user = self.request.user
        company = getattr(user, "company", None)
        if not company:
            return self.queryset.none()
        return self.queryset.filter(article__company=company)


class KnowledgeInternalCommentViewSet(CompanyScopedModelViewSet):
    queryset = KnowledgeInternalComment.objects.all()
    serializer_class = KnowledgeInternalCommentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["article", "author"]
    ordering_fields = "__all__"
    company_field_name = "article__company"

    def get_queryset(self):
        user = self.request.user
        company = getattr(user, "company", None)
        if not company:
            return self.queryset.none()
        # Comentários internos nunca são visíveis a clientes.
        if _is_client(user):
            return KnowledgeInternalComment.objects.none()
        return KnowledgeInternalComment.objects.filter(article__company=company)

    def perform_create(self, serializer):
        if _is_client(self.request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Clientes não podem comentar internamente.")
        serializer.save(author=self.request.user)
