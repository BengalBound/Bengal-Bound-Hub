from django.test import TestCase
from .models import Store, StoreCategory, StoreProduct, Order, OrderItem

class StoreModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Store, "objects"))

class StoreCategoryModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(StoreCategory, "objects"))

class StoreProductModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(StoreProduct, "objects"))

class OrderModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Order, "objects"))

class OrderItemModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(OrderItem, "objects"))

