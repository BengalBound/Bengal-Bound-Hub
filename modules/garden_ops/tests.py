from django.test import TestCase
from .models import ClientSite, GardenJob, GardenInventoryItem

class ClientSiteModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ClientSite, "objects"))

class GardenJobModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(GardenJob, "objects"))

class GardenInventoryItemModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(GardenInventoryItem, "objects"))

