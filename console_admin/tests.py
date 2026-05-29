from django.test import TestCase
from .models import WorkspaceEnvironment, WorkspaceProject, AITask, AIChatInteraction, SupportTicket, AICredential, AITrainingDocument, AITaskLimit, ConsoleModuleActivation

class WorkspaceEnvironmentModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(WorkspaceEnvironment, "objects"))

class WorkspaceProjectModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(WorkspaceProject, "objects"))

class AITaskModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(AITask, "objects"))

class AIChatInteractionModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(AIChatInteraction, "objects"))

class SupportTicketModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(SupportTicket, "objects"))

class AICredentialModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(AICredential, "objects"))

class AITrainingDocumentModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(AITrainingDocument, "objects"))

class AITaskLimitModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(AITaskLimit, "objects"))

class ConsoleModuleActivationModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ConsoleModuleActivation, "objects"))

