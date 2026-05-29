from django.test import TestCase
from .models import EmailList, Subscriber, EmailTemplate, Campaign

class EmailListModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(EmailList, "objects"))

class SubscriberModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Subscriber, "objects"))

class EmailTemplateModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(EmailTemplate, "objects"))

class CampaignModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Campaign, "objects"))

