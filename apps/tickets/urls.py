from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import TicketCustomFieldViewSet, TicketViewSet, TicketTemplateViewSet, SLAPolicyViewSet, TicketReportsView

router = DefaultRouter()
router.register("", TicketViewSet, basename="tickets")
router.register("ticket-templates", TicketTemplateViewSet, basename="ticket-template")
router.register("custom-fields", TicketCustomFieldViewSet, basename="ticket-custom-field")
router.register("sla-policies", SLAPolicyViewSet, basename="sla-policy")

urlpatterns = router.urls + [
    path("reports/", TicketReportsView.as_view(), name="ticket-reports"),
]
