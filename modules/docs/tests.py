from django.test import TestCase
from .models import HubDoc, DocShare

class HubDocModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(HubDoc, "objects"))

class DocShareModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(DocShare, "objects"))

