from django.test import TestCase
from .models import StoreLayout, PlanogramSection, PlanogramSlot

class StoreLayoutModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(StoreLayout, "objects"))

class PlanogramSectionModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(PlanogramSection, "objects"))

class PlanogramSlotModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(PlanogramSlot, "objects"))

