from django.test import TestCase
from .models import Asset, MaintenanceSchedule, WorkOrder

class AssetModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Asset, "objects"))

class MaintenanceScheduleModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(MaintenanceSchedule, "objects"))

class WorkOrderModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(WorkOrder, "objects"))

