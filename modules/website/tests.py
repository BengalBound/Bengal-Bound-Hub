from django.test import TestCase
from .models import WebsiteProject, WebPage, WebsiteAsset

class WebsiteProjectModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(WebsiteProject, "objects"))

class WebPageModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(WebPage, "objects"))

class WebsiteAssetModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(WebsiteAsset, "objects"))

