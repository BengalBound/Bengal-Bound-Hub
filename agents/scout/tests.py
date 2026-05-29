from django.test import TestCase
from .models import Competitor, CompetitorChange

class CompetitorModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Competitor, "objects"))

class CompetitorChangeModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(CompetitorChange, "objects"))

