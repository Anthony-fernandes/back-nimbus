from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import LoginView, MeView, LogoutView

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("me/", MeView.as_view(), name="me"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
