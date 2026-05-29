from django.test import TestCase
from .models import ProcessMap, ProcessStep, ProcessFlow, ProcessDocument, SimulationRun

class ProcessMapModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ProcessMap, "objects"))

class ProcessStepModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ProcessStep, "objects"))

class ProcessFlowModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ProcessFlow, "objects"))

class ProcessDocumentModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ProcessDocument, "objects"))

class SimulationRunModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(SimulationRun, "objects"))

