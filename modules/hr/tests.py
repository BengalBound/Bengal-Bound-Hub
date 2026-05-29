from django.test import TestCase
from .models import Department, JobPosition, Employee, LeaveType, LeaveRequest, PerformanceReview

class DepartmentModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Department, "objects"))

class JobPositionModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(JobPosition, "objects"))

class EmployeeModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Employee, "objects"))

class LeaveTypeModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(LeaveType, "objects"))

class LeaveRequestModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(LeaveRequest, "objects"))

class PerformanceReviewModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(PerformanceReview, "objects"))

