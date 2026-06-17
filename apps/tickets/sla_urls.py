from rest_framework.routers import DefaultRouter
from .views import SLAPolicyViewSet

router = DefaultRouter()
router.register(r"", SLAPolicyViewSet, basename="sla-policy")
urlpatterns = router.urls
