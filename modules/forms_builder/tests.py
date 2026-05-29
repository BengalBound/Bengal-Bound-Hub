from django.test import TestCase
from .models import HubForm, HubFormField, HubFormResponse

class HubFormModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(HubForm, "objects"))

class HubFormFieldModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(HubFormField, "objects"))

class HubFormResponseModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(HubFormResponse, "objects"))

