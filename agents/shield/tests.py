from django.test import TestCase
from .models import ITTicket, KnowledgeArticle

class ITTicketModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ITTicket, "objects"))

class KnowledgeArticleModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(KnowledgeArticle, "objects"))

