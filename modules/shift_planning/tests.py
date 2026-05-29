from django.test import TestCase
from .models import ShiftTemplate, SchedulePeriod, Shift, ShiftSwapRequest

class ShiftTemplateModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ShiftTemplate, "objects"))

class SchedulePeriodModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(SchedulePeriod, "objects"))

class ShiftModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Shift, "objects"))

class ShiftSwapRequestModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ShiftSwapRequest, "objects"))

