from django.test import TestCase
from .models import ERPLedger, ERPJournalEntry, ERPJournalLine, ERPVendor, ERPPurchaseOrder, ERPPurchaseOrderLine, ERPCostCenter, ERPBudgetLine

class ERPLedgerModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ERPLedger, "objects"))

class ERPJournalEntryModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ERPJournalEntry, "objects"))

class ERPJournalLineModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ERPJournalLine, "objects"))

class ERPVendorModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ERPVendor, "objects"))

class ERPPurchaseOrderModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ERPPurchaseOrder, "objects"))

class ERPPurchaseOrderLineModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ERPPurchaseOrderLine, "objects"))

class ERPCostCenterModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ERPCostCenter, "objects"))

class ERPBudgetLineModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ERPBudgetLine, "objects"))

