from rest_framework.routers import DefaultRouter

from .views import TicketAttachmentViewSet

router = DefaultRouter()
router.register("", TicketAttachmentViewSet, basename="ticket-attachments")
urlpatterns = router.urls
