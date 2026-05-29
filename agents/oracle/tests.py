from django.test import TestCase
from .models import Website, SEOIssue

class WebsiteModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Website, "objects"))

class SEOIssueModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(SEOIssue, "objects"))

