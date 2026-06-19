from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"forum-categories", views.ForumCategoryViewSet, basename="forum-categories")
router.register(r"forum-topics", views.ForumTopicViewSet, basename="forum-topics")
router.register(r"forum-replies", views.ForumReplyViewSet, basename="forum-replies")

urlpatterns = router.urls
