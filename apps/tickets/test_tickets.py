from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.companies.models import Company
from apps.clients.models import Client
from .models import Ticket, TicketCategory

User = get_user_model()


class TicketModelTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Test Co")
        self.client_obj = Client.objects.create(company=self.company, name="Test Client")
        self.user = User.objects.create_user(
            username="tech_user",
            email="tech@test.com",
            password="pass123",
            company=self.company,
            role="TECHNICIAN",
        )

    def _make_ticket(self, title="Test ticket"):
        return Ticket.objects.create(
            company=self.company,
            client=self.client_obj,
            title=title,
            requester_user=self.user,
            status="Aberto",
            priority="Media",
        )

    def test_ticket_code_generated(self):
        """Ticket code is auto-generated on save."""
        t = self._make_ticket()
        self.assertIsNotNone(t.code)
        self.assertTrue(len(t.code) > 0)

    def test_soft_delete(self):
        """Soft delete sets deleted_at without removing from DB."""
        from django.utils import timezone
        t = self._make_ticket("Delete me")
        t_id = t.id
        t.deleted_at = timezone.now()
        t.save()
        self.assertTrue(Ticket.objects.filter(id=t_id).exists())
        self.assertIsNotNone(Ticket.objects.get(id=t_id).deleted_at)

    def test_ticket_str(self):
        """__str__ returns code (auto-generated) or title."""
        t = self._make_ticket("My ticket")
        # code is auto-generated; __str__ returns code if set, otherwise title
        result = str(t)
        self.assertTrue(result == t.code or "My ticket" in result)

    def test_ticket_code_unique(self):
        """Two tickets get different codes."""
        t1 = self._make_ticket("Ticket 1")
        t2 = self._make_ticket("Ticket 2")
        self.assertNotEqual(t1.code, t2.code)

    def test_ticket_default_status(self):
        """Default status is Aberto."""
        t = Ticket.objects.create(
            company=self.company,
            client=self.client_obj,
            title="Defaults test",
            requester_user=self.user,
            priority="Media",
        )
        self.assertEqual(t.status, "Aberto")
