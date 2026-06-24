from rest_framework.routers import DefaultRouter

from .views import SprintTicketPlanViewSet

router = DefaultRouter()
router.register("", SprintTicketPlanViewSet, basename="sprint-ticket-plans")
urlpatterns = router.urls
