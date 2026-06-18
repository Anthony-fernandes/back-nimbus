from rest_framework.routers import DefaultRouter
from .views import TicketViewSet, TicketTemplateViewSet

router = DefaultRouter()
router.register("", TicketViewSet, basename="tickets")
router.register("ticket-templates", TicketTemplateViewSet, basename="ticket-template")
urlpatterns = router.urls
