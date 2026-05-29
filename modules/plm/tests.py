from django.test import TestCase
from .models import Product, BillOfMaterials, BOMLine, EngineeringChangeOrder, ProductDocument, ProductStage, ShoeArticle, SampleOrder, SampleBuyerComment

class ProductModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Product, "objects"))

class BillOfMaterialsModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(BillOfMaterials, "objects"))

class BOMLineModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(BOMLine, "objects"))

class EngineeringChangeOrderModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(EngineeringChangeOrder, "objects"))

class ProductDocumentModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ProductDocument, "objects"))

class ProductStageModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ProductStage, "objects"))

class ShoeArticleModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ShoeArticle, "objects"))

class SampleOrderModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(SampleOrder, "objects"))

class SampleBuyerCommentModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(SampleBuyerComment, "objects"))

