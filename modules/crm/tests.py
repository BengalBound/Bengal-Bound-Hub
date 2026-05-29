from django.test import TestCase
from .models import Contact, Pipeline, Stage, Deal, Activity

class ContactModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Contact, "objects"))

class PipelineModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Pipeline, "objects"))

class StageModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Stage, "objects"))

class DealModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Deal, "objects"))

class ActivityModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Activity, "objects"))

