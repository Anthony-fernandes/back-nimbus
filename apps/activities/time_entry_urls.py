from rest_framework.routers import DefaultRouter

from .views import ActivityTimeEntryViewSet

router = DefaultRouter()
router.register("", ActivityTimeEntryViewSet, basename="activity-time-entries")
urlpatterns = router.urls
