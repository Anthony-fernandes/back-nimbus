from rest_framework import serializers
from .models import (
    ChatConversation,
    ChatMessage,
    DoubtsAnswer,
    DoubtsAnswerLike,
    DoubtsQuestion,
    ForumCategory,
    ForumReply,
    ForumReplyLike,
    ForumTopic,
)


class ForumCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ForumCategory
        fields = "__all__"
        extra_kwargs = {"company": {"required": False, "read_only": True}}


class ForumReplySerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.full_name_or_username", read_only=True)

    class Meta:
        model = ForumReply
        fields = "__all__"
        extra_kwargs = {
            "author": {"required": False, "read_only": True},
            "likes_count": {"read_only": True},
            "is_best_answer": {"read_only": True},
        }


class ForumTopicSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.full_name_or_username", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = ForumTopic
        fields = "__all__"
        extra_kwargs = {
            "company": {"required": False, "read_only": True},
            "author": {"required": False, "read_only": True},
            "views_count": {"read_only": True},
            "replies_count": {"read_only": True},
            "best_answer": {"read_only": True},
        }


class ForumReplyLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForumReplyLike
        fields = "__all__"
        extra_kwargs = {"user": {"required": False, "read_only": True}}


class ChatMessageSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.full_name_or_username", read_only=True)

    class Meta:
        model = ChatMessage
        fields = "__all__"
        extra_kwargs = {
            "author": {"required": False, "read_only": True},
            "conversation": {"required": False},
        }


class ChatConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatConversation
        fields = "__all__"
        extra_kwargs = {
            "company": {"required": False, "read_only": True},
            "created_by": {"required": False, "read_only": True},
            "last_message_at": {"read_only": True},
        }


class DoubtsAnswerSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.full_name_or_username", read_only=True)

    class Meta:
        model = DoubtsAnswer
        fields = "__all__"
        extra_kwargs = {
            "author": {"required": False, "read_only": True},
            "likes_count": {"read_only": True},
            "is_accepted": {"read_only": True},
        }


class DoubtsQuestionSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.full_name_or_username", read_only=True)

    class Meta:
        model = DoubtsQuestion
        fields = "__all__"
        extra_kwargs = {
            "company": {"required": False, "read_only": True},
            "author": {"required": False, "read_only": True},
            "views_count": {"read_only": True},
            "answers_count": {"read_only": True},
        }


class DoubtsAnswerLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoubtsAnswerLike
        fields = "__all__"
        extra_kwargs = {"user": {"required": False, "read_only": True}}
