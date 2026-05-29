from django.test import TestCase
from .models import ManufacturingOrder, WorkOrderOperation, MaterialConsumption, ProductionKPISnapshot

class ManufacturingOrderModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ManufacturingOrder, "objects"))

class WorkOrderOperationModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(WorkOrderOperation, "objects"))

class MaterialConsumptionModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(MaterialConsumption, "objects"))

class ProductionKPISnapshotModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ProductionKPISnapshot, "objects"))

