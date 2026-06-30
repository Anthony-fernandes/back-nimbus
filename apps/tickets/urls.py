from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    BusinessHoursViewSet,
    CompanyHolidayViewSet,
    InboundMailboxViewSet,
    SLAPolicyViewSet,
    TicketAutomationRuleViewSet,
    TicketCustomFieldViewSet,
    TicketRelationViewSet,
    TicketReportsView,
    TicketStatusHistoryViewSet,
    TicketTemplateViewSet,
    TicketViewSet,
    inbound_email_webhook,
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
router.register("automation-rules", TicketAutomationRuleViewSet, basename="automation-rules")
router.register("mailboxes", InboundMailboxViewSet, basename="mailboxes")

urlpatterns = router.urls + [
    path("reports/", TicketReportsView.as_view(), name="ticket-reports"),
    path("<uuid:pk>/reopen/", reopen_ticket, name="ticket-reopen"),
    path("inbound/<str:token>/", inbound_email_webhook, name="inbound-email-webhook"),
]
