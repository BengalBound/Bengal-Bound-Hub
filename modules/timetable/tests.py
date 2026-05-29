from django.test import TestCase
from .models import Room, TimeSlot, ClassSession, ScheduleException

class RoomModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Room, "objects"))

class TimeSlotModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(TimeSlot, "objects"))

class ClassSessionModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ClassSession, "objects"))

class ScheduleExceptionModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ScheduleException, "objects"))

