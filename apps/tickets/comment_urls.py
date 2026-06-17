from rest_framework.routers import DefaultRouter

from .views import TicketCommentViewSet

router = DefaultRouter()
router.register("", TicketCommentViewSet, basename="ticket-comments")
urlpatterns = router.urls
