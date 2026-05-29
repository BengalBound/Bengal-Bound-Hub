from django.test import TestCase
from .models import TravelClient, Itinerary, ItineraryItem, TravelBooking

class TravelClientModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(TravelClient, "objects"))

class ItineraryModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Itinerary, "objects"))

class ItineraryItemModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ItineraryItem, "objects"))

class TravelBookingModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(TravelBooking, "objects"))

