from django.test import TestCase
from .models import SalesChannel, ChannelListing, ChannelSyncLog

class SalesChannelModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(SalesChannel, "objects"))

class ChannelListingModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ChannelListing, "objects"))

class ChannelSyncLogModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ChannelSyncLog, "objects"))

