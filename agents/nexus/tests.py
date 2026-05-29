from django.test import TestCase
from .models import Course, Enrollment

class CourseModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Course, "objects"))

class EnrollmentModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Enrollment, "objects"))

