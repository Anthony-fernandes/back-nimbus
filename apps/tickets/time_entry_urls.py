from rest_framework.routers import DefaultRouter

from .views import TicketTimeEntryViewSet

router = DefaultRouter()
router.register("", TicketTimeEntryViewSet, basename="ticket-time-entries")
urlpatterns = router.urls
