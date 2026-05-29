from django.test import TestCase
from .models import Event, Attendee

class EventModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Event, "objects"))

class AttendeeModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Attendee, "objects"))

