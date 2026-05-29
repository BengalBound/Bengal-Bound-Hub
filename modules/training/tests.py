from django.test import TestCase
from .models import Course, CourseModule, Enrollment, Quiz, QuizQuestion, QuizChoice

class CourseModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Course, "objects"))

class CourseModuleModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(CourseModule, "objects"))

class EnrollmentModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Enrollment, "objects"))

class QuizModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Quiz, "objects"))

class QuizQuestionModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(QuizQuestion, "objects"))

class QuizChoiceModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(QuizChoice, "objects"))

