from django.test import TestCase
from .models import ListingFlyer, DripCampaign, DripMessage, SocialPost

class ListingFlyerModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ListingFlyer, "objects"))

class DripCampaignModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(DripCampaign, "objects"))

class DripMessageModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(DripMessage, "objects"))

class SocialPostModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(SocialPost, "objects"))

