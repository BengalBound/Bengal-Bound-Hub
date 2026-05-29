from django.test import TestCase
from .models import WarehouseZone, StorageBin, InboundReceipt, InboundReceiptLine, PickList, PickListItem

class WarehouseZoneModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(WarehouseZone, "objects"))

class StorageBinModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(StorageBin, "objects"))

class InboundReceiptModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(InboundReceipt, "objects"))

class InboundReceiptLineModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(InboundReceiptLine, "objects"))

class PickListModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(PickList, "objects"))

class PickListItemModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(PickListItem, "objects"))

