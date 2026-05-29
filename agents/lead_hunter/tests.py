from django.test import TestCase
from .models import Prospect, OutreachSequence

class ProspectModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Prospect, "objects"))

class OutreachSequenceModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(OutreachSequence, "objects"))

