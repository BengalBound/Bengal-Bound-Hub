from django.test import TestCase
from .models import ServiceBay, JobCard, ServiceItem, JobStatusLog, VehicleServiceHistory

class ServiceBayModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ServiceBay, "objects"))

class JobCardModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(JobCard, "objects"))

class ServiceItemModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ServiceItem, "objects"))

class JobStatusLogModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(JobStatusLog, "objects"))

class VehicleServiceHistoryModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(VehicleServiceHistory, "objects"))

