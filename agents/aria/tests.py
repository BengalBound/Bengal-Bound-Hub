from django.test import TestCase
from .models import SupportTicket, TicketResponse

class SupportTicketModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(SupportTicket, "objects"))

class TicketResponseModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(TicketResponse, "objects"))

