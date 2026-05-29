from django.test import TestCase
from .models import GroupRFP, GroupBlock, RoomingListEntry, GroupContract

class GroupRFPModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(GroupRFP, "objects"))

class GroupBlockModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(GroupBlock, "objects"))

class RoomingListEntryModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(RoomingListEntry, "objects"))

class GroupContractModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(GroupContract, "objects"))

