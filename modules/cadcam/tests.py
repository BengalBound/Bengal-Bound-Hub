from django.test import TestCase
from .models import CADProject, CADFile

class CADProjectModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(CADProject, "objects"))

class CADFileModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(CADFile, "objects"))

