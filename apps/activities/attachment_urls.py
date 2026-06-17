from rest_framework.routers import DefaultRouter

from .views import ActivityAttachmentViewSet

router = DefaultRouter()
router.register("", ActivityAttachmentViewSet, basename="activity-attachments")
urlpatterns = router.urls
