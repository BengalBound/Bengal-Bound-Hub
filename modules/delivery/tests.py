from django.test import TestCase
from .models import DeliveryZone, Driver, DeliveryOrder, DeliveryRoute

class DeliveryZoneModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(DeliveryZone, "objects"))

class DriverModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Driver, "objects"))

class DeliveryOrderModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(DeliveryOrder, "objects"))

class DeliveryRouteModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(DeliveryRoute, "objects"))

