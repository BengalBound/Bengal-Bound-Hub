from django.test import TestCase
from .models import ClientPortalAccess, PortalDocument

class ClientPortalAccessModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ClientPortalAccess, "objects"))

class PortalDocumentModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(PortalDocument, "objects"))

