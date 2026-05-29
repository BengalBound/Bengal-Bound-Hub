from django.test import TestCase
from .models import LegalDocument, Clause

class LegalDocumentModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(LegalDocument, "objects"))

class ClauseModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Clause, "objects"))

