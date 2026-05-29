from django.test import TestCase
from .models import Deal, DealDocument, DealNote, DealMilestone

class DealModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Deal, "objects"))

class DealDocumentModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(DealDocument, "objects"))

class DealNoteModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(DealNote, "objects"))

class DealMilestoneModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(DealMilestone, "objects"))

