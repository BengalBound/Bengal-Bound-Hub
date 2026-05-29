from django.test import TestCase
from .models import POSConfig, POSSession, POSOrder, POSOrderItem

class POSConfigModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(POSConfig, "objects"))

class POSSessionModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(POSSession, "objects"))

class POSOrderModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(POSOrder, "objects"))

class POSOrderItemModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(POSOrderItem, "objects"))

