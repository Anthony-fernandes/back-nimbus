from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import LoginView, MeView, LogoutView, ChangePasswordView, PasswordResetView, PasswordResetConfirmView
from .mfa_views import MFASetupView, MFASetupConfirmView, MFADisableView, MFAVerifyLoginView, MFAStatusView

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("me/", MeView.as_view(), name="me"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("password-reset/", PasswordResetView.as_view(), name="password-reset"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("mfa/setup/", MFASetupView.as_view(), name="mfa-setup"),
    path("mfa/setup/confirm/", MFASetupConfirmView.as_view(), name="mfa-setup-confirm"),
    path("mfa/disable/", MFADisableView.as_view(), name="mfa-disable"),
    path("mfa/verify-login/", MFAVerifyLoginView.as_view(), name="mfa-verify-login"),
    path("mfa/status/", MFAStatusView.as_view(), name="mfa-status"),
]
