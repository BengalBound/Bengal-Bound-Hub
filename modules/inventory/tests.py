from django.test import TestCase
from .models import ProductCategory, UnitOfMeasure, UoMConversion, Warehouse, Product, ProductLot, StockLevel, StockMovement, LabelTemplate, PackagingLabel

class ProductCategoryModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ProductCategory, "objects"))

class UnitOfMeasureModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(UnitOfMeasure, "objects"))

class UoMConversionModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(UoMConversion, "objects"))

class WarehouseModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Warehouse, "objects"))

class ProductModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Product, "objects"))

class ProductLotModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ProductLot, "objects"))

class StockLevelModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(StockLevel, "objects"))

class StockMovementModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(StockMovement, "objects"))

class LabelTemplateModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(LabelTemplate, "objects"))

class PackagingLabelModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(PackagingLabel, "objects"))

