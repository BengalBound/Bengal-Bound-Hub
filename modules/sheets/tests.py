from django.test import TestCase
from .models import HubSheet

class HubSheetModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(HubSheet, "objects"))

