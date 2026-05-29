from django.test import TestCase
from .models import MailAccount, MailMessage, MailAttachment

class MailAccountModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(MailAccount, "objects"))

class MailMessageModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(MailMessage, "objects"))

class MailAttachmentModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(MailAttachment, "objects"))

