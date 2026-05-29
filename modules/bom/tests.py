from django.test import TestCase
from .models import BillOfMaterials, BOMComponent, WorkCenter, BOMOperation, ShoeArticleBOM, ShoeColorwayEntry, ShoeBOMLine

class BillOfMaterialsModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(BillOfMaterials, "objects"))

class BOMComponentModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(BOMComponent, "objects"))

class WorkCenterModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(WorkCenter, "objects"))

class BOMOperationModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(BOMOperation, "objects"))

class ShoeArticleBOMModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ShoeArticleBOM, "objects"))

class ShoeColorwayEntryModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ShoeColorwayEntry, "objects"))

class ShoeBOMLineModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ShoeBOMLine, "objects"))

