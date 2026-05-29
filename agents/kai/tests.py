from django.test import TestCase
from .models import Pipeline, Incident

class PipelineModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Pipeline, "objects"))

class IncidentModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Incident, "objects"))

