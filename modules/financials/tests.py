from django.test import TestCase
from .models import OperationalReport, UserExpense

class OperationalReportModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(OperationalReport, "objects"))

class UserExpenseModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(UserExpense, "objects"))

