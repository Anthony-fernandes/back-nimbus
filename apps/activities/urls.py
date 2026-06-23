from rest_framework.routers import DefaultRouter
from .views import ActivityDependencyViewSet, ActivityViewSet

router = DefaultRouter()
router.register("", ActivityViewSet, basename="activities")
router.register("dependencies", ActivityDependencyViewSet, basename="activity-dependency")

urlpatterns = router.urls
