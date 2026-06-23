from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    ChatConversationViewSet,
    ChatMessageViewSet,
    ContentFlagViewSet,
    DoubtsAnswerLikeViewSet,
    DoubtsAnswerViewSet,
    DoubtsQuestionViewSet,
    ForumBadgeViewSet,
    ForumCategoryViewSet,
    ForumCommentViewSet,
    ForumReplyEditViewSet,
    ForumReplyLikeViewSet,
    ForumReplyViewSet,
    ForumTopicEditViewSet,
    ForumTopicViewSet,
    ForumUserProfileView,
    ForumUserReputationViewSet,
    UserBadgeViewSet,
)

router = DefaultRouter()
router.register(r"forum-categories", ForumCategoryViewSet, basename="forum-category")
router.register(r"forum-topics", ForumTopicViewSet, basename="forum-topic")
router.register(r"forum-replies", ForumReplyViewSet, basename="forum-reply")
router.register(r"forum-reply-likes", ForumReplyLikeViewSet, basename="forum-reply-like")
router.register(r"forum-comments", ForumCommentViewSet, basename="forum-comment")
router.register(r"forum-topic-edits", ForumTopicEditViewSet, basename="forum-topic-edit")
router.register(r"forum-reply-edits", ForumReplyEditViewSet, basename="forum-reply-edit")
router.register(r"forum-reputation", ForumUserReputationViewSet, basename="forum-reputation")
router.register(r"flags", ContentFlagViewSet, basename="flag")
router.register(r"chat-conversations", ChatConversationViewSet, basename="chat-conversation")
router.register(r"chat-messages", ChatMessageViewSet, basename="chat-message")
router.register(r"doubts-questions", DoubtsQuestionViewSet, basename="doubts-question")
router.register(r"doubts-answers", DoubtsAnswerViewSet, basename="doubts-answer")
router.register(r"doubts-answer-likes", DoubtsAnswerLikeViewSet, basename="doubts-answer-like")
router.register(r"forum-badges", ForumBadgeViewSet, basename="forum-badge")
router.register(r"user-badges", UserBadgeViewSet, basename="user-badge")

urlpatterns = router.urls + [
    path("forum-users/<str:user_id>/profile/", ForumUserProfileView.as_view(), name="forum-user-profile"),
]
