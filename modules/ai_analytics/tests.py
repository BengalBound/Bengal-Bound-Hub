from django.test import TestCase
from .models import AnalyticsDataset, AIInsight, KPIMetric

class AnalyticsDatasetModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(AnalyticsDataset, "objects"))

class AIInsightModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(AIInsight, "objects"))

class KPIMetricModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(KPIMetric, "objects"))

