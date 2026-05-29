from django.test import TestCase
from .models import ExpenseCategory, ExpenseClaim, ExpenseItem

class ExpenseCategoryModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ExpenseCategory, "objects"))

class ExpenseClaimModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ExpenseClaim, "objects"))

class ExpenseItemModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ExpenseItem, "objects"))

