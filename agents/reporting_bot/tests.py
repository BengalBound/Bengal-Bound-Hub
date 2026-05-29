from django.test import TestCase
from .models import ReportConfig, Report

class ReportConfigModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ReportConfig, "objects"))

class ReportModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Report, "objects"))

