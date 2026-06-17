from rest_framework.routers import DefaultRouter

from .views import ActivityCommentViewSet

router = DefaultRouter()
router.register("", ActivityCommentViewSet, basename="activity-comments")
urlpatterns = router.urls
