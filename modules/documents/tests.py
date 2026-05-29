from django.test import TestCase
from .models import DocumentFolder, Document, DocumentShare

class DocumentFolderModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(DocumentFolder, "objects"))

class DocumentModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Document, "objects"))

class DocumentShareModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(DocumentShare, "objects"))

