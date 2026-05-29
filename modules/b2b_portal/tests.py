from django.test import TestCase
from .models import B2BCustomer, B2BOrder, B2BOrderLine

class B2BCustomerModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(B2BCustomer, "objects"))

class B2BOrderModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(B2BOrder, "objects"))

class B2BOrderLineModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(B2BOrderLine, "objects"))

