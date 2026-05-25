from rest_framework.routers import DefaultRouter

from .views import TicketWorkflowStatusViewSet

router = DefaultRouter()
router.register("", TicketWorkflowStatusViewSet, basename="ticket-workflow-statuses")
urlpatterns = router.urls
