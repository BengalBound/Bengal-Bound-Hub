from django.test import TestCase
from .models import ContentCalendar, CalendarEntry

class ContentCalendarModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ContentCalendar, "objects"))

class CalendarEntryModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(CalendarEntry, "objects"))

