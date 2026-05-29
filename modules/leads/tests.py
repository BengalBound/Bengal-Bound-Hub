from django.test import TestCase
from .models import LeadSource, Lead, LeadActivity

class LeadSourceModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(LeadSource, "objects"))

class LeadModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Lead, "objects"))

class LeadActivityModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(LeadActivity, "objects"))

