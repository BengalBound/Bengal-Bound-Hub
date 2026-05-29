from django.test import TestCase
from .models import DiningArea, Table, Reservation, TableOrder

class DiningAreaModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(DiningArea, "objects"))

class TableModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Table, "objects"))

class ReservationModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Reservation, "objects"))

class TableOrderModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(TableOrder, "objects"))

