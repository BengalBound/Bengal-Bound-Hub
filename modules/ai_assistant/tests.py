from django.test import TestCase
from .models import AssistantConversation, AssistantMessage, AssistantPromptTemplate

class AssistantConversationModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(AssistantConversation, "objects"))

class AssistantMessageModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(AssistantMessage, "objects"))

class AssistantPromptTemplateModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(AssistantPromptTemplate, "objects"))

