from django.test import TestCase
from .models import BrandMention, PressRelease

class BrandMentionModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(BrandMention, "objects"))

class PressReleaseModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(PressRelease, "objects"))

