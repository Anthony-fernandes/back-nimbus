from rest_framework.routers import DefaultRouter
from .views import TeamViewSet, TeamMemberViewSet

router = DefaultRouter()
router.register("", TeamViewSet, basename="teams")
router.register("members", TeamMemberViewSet, basename="team-members")

urlpatterns = router.urls
