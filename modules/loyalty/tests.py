from django.test import TestCase
from .models import LoyaltyProgram, LoyaltyTier, LoyaltyMember, PointTransaction

class LoyaltyProgramModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(LoyaltyProgram, "objects"))

class LoyaltyTierModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(LoyaltyTier, "objects"))

class LoyaltyMemberModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(LoyaltyMember, "objects"))

class PointTransactionModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(PointTransaction, "objects"))

