from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    SprintActivityPlanViewSet,
    SprintParticipantViewSet,
    SprintRetrospectiveViewSet,
    SprintReviewViewSet,
    SprintTicketPlanViewSet,
    SprintViewSet,
    close_sprint,
    sprint_velocity,
    start_sprint,
    sprint_metrics,
    sprint_items,
)

router = DefaultRouter()
router.register("retrospectives", SprintRetrospectiveViewSet, basename="sprint-retrospective")
router.register("reviews", SprintReviewViewSet, basename="sprint-review")
router.register("ticket-plans", SprintTicketPlanViewSet, basename="sprint-ticket-plan")
router.register("sprint-participants", SprintParticipantViewSet, basename="sprint-participants")
router.register("", SprintViewSet, basename="sprints")

urlpatterns = router.urls + [
    path("<uuid:pk>/close/", close_sprint, name="sprint-close"),
    path("<uuid:pk>/start/", start_sprint, name="sprint-start"),
    path("<uuid:pk>/metrics/", sprint_metrics, name="sprint-metrics"),
    path("<uuid:pk>/items/", sprint_items, name="sprint-items"),
    path("velocity/", sprint_velocity, name="sprint-velocity"),
]
