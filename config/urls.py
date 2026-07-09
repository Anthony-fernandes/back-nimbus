from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework.permissions import AllowAny
from apps.core.views import health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check),
    # Documentação da API: páginas públicas (o app usa JWT, então o navegador não envia
    # credenciais ao abrir a URL direto). O schema descreve só a estrutura — os endpoints
    # de dados continuam protegidos por IsAuthenticated.
    path("api/schema/", SpectacularAPIView.as_view(permission_classes=[AllowAny]), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema", permission_classes=[AllowAny])),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema", permission_classes=[AllowAny]), name="redoc"),
    path("api/v1/", include("config.api_urls")),
    path("api/", include("config.api_urls")),  # backwards compat
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
