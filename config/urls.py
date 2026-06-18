from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework.permissions import IsAuthenticated
from apps.core.views import health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check),
    path("api/schema/", SpectacularAPIView.as_view(permission_classes=[IsAuthenticated]), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema", permission_classes=[IsAuthenticated])),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/v1/", include("config.api_urls")),
    path("api/", include("config.api_urls")),  # backwards compat
]
