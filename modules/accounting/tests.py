from django.test import TestCase
from .models import AccountCategory, Account, JournalEntry, JournalLine, TaxRate, FiscalYear

class AccountCategoryModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(AccountCategory, "objects"))

class AccountModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Account, "objects"))

class JournalEntryModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(JournalEntry, "objects"))

class JournalLineModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(JournalLine, "objects"))

class TaxRateModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(TaxRate, "objects"))

class FiscalYearModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(FiscalYear, "objects"))

