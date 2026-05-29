from django.test import TestCase
from .models import Student, ParentGuardian, SubjectGrade, StudentAttendance

class StudentModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Student, "objects"))

class ParentGuardianModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ParentGuardian, "objects"))

class SubjectGradeModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(SubjectGrade, "objects"))

class StudentAttendanceModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(StudentAttendance, "objects"))

