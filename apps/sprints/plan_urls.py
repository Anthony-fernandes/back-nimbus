from rest_framework.routers import DefaultRouter

from .views import SprintActivityPlanViewSet

router = DefaultRouter()
router.register("", SprintActivityPlanViewSet, basename="sprint-activity-plans")
urlpatterns = router.urls
