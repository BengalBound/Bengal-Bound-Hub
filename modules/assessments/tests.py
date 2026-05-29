from django.test import TestCase
from .models import Quiz, Question, QuestionChoice, QuizAttempt, AttemptAnswer

class QuizModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Quiz, "objects"))

class QuestionModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Question, "objects"))

class QuestionChoiceModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(QuestionChoice, "objects"))

class QuizAttemptModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(QuizAttempt, "objects"))

class AttemptAnswerModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(AttemptAnswer, "objects"))

