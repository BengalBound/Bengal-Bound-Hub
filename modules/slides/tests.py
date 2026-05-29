from django.test import TestCase
from .models import HubPresentation, HubSlide

class HubPresentationModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(HubPresentation, "objects"))

class HubSlideModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(HubSlide, "objects"))

