from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.companies.models import Company
from apps.users.models import User
from apps.notifications.models import Notification
from apps.notifications.services import notify


def make_token(user):
    return str(RefreshToken.for_user(user).access_token)


class NotifyServiceTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Notify Co")
        self.recipient = User.objects.create_user(
            username="recipient", password="pass123", company=self.company, role="ADMIN"
        )
        self.actor = User.objects.create_user(
            username="actor", password="pass123", company=self.company, role="TECHNICIAN"
        )

    def test_notify_creates_notification(self):
        notify(
            self.recipient,
            title="Test Notification",
            event="ticket.created",
            message="A ticket was created",
            actor=self.actor,
        )
        self.assertTrue(
            Notification.objects.filter(recipient=self.recipient, title="Test Notification").exists()
        )

    def test_notify_self_does_not_create(self):
        """Actor notifying themselves should be skipped."""
        count_before = Notification.objects.filter(recipient=self.actor).count()
        notify(
            self.actor,
            title="Self notification",
            actor=self.actor,
        )
        self.assertEqual(Notification.objects.filter(recipient=self.actor).count(), count_before)

    def test_notify_sets_category_from_event(self):
        notify(
            self.recipient,
            title="Project notify",
            event="project.created",
            actor=self.actor,
        )
        n = Notification.objects.get(recipient=self.recipient, event="project.created")
        self.assertEqual(n.category, "Projetos")


class UnreadCountTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Count Co")
        self.user = User.objects.create_user(
            username="countuser", password="pass123", company=self.company, role="ADMIN"
        )
        self.other = User.objects.create_user(
            username="other", password="pass123", company=self.company, role="TECHNICIAN"
        )
        self.api_client = APIClient()
        self.api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {make_token(self.user)}")

    def _make_notification(self, user, is_read=False):
        return Notification.objects.create(
            company=self.company,
            recipient=user,
            title="Test",
            is_read=is_read,
        )

    def test_unread_count_returns_correct_number(self):
        self._make_notification(self.user, is_read=False)
        self._make_notification(self.user, is_read=False)
        self._make_notification(self.user, is_read=True)
        resp = self.api_client.get("/api/notifications/unread-count/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 2)

    def test_unread_count_excludes_other_user(self):
        self._make_notification(self.other, is_read=False)
        resp = self.api_client.get("/api/notifications/unread-count/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 0)


class MarkAsReadTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Read Co")
        self.user = User.objects.create_user(
            username="readuser", password="pass123", company=self.company, role="ADMIN"
        )
        self.api_client = APIClient()
        self.api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {make_token(self.user)}")

    def test_mark_as_read(self):
        n = Notification.objects.create(
            company=self.company, recipient=self.user, title="Unread", is_read=False
        )
        resp = self.api_client.post(f"/api/notifications/{n.id}/read/")
        self.assertEqual(resp.status_code, 200)
        n.refresh_from_db()
        self.assertTrue(n.is_read)

    def test_read_all(self):
        Notification.objects.create(company=self.company, recipient=self.user, title="A", is_read=False)
        Notification.objects.create(company=self.company, recipient=self.user, title="B", is_read=False)
        resp = self.api_client.post("/api/notifications/read-all/")
        self.assertEqual(resp.status_code, 200)
        unread = Notification.objects.filter(recipient=self.user, is_read=False).count()
        self.assertEqual(unread, 0)
