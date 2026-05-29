from django.test import TestCase
from .models import ExecTask, MeetingBrief

class ExecTaskModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ExecTask, "objects"))

class MeetingBriefModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(MeetingBrief, "objects"))

