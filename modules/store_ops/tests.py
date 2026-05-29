from django.test import TestCase
from .models import RetailStore, StoreReport, StoreTask

class RetailStoreModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(RetailStore, "objects"))

class StoreReportModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(StoreReport, "objects"))

class StoreTaskModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(StoreTask, "objects"))

