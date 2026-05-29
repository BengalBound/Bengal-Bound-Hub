from django.test import TestCase
from .models import InvoiceClient, Invoice, InvoiceLine, Payment

class InvoiceClientModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(InvoiceClient, "objects"))

class InvoiceModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Invoice, "objects"))

class InvoiceLineModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(InvoiceLine, "objects"))

class PaymentModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Payment, "objects"))

