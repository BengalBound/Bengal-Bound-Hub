from django.test import TestCase
from .models import CustomDashboard, DashboardWidget, DashboardSharedUser

class CustomDashboardModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(CustomDashboard, "objects"))

class DashboardWidgetModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(DashboardWidget, "objects"))

class DashboardSharedUserModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(DashboardSharedUser, "objects"))

