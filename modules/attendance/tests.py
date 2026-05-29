from django.test import TestCase
from .models import WorkSchedule, AttendanceRecord, Timesheet, TimesheetEntry

class WorkScheduleModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(WorkSchedule, "objects"))

class AttendanceRecordModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(AttendanceRecord, "objects"))

class TimesheetModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Timesheet, "objects"))

class TimesheetEntryModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(TimesheetEntry, "objects"))

