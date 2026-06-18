from django.test import TestCase
from django.core.cache import cache
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.companies.models import Company

User = get_user_model()


class AuthenticationTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Auth Test Co")
        self.user = User.objects.create_user(
            username="authuser",
            email="auth@test.com",
            password="securepass123",
            company=self.company,
            role="ADMIN",
        )
        self.client = APIClient()

    def test_login_valid_credentials_returns_tokens(self):
        """Login with valid credentials returns JWT access and refresh tokens."""
        resp = self.client.post("/api/auth/login/", {
            "username": "authuser",
            "password": "securepass123",
        }, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_login_wrong_password_returns_401(self):
        """Login with wrong password returns 401."""
        resp = self.client.post("/api/auth/login/", {
            "username": "authuser",
            "password": "wrongpassword",
        }, format="json")
        self.assertEqual(resp.status_code, 401)

    def test_login_mfa_enabled_returns_mfa_required(self):
        """Login with MFA enabled returns mfa_required: true and mfa_token."""
        self.user.mfa_enabled = True
        self.user.save()
        resp = self.client.post("/api/auth/login/", {
            "username": "authuser",
            "password": "securepass123",
        }, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data.get("mfa_required"))
        self.assertIn("mfa_token", resp.data)

    def test_protected_endpoint_without_token_returns_401(self):
        """Accessing a protected endpoint without a token returns 401."""
        resp = self.client.get("/api/auth/me/")
        self.assertEqual(resp.status_code, 401)
