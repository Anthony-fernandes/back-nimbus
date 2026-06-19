from rest_framework import serializers
from .models import DoubtsQuestion, DoubtsAnswer


class DoubtsQuestionSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    answer_count = serializers.SerializerMethodField()

    class Meta:
        model = DoubtsQuestion
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

    def get_answer_count(self, obj):
        return obj.answers.count()


class DoubtsAnswerSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = DoubtsAnswer
        fields = "__all__"
        extra_kwargs = {
            "author": {"required": False, "read_only": True},
        }

    def get_author_name(self, obj):
        if obj.author:
            return getattr(obj.author, "full_name_or_username", str(obj.author))
        return None
