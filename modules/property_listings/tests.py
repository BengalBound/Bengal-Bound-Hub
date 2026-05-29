from django.test import TestCase
from .models import Property, PropertyShowing

class PropertyModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Property, "objects"))

class PropertyShowingModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(PropertyShowing, "objects"))

