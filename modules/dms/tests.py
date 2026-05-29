from django.test import TestCase
from .models import VehicleStock, VehiclePhoto, VehicleDeal, TradeIn, DealNote

class VehicleStockModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(VehicleStock, "objects"))

class VehiclePhotoModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(VehiclePhoto, "objects"))

class VehicleDealModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(VehicleDeal, "objects"))

class TradeInModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(TradeIn, "objects"))

class DealNoteModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(DealNote, "objects"))

