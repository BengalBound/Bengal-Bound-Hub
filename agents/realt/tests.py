from django.test import TestCase
from .models import Property, Lead

class PropertyModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Property, "objects"))

class LeadModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Lead, "objects"))

