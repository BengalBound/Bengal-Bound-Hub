from django.test import TestCase
from .models import Supplier, PurchaseOrder

class SupplierModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Supplier, "objects"))

class PurchaseOrderModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(PurchaseOrder, "objects"))

