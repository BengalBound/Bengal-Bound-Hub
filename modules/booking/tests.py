from django.test import TestCase
from .models import BookingService, StaffAvailability, Booking, BookingBlock

class BookingServiceModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(BookingService, "objects"))

class StaffAvailabilityModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(StaffAvailability, "objects"))

class BookingModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Booking, "objects"))

class BookingBlockModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(BookingBlock, "objects"))

