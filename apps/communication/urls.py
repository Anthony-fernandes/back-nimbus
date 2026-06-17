from rest_framework.routers import DefaultRouter
from .views import (
    ChatConversationViewSet,
    ChatMessageViewSet,
    DoubtsAnswerLikeViewSet,
    DoubtsAnswerViewSet,
    DoubtsQuestionViewSet,
    ForumCategoryViewSet,
    ForumReplyLikeViewSet,
    ForumReplyViewSet,
    ForumTopicViewSet,
)

router = DefaultRouter()
router.register(r"forum-categories", ForumCategoryViewSet, basename="forum-category")
router.register(r"forum-topics", ForumTopicViewSet, basename="forum-topic")
router.register(r"forum-replies", ForumReplyViewSet, basename="forum-reply")
router.register(r"forum-reply-likes", ForumReplyLikeViewSet, basename="forum-reply-like")
router.register(r"chat-conversations", ChatConversationViewSet, basename="chat-conversation")
router.register(r"chat-messages", ChatMessageViewSet, basename="chat-message")
router.register(r"doubts-questions", DoubtsQuestionViewSet, basename="doubts-question")
router.register(r"doubts-answers", DoubtsAnswerViewSet, basename="doubts-answer")
router.register(r"doubts-answer-likes", DoubtsAnswerLikeViewSet, basename="doubts-answer-like")

urlpatterns = router.urls
