from rest_framework.routers import DefaultRouter
from apps.companies.views import SuperAdminCompanyViewSet

router = DefaultRouter()
router.register("companies", SuperAdminCompanyViewSet, basename="superadmin-companies")
urlpatterns = router.urls
