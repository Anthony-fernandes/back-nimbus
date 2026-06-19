from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"doubts-questions", views.DoubtsQuestionViewSet, basename="doubts-questions")
router.register(r"doubts-answers", views.DoubtsAnswerViewSet, basename="doubts-answers")

urlpatterns = router.urls
