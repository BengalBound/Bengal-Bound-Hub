from django.test import TestCase
from .models import Employee, PayrollRun

class EmployeeModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Employee, "objects"))

class PayrollRunModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(PayrollRun, "objects"))

