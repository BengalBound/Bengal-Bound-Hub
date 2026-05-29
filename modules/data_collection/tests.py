from django.test import TestCase
from .models import DataForm, FormField, FormResponse, FieldResponse

class DataFormModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(DataForm, "objects"))

class FormFieldModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(FormField, "objects"))

class FormResponseModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(FormResponse, "objects"))

class FieldResponseModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(FieldResponse, "objects"))

