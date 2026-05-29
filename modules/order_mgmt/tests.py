from django.test import TestCase
from .models import Vendor, PurchaseOrder, PurchaseOrderLine

class VendorModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Vendor, "objects"))

class PurchaseOrderModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(PurchaseOrder, "objects"))

class PurchaseOrderLineModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(PurchaseOrderLine, "objects"))

