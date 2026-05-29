from django.test import TestCase
from .models import FeedbackSurvey, InsightTheme

class FeedbackSurveyModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(FeedbackSurvey, "objects"))

class InsightThemeModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(InsightTheme, "objects"))

