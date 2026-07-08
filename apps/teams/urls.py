from rest_framework.routers import DefaultRouter
from .views import TeamViewSet, TeamMemberViewSet

router = DefaultRouter()
router.register("members", TeamMemberViewSet, basename="team-members")
router.register("", TeamViewSet, basename="teams")

urlpatterns = router.urls
