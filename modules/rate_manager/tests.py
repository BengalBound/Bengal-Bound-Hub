from django.test import TestCase
from .models import Season, RoomRateBase, YieldRule, RateRestriction, SpecialOffer

class SeasonModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Season, "objects"))

class RoomRateBaseModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(RoomRateBase, "objects"))

class YieldRuleModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(YieldRule, "objects"))

class RateRestrictionModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(RateRestriction, "objects"))

class SpecialOfferModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(SpecialOffer, "objects"))

