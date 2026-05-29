from django.test import TestCase
from .models import Project, Milestone, Task, TimeEntry, ProjectComment

class ProjectModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Project, "objects"))

class MilestoneModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Milestone, "objects"))

class TaskModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Task, "objects"))

class TimeEntryModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(TimeEntry, "objects"))

class ProjectCommentModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ProjectComment, "objects"))

