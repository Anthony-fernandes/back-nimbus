from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    BusinessHoursViewSet,
    CompanyHolidayViewSet,
    SLAPolicyViewSet,
    TicketCustomFieldViewSet,
    TicketRelationViewSet,
    TicketReportsView,
    TicketStatusHistoryViewSet,
    TicketTemplateViewSet,
    TicketViewSet,
    reopen_ticket,
)

router = DefaultRouter()
router.register("", TicketViewSet, basename="tickets")
router.register("ticket-templates", TicketTemplateViewSet, basename="ticket-template")
router.register("custom-fields", TicketCustomFieldViewSet, basename="ticket-custom-field")
router.register("sla-policies", SLAPolicyViewSet, basename="sla-policy")
router.register("status-history", TicketStatusHistoryViewSet, basename="ticket-status-history")
router.register("relations", TicketRelationViewSet, basename="ticket-relation")
router.register("business-hours", BusinessHoursViewSet, basename="business-hours")
router.register("holidays", CompanyHolidayViewSet, basename="company-holiday")

urlpatterns = router.urls + [
    path("reports/", TicketReportsView.as_view(), name="ticket-reports"),
    path("<uuid:pk>/reopen/", reopen_ticket, name="ticket-reopen"),
]
