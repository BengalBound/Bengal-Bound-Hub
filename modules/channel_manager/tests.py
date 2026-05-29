from django.test import TestCase
from .models import Channel, RatePlan, ChannelRate, AvailabilityBlock, ChannelSyncLog

class ChannelModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Channel, "objects"))

class RatePlanModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(RatePlan, "objects"))

class ChannelRateModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ChannelRate, "objects"))

class AvailabilityBlockModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(AvailabilityBlock, "objects"))

class ChannelSyncLogModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ChannelSyncLog, "objects"))

