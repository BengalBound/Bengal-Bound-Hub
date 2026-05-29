from django.test import TestCase
from .models import Vendor, RFQ

class VendorModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Vendor, "objects"))

class RFQModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(RFQ, "objects"))

