from django.contrib import admin
from .models import (
    ProductionOrder, ProductionPlan, RawMaterial, WIPLot, FinishedGoodsLot,
    TimeStudy, SMVSheet, CapacityStudy, StyleCosting,
    DailyProductionReport, AttendanceSheet, MaterialIssue,
    QCInspection, ReworkRecord, FactorySOP,
    Buyer, SalesDeal, CustomerOrder, FactoryInvoice,
    Vendor, VendorPO, SupplierScore,
    DistributionChannel, WholesaleAccount, SalesRep, SalesTarget,
    FactoryTask, MarketingCampaign,
    ARAPEntry, BankAccount, LetterOfCredit,
    FactoryEmployee, ApprovalRequest,
)

for model in [
    ProductionOrder, ProductionPlan, RawMaterial, WIPLot, FinishedGoodsLot,
    TimeStudy, SMVSheet, CapacityStudy, StyleCosting,
    DailyProductionReport, AttendanceSheet, MaterialIssue,
    QCInspection, ReworkRecord, FactorySOP,
    Buyer, SalesDeal, CustomerOrder, FactoryInvoice,
    Vendor, VendorPO, SupplierScore,
    DistributionChannel, WholesaleAccount, SalesRep, SalesTarget,
    FactoryTask, MarketingCampaign,
    ARAPEntry, BankAccount, LetterOfCredit,
    FactoryEmployee, ApprovalRequest,
]:
    admin.site.register(model)
