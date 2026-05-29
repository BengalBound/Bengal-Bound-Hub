from django.test import TestCase
from .models import MeetingRequest, EmailTriage

class MeetingRequestModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(MeetingRequest, "objects"))

class EmailTriageModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(EmailTriage, "objects"))

