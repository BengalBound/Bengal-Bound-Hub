from django.test import TestCase
from .models import BudgetPeriod, Budget, BudgetLine

class BudgetPeriodModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(BudgetPeriod, "objects"))

class BudgetModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Budget, "objects"))

class BudgetLineModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(BudgetLine, "objects"))

