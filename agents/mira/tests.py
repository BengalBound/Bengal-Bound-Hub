from django.test import TestCase
from .models import ClientHealth, SuccessEmail

class ClientHealthModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ClientHealth, "objects"))

class SuccessEmailModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(SuccessEmail, "objects"))

