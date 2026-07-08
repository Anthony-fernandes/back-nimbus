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
)

router = DefaultRouter()
router.register("", SprintViewSet, basename="sprints")
router.register("retrospectives", SprintRetrospectiveViewSet, basename="sprint-retrospective")
router.register("reviews", SprintReviewViewSet, basename="sprint-review")
router.register("ticket-plans", SprintTicketPlanViewSet, basename="sprint-ticket-plan")
router.register("sprint-participants", SprintParticipantViewSet, basename="sprint-participants")

urlpatterns = router.urls + [
    path("<uuid:pk>/close/", close_sprint, name="sprint-close"),
    path("<uuid:pk>/start/", start_sprint, name="sprint-start"),
    path("<uuid:pk>/metrics/", sprint_metrics, name="sprint-metrics"),
    path("velocity/", sprint_velocity, name="sprint-velocity"),
]
