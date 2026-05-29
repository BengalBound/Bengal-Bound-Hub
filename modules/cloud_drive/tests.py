from django.test import TestCase
from .models import DriveFolder, DriveFile, DriveShare

class DriveFolderModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(DriveFolder, "objects"))

class DriveFileModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(DriveFile, "objects"))

class DriveShareModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(DriveShare, "objects"))

