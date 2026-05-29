from django.test import TestCase
from .models import VideoPitch, PresentationSlide

class VideoPitchModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(VideoPitch, "objects"))

class PresentationSlideModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(PresentationSlide, "objects"))

