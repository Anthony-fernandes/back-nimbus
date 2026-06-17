from rest_framework import serializers
from .models import ArticleAttachment, ArticleRating, ArticleVersion, KnowledgeArticle, KnowledgeCategory, KnowledgeTag


class KnowledgeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeCategory
        fields = "__all__"
        extra_kwargs = {"company": {"required": False, "read_only": True}}


class KnowledgeTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeTag
        fields = "__all__"
        extra_kwargs = {"company": {"required": False, "read_only": True}}


class KnowledgeArticleSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.full_name_or_username", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = KnowledgeArticle
        fields = "__all__"
        extra_kwargs = {
            "company": {"required": False, "read_only": True},
            "views_count": {"read_only": True},
            "helpful_count": {"read_only": True},
            "not_helpful_count": {"read_only": True},
            "published_at": {"read_only": True},
            "version": {"read_only": True},
            "source_ticket": {"read_only": True},
            "source_forum_topic": {"read_only": True},
            "source_doubts_question": {"read_only": True},
        }


class ArticleVersionSerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source="changed_by.full_name_or_username", read_only=True)

    class Meta:
        model = ArticleVersion
        fields = "__all__"
        extra_kwargs = {"changed_by": {"required": False, "read_only": True}}


class ArticleAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleAttachment
        fields = "__all__"


class ArticleRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleRating
        fields = "__all__"
        extra_kwargs = {"user": {"required": False, "read_only": True}}
