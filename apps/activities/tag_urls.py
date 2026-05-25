from rest_framework.routers import DefaultRouter

from .views import ActivityTagViewSet

router = DefaultRouter()
router.register("", ActivityTagViewSet, basename="activity-tags")
urlpatterns = router.urls
