from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import AdminDashboardStatsView, DashboardDataQueryView, DashboardView, DashboardViewSet

router = DefaultRouter()
router.register(r"dashboards", DashboardViewSet, basename="dashboard")

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("dashboard-data/query/", DashboardDataQueryView.as_view(), name="dashboard-data-query"),
    path("admin-dashboard/stats/", AdminDashboardStatsView.as_view(), name="admin-dashboard-stats"),
    path("", include(router.urls)),
]
