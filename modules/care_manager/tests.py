from django.test import TestCase
from .models import CareClient, CarePlan, CareSession, StaffRota, ComplianceDocument

class CareClientModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(CareClient, "objects"))

class CarePlanModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(CarePlan, "objects"))

class CareSessionModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(CareSession, "objects"))

class StaffRotaModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(StaffRota, "objects"))

class ComplianceDocumentModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ComplianceDocument, "objects"))

