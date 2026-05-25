from rest_framework.routers import DefaultRouter
from .views import SprintViewSet

router = DefaultRouter()
router.register("", SprintViewSet, basename="sprints")
urlpatterns = router.urls
