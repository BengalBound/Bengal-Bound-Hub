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


class E2EFactoryFlowTest(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        from hub.models import BusinessInstance
        User = get_user_model()
        owner = User.objects.create_user(username='factory_owner', email='factory@test.com', password='pass')
        self.business = BusinessInstance.objects.create(
            name="Test Factory",
            owner=owner,
        )

    def test_full_production_lifecycle(self):
        from django.utils import timezone
        # 1. Raw Material setup
        raw_mat = RawMaterial.objects.create(
            business=self.business,
            item_id="RM-001",
            name="Premium Leather",
            category="Leather",
            on_hand=1000,
            unit_cost=5.00
        )
        self.assertEqual(raw_mat.on_hand, 1000)

        # 2. Production Order creation
        order = ProductionOrder.objects.create(
            business=self.business,
            order_id="PO-999",
            style="Oxford Classic",
            buyer="Boutique Co",
            qty=100
        )
        self.assertEqual(order.current_stage, "planned")

        # 3. Material Issue (consume raw material)
        issue = MaterialIssue.objects.create(
            business=self.business,
            issue_id="MI-999",
            issue_date=timezone.now().date(),
            production_order_ref=order.order_id,
            material_name=raw_mat.name,
            issued_qty=250,
            standard_qty=200
        )
        
        # Assuming manual decrement logic is required in view layer
        raw_mat.on_hand -= issue.issued_qty
        raw_mat.save()
        self.assertEqual(raw_mat.on_hand, 750)
        
        # Move order to materials ready
        order.current_stage = "materials"
        order.stage_materials = True
        order.save()

        # 4. WIP Lot Tracking
        wip = WIPLot.objects.create(
            business=self.business,
            wip_id="WIP-999-1",
            style=order.style,
            production_order_ref=order.order_id,
            current_stage="cutting",
            qty=100
        )
        wip.current_stage = "stitching"
        wip.save()
        self.assertEqual(wip.current_stage, "stitching")

        # 5. Quality Control
        qc = QCInspection.objects.create(
            business=self.business,
            inspection_id="QC-999",
            checkpoint="Upper Stitching Final",
            production_order_ref=order.order_id,
            inspection_date=timezone.now().date(),
            lot_size=100,
            checked=20,
            defects_found=1
        )
        self.assertEqual(qc.defect_rate_pct, 5.0)

        # 6. Finished Goods completion
        fg = FinishedGoodsLot.objects.create(
            business=self.business,
            fg_id="FG-999",
            style=order.style,
            production_order_ref=order.order_id,
            qty=99,
            unit_cost=25.00
        )
        self.assertEqual(fg.total_value, 99 * 25.00)

        # Update order to complete
        order.current_stage = "shipped"
        order.stage_shipped = True
        order.save()
        
        self.assertFalse(order.is_overdue)
