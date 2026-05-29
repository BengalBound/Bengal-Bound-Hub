from django.test import TestCase
from .models import ContentPiece, Campaign

class ContentPieceModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ContentPiece, "objects"))

class CampaignModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Campaign, "objects"))

