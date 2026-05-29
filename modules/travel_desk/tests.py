from django.test import TestCase
from .models import CorporateAccount, TravelPolicy, TravelRequest, TravelExpense

class CorporateAccountModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(CorporateAccount, "objects"))

class TravelPolicyModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(TravelPolicy, "objects"))

class TravelRequestModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(TravelRequest, "objects"))

class TravelExpenseModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(TravelExpense, "objects"))

