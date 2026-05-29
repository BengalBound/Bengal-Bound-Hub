from django.test import TestCase
from .models import ReportDefinition, ReportRun, Dashboard

class ReportDefinitionModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ReportDefinition, "objects"))

class ReportRunModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ReportRun, "objects"))

class DashboardModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Dashboard, "objects"))

