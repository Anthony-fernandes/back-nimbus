from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, ProjectCustomFieldViewSet, ProjectCustomValueViewSet

router = DefaultRouter()
router.register("", ProjectViewSet, basename="projects")
router.register("custom-fields", ProjectCustomFieldViewSet, basename="project-custom-field")
router.register("custom-values", ProjectCustomValueViewSet, basename="project-custom-value")

urlpatterns = router.urls
