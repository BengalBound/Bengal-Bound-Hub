from django.test import TestCase
from .models import DataSet, AnalyticsChart, DataStudioReport

class DataSetModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(DataSet, "objects"))

class AnalyticsChartModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(AnalyticsChart, "objects"))

class DataStudioReportModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(DataStudioReport, "objects"))

