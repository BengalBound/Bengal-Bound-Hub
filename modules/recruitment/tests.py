from django.test import TestCase
from .models import JobPosting, Applicant, Application, Interview

class JobPostingModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(JobPosting, "objects"))

class ApplicantModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Applicant, "objects"))

class ApplicationModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Application, "objects"))

class InterviewModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Interview, "objects"))

