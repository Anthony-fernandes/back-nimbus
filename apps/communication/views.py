from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.viewsets import CompanyScopedModelViewSet
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
from .serializers import (
    ChatConversationSerializer,
    ChatMessageSerializer,
    DoubtsAnswerLikeSerializer,
    DoubtsAnswerSerializer,
    DoubtsQuestionSerializer,
    ForumCategorySerializer,
    ForumReplyLikeSerializer,
    ForumReplySerializer,
    ForumTopicSerializer,
)


class ForumCategoryViewSet(CompanyScopedModelViewSet):
    queryset = ForumCategory.objects.all()
    serializer_class = ForumCategorySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["active"]
    search_fields = ["name", "description"]
    ordering_fields = "__all__"


class ForumTopicViewSet(CompanyScopedModelViewSet):
    queryset = ForumTopic.objects.all()
    serializer_class = ForumTopicSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["category", "is_pinned", "is_locked", "author"]
    search_fields = ["title", "content"]
    ordering_fields = "__all__"

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company, author=self.request.user)

    @action(detail=True, methods=["post"], url_path="mark-best-answer")
    def mark_best_answer(self, request, pk=None):
        topic = self.get_object()
        reply_id = request.data.get("reply_id")
        if not reply_id:
            raise ValidationError("'reply_id' is required.")
        try:
            reply = topic.replies.get(id=reply_id)
        except ForumReply.DoesNotExist:
            raise ValidationError("Reply not found in this topic.")
        # Unmark previous best answer
        topic.replies.filter(is_best_answer=True).update(is_best_answer=False)
        reply.is_best_answer = True
        reply.save(update_fields=["is_best_answer", "updated_at"])
        topic.best_answer = reply
        topic.save(update_fields=["best_answer", "updated_at"])
        return Response(self.get_serializer(topic).data)

    @action(detail=True, methods=["post"], url_path="convert-to-kb")
    def convert_to_kb(self, request, pk=None):
        topic = self.get_object()
        from apps.knowledge.models import KnowledgeArticle, KnowledgeCategory
        category_id = request.data.get("category")
        category = None
        if category_id:
            try:
                category = KnowledgeCategory.objects.get(id=category_id, company=request.user.company)
            except KnowledgeCategory.DoesNotExist:
                pass
        article = KnowledgeArticle.objects.create(
            company=request.user.company,
            title=topic.title,
            slug=f"forum-{str(topic.id)[:8]}",
            content=topic.content,
            summary=topic.content[:300],
            category=category,
            status="DRAFT",
            visibility="INTERNAL",
            author=request.user,
            source_forum_topic=topic,
        )
        from common.audit import record_audit
        record_audit(
            request=request,
            action="CONVERT_FORUM_TO_KB",
            instance=article,
            entity_label=article.title,
        )
        from apps.knowledge.serializers import KnowledgeArticleSerializer
        return Response(KnowledgeArticleSerializer(article).data, status=201)


class ForumReplyViewSet(CompanyScopedModelViewSet):
    queryset = ForumReply.objects.all()
    serializer_class = ForumReplySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["topic", "author", "is_best_answer"]
    search_fields = ["content"]
    ordering_fields = "__all__"
    company_field_name = "topic__company"

    def get_queryset(self):
        user = self.request.user
        company = getattr(user, "company", None)
        if not company:
            return self.queryset.none()
        return self.queryset.filter(topic__company=company)

    def perform_create(self, serializer):
        reply = serializer.save(author=self.request.user)
        topic = reply.topic
        topic.replies_count += 1
        topic.save(update_fields=["replies_count", "updated_at"])

    @action(detail=True, methods=["post"], url_path="toggle-like")
    def toggle_like(self, request, pk=None):
        reply = self.get_object()
        like, created = ForumReplyLike.objects.get_or_create(reply=reply, user=request.user)
        if created:
            reply.likes_count += 1
            reply.save(update_fields=["likes_count", "updated_at"])
        else:
            like.delete()
            reply.likes_count = max(0, reply.likes_count - 1)
            reply.save(update_fields=["likes_count", "updated_at"])
        return Response(self.get_serializer(reply).data)


class ForumReplyLikeViewSet(CompanyScopedModelViewSet):
    queryset = ForumReplyLike.objects.all()
    serializer_class = ForumReplyLikeSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["reply", "user"]
    ordering_fields = "__all__"
    company_field_name = "reply__topic__company"

    def get_queryset(self):
        user = self.request.user
        company = getattr(user, "company", None)
        if not company:
            return self.queryset.none()
        return self.queryset.filter(reply__topic__company=company)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ChatConversationViewSet(CompanyScopedModelViewSet):
    queryset = ChatConversation.objects.all()
    serializer_class = ChatConversationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["created_by"]
    ordering_fields = "__all__"

    def get_queryset(self):
        user = self.request.user
        company = getattr(user, "company", None)
        if not company:
            return self.queryset.none()
        return self.queryset.filter(company=company, participants=user)

    def perform_create(self, serializer):
        user = self.request.user
        conversation = serializer.save(company=user.company, created_by=user)
        conversation.participants.add(user)

    @action(detail=True, methods=["post"], url_path="send-message")
    def send_message(self, request, pk=None):
        conversation = self.get_object()
        serializer = ChatMessageSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        message = serializer.save(conversation=conversation, author=request.user)
        message.read_by.add(request.user)
        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=["last_message_at", "updated_at"])
        return Response(ChatMessageSerializer(message, context=self.get_serializer_context()).data)


class ChatMessageViewSet(CompanyScopedModelViewSet):
    queryset = ChatMessage.objects.all()
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["conversation", "author"]
    search_fields = ["content", "file_name"]
    ordering_fields = "__all__"
    company_field_name = "conversation__company"

    def get_queryset(self):
        user = self.request.user
        company = getattr(user, "company", None)
        if not company:
            return self.queryset.none()
        return self.queryset.filter(conversation__company=company, conversation__participants=user)

    def perform_create(self, serializer):
        user = self.request.user
        message = serializer.save(author=user)
        message.read_by.add(user)
        conversation = message.conversation
        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=["last_message_at", "updated_at"])


class DoubtsQuestionViewSet(CompanyScopedModelViewSet):
    queryset = DoubtsQuestion.objects.all()
    serializer_class = DoubtsQuestionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["status", "author"]
    search_fields = ["title", "content"]
    ordering_fields = "__all__"

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company, author=self.request.user)

    @action(detail=True, methods=["post"], url_path="accept-answer")
    def accept_answer(self, request, pk=None):
        question = self.get_object()
        answer_id = request.data.get("answer_id")
        if not answer_id:
            raise ValidationError("'answer_id' is required.")
        try:
            answer = question.answers.get(id=answer_id)
        except DoubtsAnswer.DoesNotExist:
            raise ValidationError("Answer not found for this question.")
        question.answers.filter(is_accepted=True).update(is_accepted=False)
        answer.is_accepted = True
        answer.save(update_fields=["is_accepted", "updated_at"])
        question.status = "ANSWERED"
        question.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(question).data)

    @action(detail=True, methods=["post"], url_path="convert-to-kb")
    def convert_to_kb(self, request, pk=None):
        question = self.get_object()
        from apps.knowledge.models import KnowledgeArticle, KnowledgeCategory
        category_id = request.data.get("category")
        category = None
        if category_id:
            try:
                category = KnowledgeCategory.objects.get(id=category_id, company=request.user.company)
            except KnowledgeCategory.DoesNotExist:
                pass
        accepted = DoubtsAnswer.objects.filter(question=question, is_accepted=True).first()
        content = question.content
        if accepted:
            content += f"\n\n---\n\n**Resposta aceita:**\n\n{accepted.content}"
        article = KnowledgeArticle.objects.create(
            company=request.user.company,
            title=question.title,
            slug=f"doubts-{str(question.id)[:8]}",
            content=content,
            summary=question.content[:300],
            category=category,
            status="DRAFT",
            visibility="INTERNAL",
            author=request.user,
            source_doubts_question=question,
        )
        from common.audit import record_audit
        record_audit(
            request=request,
            action="CONVERT_DOUBTS_TO_KB",
            instance=article,
            entity_label=article.title,
        )
        from apps.knowledge.serializers import KnowledgeArticleSerializer
        return Response(KnowledgeArticleSerializer(article).data, status=201)


class DoubtsAnswerViewSet(CompanyScopedModelViewSet):
    queryset = DoubtsAnswer.objects.all()
    serializer_class = DoubtsAnswerSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["question", "author", "is_accepted"]
    search_fields = ["content"]
    ordering_fields = "__all__"
    company_field_name = "question__company"

    def get_queryset(self):
        user = self.request.user
        company = getattr(user, "company", None)
        if not company:
            return self.queryset.none()
        return self.queryset.filter(question__company=company)

    def perform_create(self, serializer):
        answer = serializer.save(author=self.request.user)
        question = answer.question
        question.answers_count += 1
        question.save(update_fields=["answers_count", "updated_at"])


class DoubtsAnswerLikeViewSet(CompanyScopedModelViewSet):
    queryset = DoubtsAnswerLike.objects.all()
    serializer_class = DoubtsAnswerLikeSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["answer", "user"]
    ordering_fields = "__all__"
    company_field_name = "answer__question__company"

    def get_queryset(self):
        user = self.request.user
        company = getattr(user, "company", None)
        if not company:
            return self.queryset.none()
        return self.queryset.filter(answer__question__company=company)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
