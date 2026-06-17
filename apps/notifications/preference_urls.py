from django.urls import path

from .views import NotificationPreferenceView

urlpatterns = [
    path("me/", NotificationPreferenceView.as_view(), name="notification-preference-me"),
]
