from django.test import TestCase
from .models import CommissionRule, CommissionEntry

class CommissionRuleModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(CommissionRule, "objects"))

class CommissionEntryModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(CommissionEntry, "objects"))

