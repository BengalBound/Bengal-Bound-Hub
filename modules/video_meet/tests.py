from django.test import TestCase
from .models import MeetingRoom, Meeting, MeetingAttendee

class MeetingRoomModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(MeetingRoom, "objects"))

class MeetingModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Meeting, "objects"))

class MeetingAttendeeModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(MeetingAttendee, "objects"))

