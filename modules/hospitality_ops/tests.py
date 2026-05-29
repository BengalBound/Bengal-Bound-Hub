from django.test import TestCase
from .models import HousekeepingSchedule, MaintenanceTicket, ServiceRequest, ConciergeNote

class HousekeepingScheduleModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(HousekeepingSchedule, "objects"))

class MaintenanceTicketModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(MaintenanceTicket, "objects"))

class ServiceRequestModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ServiceRequest, "objects"))

class ConciergeNoteModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ConciergeNote, "objects"))

