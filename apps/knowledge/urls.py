from rest_framework.routers import DefaultRouter
from .views import (
    ArticleAttachmentViewSet,
    ArticleRatingViewSet,
    ArticleVersionViewSet,
    KnowledgeArticleViewSet,
    KnowledgeCategoryViewSet,
    KnowledgeTagViewSet,
)

router = DefaultRouter()
router.register(r"categories", KnowledgeCategoryViewSet, basename="knowledge-category")
router.register(r"tags", KnowledgeTagViewSet, basename="knowledge-tag")
router.register(r"articles", KnowledgeArticleViewSet, basename="knowledge-article")
router.register(r"article-versions", ArticleVersionViewSet, basename="article-version")
router.register(r"article-attachments", ArticleAttachmentViewSet, basename="article-attachment")
router.register(r"article-ratings", ArticleRatingViewSet, basename="article-rating")

urlpatterns = router.urls
