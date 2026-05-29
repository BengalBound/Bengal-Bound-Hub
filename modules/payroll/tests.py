from django.test import TestCase
from .models import SalaryStructure, SalaryComponent, PayPeriod, Payslip, PayslipLine

class SalaryStructureModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(SalaryStructure, "objects"))

class SalaryComponentModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(SalaryComponent, "objects"))

class PayPeriodModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(PayPeriod, "objects"))

class PayslipModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Payslip, "objects"))

class PayslipLineModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(PayslipLine, "objects"))

