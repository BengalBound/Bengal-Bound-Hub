from django.test import TestCase
from .models import Board, BoardList, Card, Label, CardLabel, Checklist, ChecklistItem, CardComment, CardActivity

class BoardModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Board, "objects"))

class BoardListModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(BoardList, "objects"))

class CardModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Card, "objects"))

class LabelModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Label, "objects"))

class CardLabelModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(CardLabel, "objects"))

class ChecklistModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Checklist, "objects"))

class ChecklistItemModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ChecklistItem, "objects"))

class CardCommentModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(CardComment, "objects"))

class CardActivityModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(CardActivity, "objects"))

