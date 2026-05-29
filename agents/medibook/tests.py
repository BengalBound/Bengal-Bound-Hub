from django.test import TestCase
from .models import Doctor, Appointment

class DoctorModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Doctor, "objects"))

class AppointmentModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Appointment, "objects"))

