from django.db import models
from django.utils import timezone


class ERPLedger(models.Model):
    ACCOUNT_TYPES = [
        ('asset', 'Asset'), ('liability', 'Liability'), ('equity', 'Equity'),
        ('revenue', 'Revenue'), ('expense', 'Expense'),
    ]
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='erp_ledger_accounts')
    account_code = models.CharField(max_length=20)
    account_name = models.CharField(max_length=120)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('business', 'account_code')]
        ordering = ['account_code']

    def __str__(self):
        return f"{self.account_code} — {self.account_name}"


class ERPJournalEntry(models.Model):
    STATUS = [('draft', 'Draft'), ('posted', 'Posted'), ('reversed', 'Reversed')]
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='erp_journal_entries')
    reference = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    entry_date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    posted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-entry_date', '-created_at']

    def __str__(self):
        return f"JE-{self.pk} {self.entry_date}"

    @property
    def is_balanced(self):
        lines = self.lines.all()
        total_debit = sum(l.debit for l in lines)
        total_credit = sum(l.credit for l in lines)
        return abs(total_debit - total_credit) < 0.01


class ERPJournalLine(models.Model):
    entry = models.ForeignKey(ERPJournalEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(ERPLedger, on_delete=models.PROTECT)
    description = models.CharField(max_length=200, blank=True)
    debit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.account} Dr:{self.debit} Cr:{self.credit}"


class ERPVendor(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='erp_vendors')
    name = models.CharField(max_length=150)
    contact_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    payment_terms_days = models.PositiveSmallIntegerField(default=30)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ERPPurchaseOrder(models.Model):
    STATUS = [
        ('draft', 'Draft'), ('sent', 'Sent to Vendor'), ('partial', 'Partially Received'),
        ('received', 'Fully Received'), ('cancelled', 'Cancelled'),
    ]
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='erp_purchase_orders')
    vendor = models.ForeignKey(ERPVendor, on_delete=models.PROTECT, related_name='purchase_orders')
    po_number = models.CharField(max_length=30)
    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    order_date = models.DateField(default=timezone.localdate)
    expected_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('business', 'po_number')]
        ordering = ['-order_date']

    def __str__(self):
        return f"PO-{self.po_number}"

    @property
    def total(self):
        return sum(l.line_total for l in self.lines.all())


class ERPPurchaseOrderLine(models.Model):
    po = models.ForeignKey(ERPPurchaseOrder, on_delete=models.CASCADE, related_name='lines')
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=1)
    unit = models.CharField(max_length=20, default='pcs')
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    received_qty = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    account = models.ForeignKey(ERPLedger, on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def line_total(self):
        return self.quantity * self.unit_price


class ERPCostCenter(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='erp_cost_centers')
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    manager = models.ForeignKey('bredbound.BusinessEmployee', on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [('business', 'code')]
        ordering = ['code']

    def __str__(self):
        return f"{self.code} — {self.name}"


class ERPBudgetLine(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='erp_budget_lines')
    cost_center = models.ForeignKey(ERPCostCenter, on_delete=models.CASCADE, related_name='budget_lines')
    account = models.ForeignKey(ERPLedger, on_delete=models.CASCADE)
    fiscal_year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()  # 1-12
    budgeted_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    actual_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        unique_together = [('business', 'cost_center', 'account', 'fiscal_year', 'month')]

    @property
    def variance(self):
        return self.budgeted_amount - self.actual_amount
