from django.test import TestCase
from .models import Announcement, AnnouncementRead, AnnouncementComment

class AnnouncementModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Announcement, "objects"))

class AnnouncementReadModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(AnnouncementRead, "objects"))

class AnnouncementCommentModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(AnnouncementComment, "objects"))

