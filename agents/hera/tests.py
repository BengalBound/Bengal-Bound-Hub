from django.test import TestCase
from .models import PolicyQuery, OnboardingTask

class PolicyQueryModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(PolicyQuery, "objects"))

class OnboardingTaskModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(OnboardingTask, "objects"))

