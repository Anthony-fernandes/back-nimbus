from rest_framework import serializers
from .models import (
    ChatConversation,
    ChatMessage,
    ChatMessageReaction,
    ContentFlag,
    DoubtsAnswer,
    DoubtsAnswerLike,
    DoubtsQuestion,
    DoubtsQuestionLike,
    DoubtsQuestionRating,
    ForumBadge,
    ForumCategory,
    ForumComment,
    ForumReply,
    ForumReplyEdit,
    ForumReplyLike,
    ForumTopic,
    ForumTopicEdit,
    ForumUserReputation,
    UserBadge,
)


class ForumCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ForumCategory
        fields = "__all__"
        extra_kwargs = {"company": {"required": False, "read_only": True}}


class ForumReplySerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.full_name_or_username", read_only=True)
    edit_count = serializers.SerializerMethodField()
    author_reputation = serializers.SerializerMethodField()

    def get_edit_count(self, obj):
        return obj.edits.count()

    def get_author_reputation(self, obj):
        if not obj.author:
            return 0
        return ForumUserReputation.objects.filter(
            company=obj.topic.company, user=obj.author
        ).values_list("score", flat=True).first() or 0

    class Meta:
        model = ForumReply
        fields = "__all__"
        extra_kwargs = {
            "author": {"required": False, "read_only": True},
            "likes_count": {"read_only": True},
            "downvotes_count": {"read_only": True},
            "is_best_answer": {"read_only": True},
        }


class ForumTopicSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.full_name_or_username", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    edit_count = serializers.SerializerMethodField()
    author_reputation = serializers.SerializerMethodField()

    def get_edit_count(self, obj):
        return obj.edits.count()

    def get_author_reputation(self, obj):
        if not obj.author:
            return 0
        return ForumUserReputation.objects.filter(
            company=obj.company, user=obj.author
        ).values_list("score", flat=True).first() or 0

    class Meta:
        model = ForumTopic
        fields = "__all__"
        extra_kwargs = {
            "company": {"required": False, "read_only": True},
            "author": {"required": False, "read_only": True},
            "views_count": {"read_only": True},
            "replies_count": {"read_only": True},
            "best_answer": {"read_only": True},
            "likes_count": {"read_only": True},
            "downvotes_count": {"read_only": True},
        }


class ForumReplyLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForumReplyLike
        fields = "__all__"
        extra_kwargs = {"user": {"required": False, "read_only": True}}


class ForumCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.full_name_or_username", read_only=True)

    class Meta:
        model = ForumComment
        fields = "__all__"
        extra_kwargs = {"author": {"required": False, "read_only": True}}


class ContentFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentFlag
        fields = "__all__"
        extra_kwargs = {"author": {"required": False, "read_only": True}}


class ChatMessageSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.full_name_or_username", read_only=True)
    reply_to_preview = serializers.SerializerMethodField()
    reply_to_author = serializers.SerializerMethodField()
    reactions = serializers.SerializerMethodField()
    read_by_ids = serializers.PrimaryKeyRelatedField(many=True, read_only=True, source="read_by")

    class Meta:
        model = ChatMessage
        fields = "__all__"
        extra_kwargs = {
            "author": {"required": False, "read_only": True},
            "conversation": {"required": False},
        }

    def get_reply_to_preview(self, obj):
        if obj.reply_to:
            return (obj.reply_to.content or "")[:60]
        return None

    def get_reply_to_author(self, obj):
        if obj.reply_to and obj.reply_to.author:
            return obj.reply_to.author.full_name_or_username
        return None

    def get_reactions(self, obj):
        result = {}
        for r in obj.reactions_set.all():
            result.setdefault(r.emoji, []).append(str(r.user_id))
        return result


class ChatConversationSerializer(serializers.ModelSerializer):
    participant_names = serializers.SerializerMethodField()

    class Meta:
        model = ChatConversation
        fields = "__all__"
        extra_kwargs = {
            "company": {"required": False, "read_only": True},
            "created_by": {"required": False, "read_only": True},
            "last_message_at": {"read_only": True},
        }

    def get_participant_names(self, obj):
        return [u.full_name_or_username for u in obj.participants.all()]


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
            "likes_count": {"read_only": True},
        }


class DoubtsAnswerLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoubtsAnswerLike
        fields = "__all__"
        extra_kwargs = {"user": {"required": False, "read_only": True}}


class DoubtsQuestionLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoubtsQuestionLike
        fields = "__all__"
        extra_kwargs = {"user": {"required": False, "read_only": True}}


class DoubtsQuestionRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoubtsQuestionRating
        fields = "__all__"
        extra_kwargs = {"user": {"required": False, "read_only": True}}


class ChatMessageReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessageReaction
        fields = "__all__"
        extra_kwargs = {"user": {"required": False, "read_only": True}}


class ForumTopicEditSerializer(serializers.ModelSerializer):
    editor_name = serializers.SerializerMethodField()

    def get_editor_name(self, obj):
        return obj.editor.get_full_name() or obj.editor.username if obj.editor else ""

    class Meta:
        model = ForumTopicEdit
        fields = ["id", "editor", "editor_name", "old_title", "new_title", "old_content", "new_content", "edit_comment", "created_at"]


class ForumReplyEditSerializer(serializers.ModelSerializer):
    editor_name = serializers.SerializerMethodField()

    def get_editor_name(self, obj):
        return obj.editor.get_full_name() or obj.editor.username if obj.editor else ""

    class Meta:
        model = ForumReplyEdit
        fields = ["id", "editor", "editor_name", "old_content", "new_content", "edit_comment", "created_at"]


class ForumUserReputationSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    def get_username(self, obj):
        return obj.user.username if obj.user else ""

    def get_full_name(self, obj):
        return obj.user.get_full_name() if obj.user else ""

    class Meta:
        model = ForumUserReputation
        fields = ["id", "user", "username", "full_name", "score"]


class ForumBadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForumBadge
        fields = "__all__"


class UserBadgeSerializer(serializers.ModelSerializer):
    badge_name = serializers.CharField(source="badge.name", read_only=True)
    badge_icon = serializers.CharField(source="badge.icon", read_only=True)
    badge_description = serializers.CharField(source="badge.description", read_only=True)

    class Meta:
        model = UserBadge
        fields = ["id", "badge", "badge_name", "badge_icon", "badge_description", "earned_at", "user", "company"]
        extra_kwargs = {
            "user": {"read_only": True},
            "company": {"read_only": True},
        }
