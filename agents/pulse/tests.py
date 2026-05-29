from django.test import TestCase
from .models import ResearchConfig, ResearchReport

class ResearchConfigModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ResearchConfig, "objects"))

class ResearchReportModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ResearchReport, "objects"))

