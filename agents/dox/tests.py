from django.test import TestCase
from .models import DocumentationProject, DocPage

class DocumentationProjectModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(DocumentationProject, "objects"))

class DocPageModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(DocPage, "objects"))

