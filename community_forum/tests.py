from django.test import TestCase
from .models import ForumCategory, ForumTopic, ForumPost, ForumModerationLog

class ForumCategoryModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ForumCategory, "objects"))

class ForumTopicModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ForumTopic, "objects"))

class ForumPostModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ForumPost, "objects"))

class ForumModerationLogModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ForumModerationLog, "objects"))

