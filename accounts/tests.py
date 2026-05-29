from django.test import TestCase
from .models import User, WorkspaceProfile, CustomerProfile

class UserModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(User, "objects"))

class WorkspaceProfileModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(WorkspaceProfile, "objects"))

class CustomerProfileModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(CustomerProfile, "objects"))

