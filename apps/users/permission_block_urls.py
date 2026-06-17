from rest_framework.routers import DefaultRouter

from .views import PermissionBlockViewSet


router = DefaultRouter()
router.register("", PermissionBlockViewSet, basename="permission-blocks")
urlpatterns = router.urls
