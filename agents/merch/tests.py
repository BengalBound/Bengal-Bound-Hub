from django.test import TestCase
from .models import Store, Product

class StoreModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Store, "objects"))

class ProductModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Product, "objects"))

