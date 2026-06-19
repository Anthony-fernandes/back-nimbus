from rest_framework import serializers
from .models import ForumCategory, ForumTopic, ForumReply


class ForumCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ForumCategory
        fields = "__all__"
        extra_kwargs = {"company": {"required": False, "read_only": True}}


class ForumTopicSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    reply_count = serializers.SerializerMethodField()

    class Meta:
        model = ForumTopic
        fields = "__all__"
        extra_kwargs = {
            "company": {"required": False, "write_only": True},
            "author": {"required": False, "read_only": True},
            "views": {"read_only": True},
        }

    def get_author_name(self, obj):
        if obj.author:
            return getattr(obj.author, "full_name_or_username", str(obj.author))
        return None

    def get_reply_count(self, obj):
        return obj.replies.count()


class ForumReplySerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = ForumReply
        fields = "__all__"
        extra_kwargs = {
            "author": {"required": False, "read_only": True},
        }

    def get_author_name(self, obj):
        if obj.author:
            return getattr(obj.author, "full_name_or_username", str(obj.author))
        return None
