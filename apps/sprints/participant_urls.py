from rest_framework.routers import DefaultRouter

from .views import SprintParticipantViewSet

router = DefaultRouter()
router.register("", SprintParticipantViewSet, basename="sprint-participants-root")

urlpatterns = router.urls
