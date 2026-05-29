from django.test import TestCase
from .models import VideoSession

class VideoSessionModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(VideoSession, "objects"))

