from rest_framework.routers import DefaultRouter
from .views import ActivityViewSet, ActivityDependencyViewSet, ActivityCustomFieldViewSet, ActivityCustomValueViewSet

router = DefaultRouter()
router.register("", ActivityViewSet, basename="activities")
router.register("dependencies", ActivityDependencyViewSet, basename="activity-dependency")
router.register("custom-fields", ActivityCustomFieldViewSet, basename="activity-custom-field")
router.register("custom-values", ActivityCustomValueViewSet, basename="activity-custom-value")

urlpatterns = router.urls
