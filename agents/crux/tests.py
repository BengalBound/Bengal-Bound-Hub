from django.test import TestCase
from .models import Contact, Interaction

class ContactModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Contact, "objects"))

class InteractionModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Interaction, "objects"))

