from django.test import TestCase
from .models import ProductionOrder, ProductionPlan, RawMaterial, ProductSKU, WIPLot, FinishedGoodsLot, TimeStudy, SMVSheet, CapacityStudy, StyleCosting, DailyProductionReport, AttendanceSheet, MaterialIssue, QCInspection, ReworkRecord, FactorySOP, Buyer, SalesDeal, CustomerOrder, FactoryInvoice, Vendor, VendorPO, SupplierScore, DistributionChannel, WholesaleAccount, SalesRep, SalesTarget, FactoryTask, MarketingCampaign, ARAPEntry, BankAccount, LetterOfCredit, FactoryEmployee, ApprovalRequest, HourlyProductionEntry, PettyCash, WorkerAdvance, FactorySettings, StockMovement, KPITemplate, EmployeeEvaluation, SalesIncentive, SampleOrder

class ProductionOrderModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ProductionOrder, "objects"))

class ProductionPlanModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ProductionPlan, "objects"))

class RawMaterialModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(RawMaterial, "objects"))

class ProductSKUModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ProductSKU, "objects"))

class WIPLotModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(WIPLot, "objects"))

class FinishedGoodsLotModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(FinishedGoodsLot, "objects"))

class TimeStudyModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(TimeStudy, "objects"))

class SMVSheetModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(SMVSheet, "objects"))

class CapacityStudyModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(CapacityStudy, "objects"))

class StyleCostingModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(StyleCosting, "objects"))

class DailyProductionReportModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(DailyProductionReport, "objects"))

class AttendanceSheetModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(AttendanceSheet, "objects"))

class MaterialIssueModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(MaterialIssue, "objects"))

class QCInspectionModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(QCInspection, "objects"))

class ReworkRecordModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ReworkRecord, "objects"))

class FactorySOPModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(FactorySOP, "objects"))

class BuyerModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Buyer, "objects"))

class SalesDealModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(SalesDeal, "objects"))

class CustomerOrderModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(CustomerOrder, "objects"))

class FactoryInvoiceModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(FactoryInvoice, "objects"))

class VendorModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Vendor, "objects"))

class VendorPOModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(VendorPO, "objects"))

class SupplierScoreModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(SupplierScore, "objects"))

class DistributionChannelModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(DistributionChannel, "objects"))

class WholesaleAccountModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(WholesaleAccount, "objects"))

class SalesRepModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(SalesRep, "objects"))

class SalesTargetModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(SalesTarget, "objects"))

class FactoryTaskModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(FactoryTask, "objects"))

class MarketingCampaignModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(MarketingCampaign, "objects"))

class ARAPEntryModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ARAPEntry, "objects"))

class BankAccountModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(BankAccount, "objects"))

class LetterOfCreditModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(LetterOfCredit, "objects"))

class FactoryEmployeeModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(FactoryEmployee, "objects"))

class ApprovalRequestModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ApprovalRequest, "objects"))

class HourlyProductionEntryModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(HourlyProductionEntry, "objects"))

class PettyCashModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(PettyCash, "objects"))

class WorkerAdvanceModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(WorkerAdvance, "objects"))

class FactorySettingsModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(FactorySettings, "objects"))

class StockMovementModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(StockMovement, "objects"))

class KPITemplateModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(KPITemplate, "objects"))

class EmployeeEvaluationModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(EmployeeEvaluation, "objects"))

class SalesIncentiveModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(SalesIncentive, "objects"))

class SampleOrderModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(SampleOrder, "objects"))

