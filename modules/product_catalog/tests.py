from django.test import TestCase
from .models import ProductCatalog, CatalogCategory, CatalogItem

class ProductCatalogModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ProductCatalog, "objects"))

class CatalogCategoryModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(CatalogCategory, "objects"))

class CatalogItemModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(CatalogItem, "objects"))

