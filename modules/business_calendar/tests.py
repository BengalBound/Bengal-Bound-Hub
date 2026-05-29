from django.test import TestCase
from .models import BizCalendar, CalendarEvent, EventAttendee, EventReminder

class BizCalendarModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(BizCalendar, "objects"))

class CalendarEventModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(CalendarEvent, "objects"))

class EventAttendeeModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(EventAttendee, "objects"))

class EventReminderModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(EventReminder, "objects"))

