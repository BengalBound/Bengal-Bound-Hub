from django.test import TestCase
from .models import DataSource, DataQuery

class DataSourceModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(DataSource, "objects"))

class DataQueryModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(DataQuery, "objects"))

