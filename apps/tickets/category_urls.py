from rest_framework.routers import DefaultRouter

from .views import TicketCategoryViewSet

router = DefaultRouter()
router.register("", TicketCategoryViewSet, basename="ticket-categories")
urlpatterns = router.urls
