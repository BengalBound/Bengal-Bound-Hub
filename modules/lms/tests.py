from django.test import TestCase
from .models import Course, CourseModule, Lesson, LearnerEnrollment, LessonProgress

class CourseModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Course, "objects"))

class CourseModuleModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(CourseModule, "objects"))

class LessonModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Lesson, "objects"))

class LearnerEnrollmentModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(LearnerEnrollment, "objects"))

class LessonProgressModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(LessonProgress, "objects"))

