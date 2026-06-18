from rest_framework.routers import DefaultRouter
from .views import TicketCustomFieldViewSet, TicketViewSet, TicketTemplateViewSet

router = DefaultRouter()
router.register("", TicketViewSet, basename="tickets")
router.register("ticket-templates", TicketTemplateViewSet, basename="ticket-template")
router.register("custom-fields", TicketCustomFieldViewSet, basename="ticket-custom-field")
urlpatterns = router.urls
