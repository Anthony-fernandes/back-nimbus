from rest_framework.routers import DefaultRouter

from .views import TicketApprovalViewSet

router = DefaultRouter()
router.register("", TicketApprovalViewSet, basename="ticket-approvals")
urlpatterns = router.urls
