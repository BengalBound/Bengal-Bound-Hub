from django.test import TestCase
from .models import ProgressReport, ReportSubjectLine, ParentMessage, Announcement

class ProgressReportModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ProgressReport, "objects"))

class ReportSubjectLineModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ReportSubjectLine, "objects"))

class ParentMessageModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ParentMessage, "objects"))

class AnnouncementModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Announcement, "objects"))

