from django.test import TestCase
from .models import Carrier, Route, Shipment, ShipmentEvent, FreightQuote

class CarrierModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Carrier, "objects"))

class RouteModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Route, "objects"))

class ShipmentModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Shipment, "objects"))

class ShipmentEventModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ShipmentEvent, "objects"))

class FreightQuoteModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(FreightQuote, "objects"))

