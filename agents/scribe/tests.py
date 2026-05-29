from django.test import TestCase
from .models import Meeting, ActionItem

class MeetingModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Meeting, "objects"))

class ActionItemModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ActionItem, "objects"))

