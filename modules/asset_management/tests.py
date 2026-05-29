from django.test import TestCase
from .models import AssetCategory, Asset, AssetUsageLog, MaintenanceSchedule, WorkOrder, AssetDocument, AssetDepreciation

class AssetCategoryModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(AssetCategory, "objects"))

class AssetModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Asset, "objects"))

class AssetUsageLogModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(AssetUsageLog, "objects"))

class MaintenanceScheduleModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(MaintenanceSchedule, "objects"))

class WorkOrderModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(WorkOrder, "objects"))

class AssetDocumentModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(AssetDocument, "objects"))

class AssetDepreciationModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(AssetDepreciation, "objects"))

