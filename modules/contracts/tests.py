from django.test import TestCase
from .models import ContractTemplate, Contract, ContractParty

class ContractTemplateModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ContractTemplate, "objects"))

class ContractModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Contract, "objects"))

class ContractPartyModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ContractParty, "objects"))

