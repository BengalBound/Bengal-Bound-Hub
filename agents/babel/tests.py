from django.test import TestCase
from .models import TranslationJob, TranslationOutput

class TranslationJobModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(TranslationJob, "objects"))

class TranslationOutputModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(TranslationOutput, "objects"))

