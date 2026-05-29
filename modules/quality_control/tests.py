from django.test import TestCase
from .models import AQLStandard, AQLRule, InspectionTemplate, InspectionCriterion, Inspection, InspectionResult, NonConformance, ShoeDefectRecord

class AQLStandardModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(AQLStandard, "objects"))

class AQLRuleModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(AQLRule, "objects"))

class InspectionTemplateModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(InspectionTemplate, "objects"))

class InspectionCriterionModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(InspectionCriterion, "objects"))

class InspectionModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Inspection, "objects"))

class InspectionResultModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(InspectionResult, "objects"))

class NonConformanceModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(NonConformance, "objects"))

class ShoeDefectRecordModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ShoeDefectRecord, "objects"))

