from django.test import TestCase
from .models import RoomType, Room, GuestProfile, Reservation, FolioCharge, HousekeepingTask

class RoomTypeModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(RoomType, "objects"))

class RoomModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Room, "objects"))

class GuestProfileModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(GuestProfile, "objects"))

class ReservationModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Reservation, "objects"))

class FolioChargeModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(FolioCharge, "objects"))

class HousekeepingTaskModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(HousekeepingTask, "objects"))

