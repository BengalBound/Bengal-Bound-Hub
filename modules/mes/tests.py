from django.test import TestCase
from .models import WorkCenter, Routing, RoutingStation, ProductionOrder, ProductionLog, StationTrackingLog, QualityCheck, DowntimeRecord, OEESnapshot, HardwareScanner, ScannerEventLog, FootwearProductionSchedule, ProductionDayEntry

class WorkCenterModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(WorkCenter, "objects"))

class RoutingModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Routing, "objects"))

class RoutingStationModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(RoutingStation, "objects"))

class ProductionOrderModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ProductionOrder, "objects"))

class ProductionLogModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ProductionLog, "objects"))

class StationTrackingLogModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(StationTrackingLog, "objects"))

class QualityCheckModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(QualityCheck, "objects"))

class DowntimeRecordModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(DowntimeRecord, "objects"))

class OEESnapshotModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(OEESnapshot, "objects"))

class HardwareScannerModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(HardwareScanner, "objects"))

class ScannerEventLogModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ScannerEventLog, "objects"))

class FootwearProductionScheduleModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(FootwearProductionSchedule, "objects"))

class ProductionDayEntryModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ProductionDayEntry, "objects"))

