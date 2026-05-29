from django.test import TestCase
from .models import InspectionTemplate, VehicleInspection, InspectionItem

class InspectionTemplateModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(InspectionTemplate, "objects"))

class VehicleInspectionModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(VehicleInspection, "objects"))

class InspectionItemModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(InspectionItem, "objects"))

