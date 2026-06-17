from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.permissions import IsAuthenticated

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(permission_classes=[IsAuthenticated]), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema", permission_classes=[IsAuthenticated])),
    path("api/auth/", include("apps.authentication.urls")),
    path("api/dashboard/", include("apps.dashboard.urls")),
    path("api/companies/", include("apps.companies.urls")),
    path("api/users/", include("apps.users.urls")),
    path("api/permission-blocks/", include("apps.users.permission_block_urls")),
    path("api/departments/", include("apps.users.department_urls")),
    path("api/positions/", include("apps.users.position_urls")),
    path("api/clients/", include("apps.clients.urls")),
    path("api/organizations/", include("apps.clients.urls")),
    path("api/projects/", include("apps.projects.urls")),
    path("api/tickets/", include("apps.tickets.urls")),
    path("api/ticket-categories/", include("apps.tickets.category_urls")),
    path("api/ticket-workflow-statuses/", include("apps.tickets.workflow_status_urls")),
    path("api/ticket-comments/", include("apps.tickets.comment_urls")),
    path("api/ticket-attachments/", include("apps.tickets.attachment_urls")),
    path("api/ticket-approvals/", include("apps.tickets.approval_urls")),
    path("api/sprints/", include("apps.sprints.urls")),
    path("api/sprint-activity-plans/", include("apps.sprints.plan_urls")),
    path("api/activities/", include("apps.activities.urls")),
    path("api/activity-tags/", include("apps.activities.tag_urls")),
    path("api/activity-time-entries/", include("apps.activities.time_entry_urls")),
    path("api/activity-comments/", include("apps.activities.comment_urls")),
    path("api/activity-attachments/", include("apps.activities.attachment_urls")),
    path("api/notifications/", include("apps.notifications.urls")),
    path("api/notification-preferences/", include("apps.notifications.preference_urls")),
    path("api/audit-logs/", include("apps.audit.urls")),
    path("api/knowledge/", include("apps.knowledge.urls")),
    path("api/communication/", include("apps.communication.urls")),
]
