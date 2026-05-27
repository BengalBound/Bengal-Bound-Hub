from django.db import models
from django.utils import timezone
from hub.models import BusinessInstance

CATEGORY_CHOICES = [
    ('Leather', 'Leather'), ('Sole', 'Sole'), ('Thread', 'Thread'),
    ('Fabric', 'Fabric'), ('Trim', 'Trim'), ('Chemicals', 'Chemicals'),
    ('Components', 'Components'), ('Packaging', 'Packaging'), ('Other', 'Other'),
]

# ─── PRODUCTION ───────────────────────────────────────────────────────────────

class ProductionOrder(models.Model):
    PRIORITY = [('low', 'Low'), ('med', 'Medium'), ('high', 'High')]
    STAGE = [
        ('planned', 'Planned'), ('materials', 'Materials Ready'),
        ('cutting', 'Cutting'), ('stitching', 'Upper Stitching'),
        ('lasting', 'Lasting'), ('sole', 'Sole Bonding'),
        ('finishing', 'Finishing'), ('qc', 'Final QC'),
        ('packed', 'Packed'), ('shipped', 'Shipped'),
    ]
    business      = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_production_orders')
    order_id      = models.CharField(max_length=30)
    style         = models.CharField(max_length=200)
    buyer         = models.CharField(max_length=100)
    qty           = models.PositiveIntegerField(default=0)
    line          = models.CharField(max_length=50, blank=True)
    start_date    = models.DateField(null=True, blank=True)
    target_date   = models.DateField(null=True, blank=True)
    priority      = models.CharField(max_length=10, choices=PRIORITY, default='med')
    current_stage = models.CharField(max_length=20, choices=STAGE, default='planned')
    stage_materials  = models.BooleanField(default=False)
    stage_cutting    = models.BooleanField(default=False)
    stage_stitching  = models.BooleanField(default=False)
    stage_lasting    = models.BooleanField(default=False)
    stage_sole       = models.BooleanField(default=False)
    stage_finishing  = models.BooleanField(default=False)
    stage_qc         = models.BooleanField(default=False)
    stage_packed     = models.BooleanField(default=False)
    stage_shipped    = models.BooleanField(default=False)
    notes         = models.TextField(blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_id} — {self.style}"

    @property
    def stages_done(self):
        return sum([self.stage_materials, self.stage_cutting, self.stage_stitching,
                    self.stage_lasting, self.stage_sole, self.stage_finishing,
                    self.stage_qc, self.stage_packed, self.stage_shipped])

    @property
    def progress_pct(self):
        return int(self.stages_done / 9 * 100)

    @property
    def is_overdue(self):
        return bool(self.target_date and self.current_stage != 'shipped'
                    and self.target_date < timezone.now().date())


class ProductionPlan(models.Model):
    STATUS = [('scheduled', 'Scheduled'), ('tentative', 'Tentative'),
              ('in_progress', 'In Progress'), ('completed', 'Completed')]
    business    = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_plans')
    plan_id     = models.CharField(max_length=30)
    style       = models.CharField(max_length=200)
    buyer       = models.CharField(max_length=100)
    qty         = models.PositiveIntegerField(default=0)
    line        = models.CharField(max_length=50, blank=True)
    plan_start  = models.DateField(null=True, blank=True)
    plan_end    = models.DateField(null=True, blank=True)
    capacity_pct = models.PositiveSmallIntegerField(default=80)
    status      = models.CharField(max_length=20, choices=STATUS, default='scheduled')
    notes       = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['plan_start']

    def __str__(self):
        return f"{self.plan_id} — {self.style}"


# ─── INVENTORY ────────────────────────────────────────────────────────────────

class RawMaterial(models.Model):
    business          = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_raw_materials')
    item_id           = models.CharField(max_length=30)
    name              = models.CharField(max_length=200)
    category          = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='Other')
    uom               = models.CharField(max_length=30, default='pcs')
    on_hand           = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reorder_level     = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_cost         = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    supplier          = models.CharField(max_length=100, blank=True)
    location          = models.CharField(max_length=100, blank=True)
    last_received     = models.DateField(null=True, blank=True)
    notes             = models.TextField(blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        return self.on_hand < self.reorder_level

    @property
    def stock_value(self):
        return float(self.on_hand) * float(self.unit_cost)


class ProductSKU(models.Model):
    SKU_CATEGORY = [
        ('Upper', 'Upper'), ('Sole', 'Sole'), ('Assembly', 'Assembly'),
        ('Accessory', 'Accessory'), ('Packaging', 'Packaging'), ('Other', 'Other'),
    ]
    business      = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_product_skus')
    sku_id        = models.CharField(max_length=30)
    name          = models.CharField(max_length=200)
    category      = models.CharField(max_length=30, choices=SKU_CATEGORY, default='Other')
    uom           = models.CharField(max_length=20, default='pairs')
    on_hand       = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reorder_point = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_cost     = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    supplier      = models.CharField(max_length=100, blank=True)
    last_in_date  = models.DateField(null=True, blank=True)
    notes         = models.TextField(blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.sku_id} — {self.name}"

    @property
    def is_low_stock(self):
        return self.on_hand < self.reorder_point

    @property
    def stock_value(self):
        return float(self.on_hand) * float(self.unit_cost)


class WIPLot(models.Model):
    STAGE = [('cutting', 'Cutting'), ('stitching', 'Stitching'), ('lasting', 'Lasting'),
             ('sole', 'Sole Bonding'), ('finishing', 'Finishing'), ('qc', 'QC')]
    business             = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_wip_lots')
    wip_id               = models.CharField(max_length=30)
    style                = models.CharField(max_length=200)
    production_order_ref = models.CharField(max_length=30, blank=True)
    current_stage        = models.CharField(max_length=20, choices=STAGE, default='cutting')
    qty                  = models.PositiveIntegerField(default=0)
    line                 = models.CharField(max_length=50, blank=True)
    wip_value            = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    days_in_wip          = models.PositiveSmallIntegerField(default=0)
    notes                = models.TextField(blank=True)
    created_at           = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-days_in_wip']

    def __str__(self):
        return f"{self.wip_id} — {self.style}"


class FinishedGoodsLot(models.Model):
    STATUS = [('ready_to_ship', 'Ready to Ship'), ('partial_shipped', 'Partial Shipped'), ('shipped', 'Shipped')]
    business             = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_finished_goods')
    fg_id                = models.CharField(max_length=30)
    style                = models.CharField(max_length=200)
    production_order_ref = models.CharField(max_length=30, blank=True)
    qty                  = models.PositiveIntegerField(default=0)
    uom                  = models.CharField(max_length=20, default='pairs')
    unit_cost            = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    location             = models.CharField(max_length=100, blank=True)
    buyer                = models.CharField(max_length=100, blank=True)
    ready_date           = models.DateField(null=True, blank=True)
    status               = models.CharField(max_length=20, choices=STATUS, default='ready_to_ship')
    notes                = models.TextField(blank=True)
    created_at           = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-ready_date']

    def __str__(self):
        return f"{self.fg_id} — {self.style}"

    @property
    def total_value(self):
        return float(self.qty) * float(self.unit_cost)


# ─── INDUSTRIAL ENGINEERING ──────────────────────────────────────────────────

class TimeStudy(models.Model):
    STATUS = [('draft', 'Draft'), ('review', 'Review'), ('approved', 'Approved')]
    business             = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_time_studies')
    study_id             = models.CharField(max_length=30)
    operation            = models.CharField(max_length=200)
    style                = models.CharField(max_length=200)
    machine              = models.CharField(max_length=100, blank=True)
    operator             = models.CharField(max_length=100, blank=True)
    cycles               = models.PositiveSmallIntegerField(default=10)
    observed_avg_seconds = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    performance_rating   = models.PositiveSmallIntegerField(default=100)
    allowance_pct        = models.PositiveSmallIntegerField(default=15)
    status               = models.CharField(max_length=10, choices=STATUS, default='draft')
    notes                = models.TextField(blank=True)
    created_at           = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.study_id} — {self.operation}"

    @property
    def basic_time(self):
        return float(self.observed_avg_seconds) * self.performance_rating / 100

    @property
    def standard_time_seconds(self):
        return self.basic_time * (1 + self.allowance_pct / 100)

    @property
    def smv(self):
        return round(self.standard_time_seconds / 60, 3)


class SMVSheet(models.Model):
    STATUS = [('draft', 'Draft'), ('review', 'Review'), ('approved', 'Approved')]
    business              = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_smv_sheets')
    smv_id                = models.CharField(max_length=30)
    style                 = models.CharField(max_length=200)
    section               = models.CharField(max_length=100)
    total_operations      = models.PositiveSmallIntegerField(default=0)
    total_smv             = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    target_efficiency_pct = models.PositiveSmallIntegerField(default=65)
    production_line       = models.CharField(max_length=50, blank=True)
    status                = models.CharField(max_length=10, choices=STATUS, default='draft')
    notes                 = models.TextField(blank=True)
    created_at            = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.smv_id} — {self.style} ({self.section})"


class CapacityStudy(models.Model):
    STATUS = [('planning', 'Planning'), ('active', 'Active'), ('archived', 'Archived')]
    business              = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_capacity_studies')
    study_id              = models.CharField(max_length=30)
    line                  = models.CharField(max_length=50)
    section               = models.CharField(max_length=100)
    style                 = models.CharField(max_length=200)
    operators             = models.PositiveSmallIntegerField(default=0)
    working_hours         = models.DecimalField(max_digits=4, decimal_places=1, default=8)
    line_smv              = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    target_efficiency_pct = models.PositiveSmallIntegerField(default=65)
    status                = models.CharField(max_length=10, choices=STATUS, default='active')
    notes                 = models.TextField(blank=True)
    created_at            = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['line', 'section']

    def __str__(self):
        return f"{self.study_id} — {self.line} ({self.section})"

    @property
    def target_output(self):
        if self.line_smv > 0:
            return int(self.operators * float(self.working_hours) * 60
                       / float(self.line_smv) * self.target_efficiency_pct / 100)
        return 0


class StyleCosting(models.Model):
    STATUS = [('draft', 'Draft'), ('review', 'Review'), ('approved', 'Approved')]
    business              = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_style_costings')
    costing_id            = models.CharField(max_length=30)
    style                 = models.CharField(max_length=200)
    material_cost         = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    labor_minutes         = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    labor_rate_per_minute = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    overhead_pct          = models.PositiveSmallIntegerField(default=35)
    target_margin_pct     = models.PositiveSmallIntegerField(default=20)
    status                = models.CharField(max_length=10, choices=STATUS, default='draft')
    notes                 = models.TextField(blank=True)
    created_at            = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.costing_id} — {self.style}"

    @property
    def labor_cost(self):
        return float(self.labor_minutes) * float(self.labor_rate_per_minute)

    @property
    def total_direct_cost(self):
        return float(self.material_cost) + self.labor_cost

    @property
    def total_cost(self):
        return self.total_direct_cost * (1 + self.overhead_pct / 100)

    @property
    def selling_price(self):
        if self.target_margin_pct < 100:
            return self.total_cost / (1 - self.target_margin_pct / 100)
        return 0


# ─── FACTORY DAILY OPERATIONS ─────────────────────────────────────────────────

class DailyProductionReport(models.Model):
    STATUS = [('green', 'Green — On Target'), ('amber', 'Amber — Near Target'), ('red', 'Red — Below Target')]
    business         = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_daily_reports')
    report_date      = models.DateField()
    line             = models.CharField(max_length=50)
    style            = models.CharField(max_length=200, blank=True)
    manpower         = models.PositiveSmallIntegerField(default=0)
    hour_target      = models.PositiveSmallIntegerField(default=0)
    day_target       = models.PositiveSmallIntegerField(default=0)
    actual_output    = models.PositiveSmallIntegerField(default=0)
    defects          = models.PositiveSmallIntegerField(default=0)
    downtime_minutes = models.PositiveSmallIntegerField(default=0)
    status           = models.CharField(max_length=10, choices=STATUS, default='green')
    notes            = models.TextField(blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-report_date', 'line']

    def __str__(self):
        return f"{self.report_date} — {self.line}"

    downtime_cause   = models.CharField(max_length=200, blank=True)
    smv_per_pair     = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    @property
    def efficiency_pct(self):
        return int(self.actual_output / self.day_target * 100) if self.day_target else 0

    @property
    def line_efficiency_pct(self):
        if self.manpower and self.smv_per_pair:
            return round(float(self.smv_per_pair) * self.actual_output / (self.manpower * 480) * 100, 1)
        return self.efficiency_pct


class AttendanceSheet(models.Model):
    business         = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_attendance')
    sheet_date       = models.DateField()
    section          = models.CharField(max_length=100)
    present          = models.PositiveSmallIntegerField(default=0)
    absent           = models.PositiveSmallIntegerField(default=0)
    on_leave         = models.PositiveSmallIntegerField(default=0)
    ot_hours         = models.DecimalField(max_digits=6, decimal_places=1, default=0)
    piece_rate_pairs = models.PositiveIntegerField(default=0)
    day_wage_total   = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ot_wage_total    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes            = models.TextField(blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sheet_date', 'section']

    def __str__(self):
        return f"{self.sheet_date} — {self.section}"

    @property
    def total_wages(self):
        return float(self.day_wage_total) + float(self.ot_wage_total)


class MaterialIssue(models.Model):
    business             = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_material_issues')
    issue_id             = models.CharField(max_length=30)
    issue_date           = models.DateField()
    production_order_ref = models.CharField(max_length=30, blank=True)
    style                = models.CharField(max_length=200, blank=True)
    material_name        = models.CharField(max_length=200)
    uom                  = models.CharField(max_length=30, default='pcs')
    issued_qty           = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    standard_qty         = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    qty_produced         = models.PositiveIntegerField(default=0)
    notes                = models.TextField(blank=True)
    created_at           = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-issue_date']

    def __str__(self):
        return f"{self.issue_id} — {self.material_name}"

    @property
    def variance_pct(self):
        if self.standard_qty:
            return round((float(self.issued_qty) - float(self.standard_qty))
                         / float(self.standard_qty) * 100, 1)
        return 0


# ─── QUALITY ──────────────────────────────────────────────────────────────────

class QCInspection(models.Model):
    RESULT   = [('pass', 'Pass'), ('fail', 'Fail'), ('hold', 'Hold — Pending Review')]
    STAGE    = [('incoming', 'Incoming Material'), ('cutting', 'Cutting'), ('stitching', 'Stitching'),
                ('lasting', 'Lasting'), ('sole', 'Sole Bonding'), ('final', 'Final QC'), ('pack', 'Pre-Pack')]
    AQL      = [('1.0', 'AQL 1.0'), ('2.5', 'AQL 2.5'), ('4.0', 'AQL 4.0'), ('6.5', 'AQL 6.5')]
    SEVERITY = [('critical', 'Critical'), ('major', 'Major'), ('minor', 'Minor')]
    business             = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_qc_inspections')
    inspection_id        = models.CharField(max_length=30)
    lot_number           = models.CharField(max_length=50, blank=True)
    checkpoint           = models.CharField(max_length=200)
    style                = models.CharField(max_length=200, blank=True)
    production_order_ref = models.CharField(max_length=30, blank=True)
    inspector            = models.CharField(max_length=100, blank=True)
    inspection_date      = models.DateField()
    lot_size             = models.PositiveIntegerField(default=0)
    checked              = models.PositiveIntegerField(default=0)
    defects_found        = models.PositiveIntegerField(default=0)
    defect_severity      = models.CharField(max_length=15, choices=SEVERITY, blank=True)
    aql_level            = models.CharField(max_length=5, choices=AQL, default='2.5')
    is_first_inspection  = models.BooleanField(default=True)
    stage                = models.CharField(max_length=20, choices=STAGE, default='final')
    result               = models.CharField(max_length=10, choices=RESULT, default='pass')
    report_file          = models.FileField(upload_to='factory_ops/qc_reports/', blank=True, null=True)
    notes                = models.TextField(blank=True)
    created_at           = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-inspection_date']

    def __str__(self):
        return f"{self.inspection_id} — {self.checkpoint}"

    @property
    def defect_rate_pct(self):
        return round(self.defects_found / self.checked * 100, 2) if self.checked else 0


class ReworkRecord(models.Model):
    STATUS   = [('open', 'Open'), ('in_progress', 'In Progress'), ('closed', 'Closed')]
    SEVERITY = [('critical', 'Critical'), ('major', 'Major'), ('minor', 'Minor')]
    business             = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_rework_records')
    rework_id            = models.CharField(max_length=30)
    rework_date          = models.DateField()
    production_order_ref = models.CharField(max_length=30, blank=True)
    style                = models.CharField(max_length=200, blank=True)
    stage                = models.CharField(max_length=100)
    defect_type          = models.CharField(max_length=200)
    defect_severity      = models.CharField(max_length=15, choices=SEVERITY, default='major')
    qty_affected         = models.PositiveIntegerField(default=0)
    qty_recovered        = models.PositiveIntegerField(default=0)
    qty_rejected         = models.PositiveIntegerField(default=0)
    labor_cost           = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    root_cause           = models.TextField(blank=True)
    status               = models.CharField(max_length=15, choices=STATUS, default='open')
    notes                = models.TextField(blank=True)
    created_at           = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-rework_date']

    def __str__(self):
        return f"{self.rework_id} — {self.defect_type}"

    @property
    def recovery_rate_pct(self):
        return int(self.qty_recovered / self.qty_affected * 100) if self.qty_affected else 0


class FactorySOP(models.Model):
    STATUS = [('active', 'Active'), ('review', 'Under Review'), ('draft', 'Draft'), ('superseded', 'Superseded')]
    business     = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_sops')
    sop_id       = models.CharField(max_length=30)
    title        = models.CharField(max_length=200)
    department   = models.CharField(max_length=100)
    owner        = models.CharField(max_length=100, blank=True)
    version      = models.CharField(max_length=20, default='1.0')
    updated_date = models.DateField(null=True, blank=True)
    status       = models.CharField(max_length=15, choices=STATUS, default='active')
    description  = models.TextField(blank=True)
    document     = models.FileField(upload_to='factory_ops/sops/', blank=True, null=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['department', 'title']

    def __str__(self):
        return f"{self.sop_id} — {self.title}"


# ─── COMMERCIAL ───────────────────────────────────────────────────────────────

class Buyer(models.Model):
    RATING = [('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')]
    STATUS = [('active', 'Active'), ('inactive', 'Inactive'), ('prospect', 'Prospect')]
    business      = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_buyers')
    buyer_id      = models.CharField(max_length=30)
    name          = models.CharField(max_length=200)
    country       = models.CharField(max_length=100, blank=True)
    contact       = models.CharField(max_length=100, blank=True)
    email         = models.EmailField(blank=True)
    phone         = models.CharField(max_length=50, blank=True)
    payment_terms = models.CharField(max_length=100, blank=True)
    rating        = models.CharField(max_length=2, choices=RATING, default='B')
    status        = models.CharField(max_length=10, choices=STATUS, default='prospect')
    ytd_volume    = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes         = models.TextField(blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class SalesDeal(models.Model):
    STAGE = [('lead', 'Lead'), ('quoted', 'Quoted'), ('sample_sent', 'Sample Sent'),
             ('negotiating', 'Negotiating'), ('won', 'Won'), ('lost', 'Lost')]
    business     = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_sales_deals')
    deal_id      = models.CharField(max_length=30)
    deal_name    = models.CharField(max_length=200)
    buyer_name   = models.CharField(max_length=100)
    value        = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    stage        = models.CharField(max_length=20, choices=STAGE, default='lead')
    probability  = models.PositiveSmallIntegerField(default=50)
    target_close = models.DateField(null=True, blank=True)
    next_action  = models.CharField(max_length=200, blank=True)
    notes        = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-value']

    def __str__(self):
        return f"{self.deal_id} — {self.deal_name}"

    @property
    def weighted_value(self):
        return float(self.value) * self.probability / 100


class CustomerOrder(models.Model):
    STATUS = [('draft', 'Draft'), ('confirmed', 'Confirmed'), ('in_production', 'In Production'),
              ('ready', 'Ready to Ship'), ('partial_delivered', 'Partial Delivered'),
              ('delivered', 'Delivered'), ('cancelled', 'Cancelled')]
    CHANNEL = [('Export', 'Export'), ('Wholesale', 'Wholesale'),
               ('Distribution', 'Distribution'), ('Domestic', 'Domestic')]
    business      = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_customer_orders')
    order_id      = models.CharField(max_length=30)
    buyer_name    = models.CharField(max_length=100)
    style         = models.CharField(max_length=200)
    qty           = models.PositiveIntegerField(default=0)
    unit_price    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    channel       = models.CharField(max_length=20, choices=CHANNEL, default='Export')
    order_date    = models.DateField(null=True, blank=True)
    delivery_date = models.DateField(null=True, blank=True)
    status        = models.CharField(max_length=25, choices=STATUS, default='confirmed')
    notes         = models.TextField(blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-order_date']

    def __str__(self):
        return f"{self.order_id} — {self.buyer_name}"

    @property
    def order_value(self):
        return float(self.qty) * float(self.unit_price)


class FactoryInvoice(models.Model):
    STATUS = [('draft', 'Draft'), ('unpaid', 'Unpaid'), ('paid', 'Paid'),
              ('overdue', 'Overdue'), ('cancelled', 'Cancelled')]
    business    = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_invoices')
    invoice_id  = models.CharField(max_length=30)
    order_ref   = models.CharField(max_length=30, blank=True)
    buyer_name  = models.CharField(max_length=100)
    amount      = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    issue_date  = models.DateField(null=True, blank=True)
    due_date    = models.DateField(null=True, blank=True)
    status      = models.CharField(max_length=15, choices=STATUS, default='unpaid')
    document    = models.FileField(upload_to='factory_ops/invoices/', blank=True, null=True)
    notes       = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-issue_date']

    def __str__(self):
        return f"{self.invoice_id} — {self.buyer_name}"

    @property
    def is_overdue(self):
        return bool(self.due_date and self.status not in ('paid', 'cancelled')
                    and self.due_date < timezone.now().date())


class Vendor(models.Model):
    STATUS = [('active', 'Active'), ('inactive', 'Inactive'), ('suspended', 'Suspended')]
    business      = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_vendors')
    vendor_id     = models.CharField(max_length=30)
    name          = models.CharField(max_length=200)
    category      = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='Other')
    contact       = models.CharField(max_length=100, blank=True)
    email         = models.EmailField(blank=True)
    phone         = models.CharField(max_length=50, blank=True)
    payment_terms = models.CharField(max_length=100, blank=True)
    status        = models.CharField(max_length=15, choices=STATUS, default='active')
    notes         = models.TextField(blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class VendorPO(models.Model):
    STATUS = [('open', 'Open'), ('partial', 'Partial'), ('received', 'Received'), ('cancelled', 'Cancelled')]
    business          = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_vendor_pos')
    po_id             = models.CharField(max_length=30)
    vendor_name       = models.CharField(max_length=200)
    items_description = models.TextField()
    value             = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    order_date        = models.DateField(null=True, blank=True)
    expected_date     = models.DateField(null=True, blank=True)
    received_pct      = models.PositiveSmallIntegerField(default=0)
    status            = models.CharField(max_length=15, choices=STATUS, default='open')
    document          = models.FileField(upload_to='factory_ops/pos/', blank=True, null=True)
    notes             = models.TextField(blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-order_date']

    def __str__(self):
        return f"{self.po_id} — {self.vendor_name}"


class SupplierScore(models.Model):
    SUPPLIER_STATUS = [('preferred', 'Preferred'), ('approved', 'Approved'),
                       ('watch', 'Watch'), ('suspended', 'Suspended')]
    PRICE_RATING    = [('low_cost', 'Low Cost'), ('competitive', 'Competitive'), ('premium', 'Premium')]
    business      = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_supplier_scores')
    vendor_name   = models.CharField(max_length=200)
    category      = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='Other')
    orders_ytd    = models.PositiveSmallIntegerField(default=0)
    on_time_pct   = models.PositiveSmallIntegerField(default=0)
    quality_pct   = models.PositiveSmallIntegerField(default=0)
    defect_rate   = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    price_rating  = models.CharField(max_length=15, choices=PRICE_RATING, default='competitive')
    status        = models.CharField(max_length=15, choices=SUPPLIER_STATUS, default='approved')
    notes         = models.TextField(blank=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-on_time_pct']

    def __str__(self):
        return self.vendor_name

    @property
    def composite_score(self):
        return round(self.on_time_pct * 0.4 + self.quality_pct * 0.6, 1)


# ─── DISTRIBUTION & SALES FORCE ───────────────────────────────────────────────

class DistributionChannel(models.Model):
    CHANNEL_TYPE = [('Distributor', 'Distributor'), ('Sub-Distributor', 'Sub-Distributor'),
                    ('Own Outlet', 'Own Outlet'), ('Online', 'Online')]
    STATUS = [('active', 'Active'), ('inactive', 'Inactive'), ('onboarding', 'Onboarding')]
    business     = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_distribution')
    channel_id   = models.CharField(max_length=30)
    name         = models.CharField(max_length=200)
    channel_type = models.CharField(max_length=20, choices=CHANNEL_TYPE, default='Distributor')
    region       = models.CharField(max_length=100, blank=True)
    contact      = models.CharField(max_length=100, blank=True)
    coverage     = models.CharField(max_length=200, blank=True)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ytd_sales    = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status       = models.CharField(max_length=15, choices=STATUS, default='active')
    notes        = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['region', 'name']

    def __str__(self):
        return self.name


class WholesaleAccount(models.Model):
    STATUS = [('active', 'Active'), ('inactive', 'Inactive'), ('dormant', 'Dormant')]
    business      = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_wholesale')
    account_id    = models.CharField(max_length=30)
    name          = models.CharField(max_length=200)
    location      = models.CharField(max_length=100, blank=True)
    buyer_type    = models.CharField(max_length=50, blank=True)
    payment_terms = models.CharField(max_length=100, blank=True)
    credit_limit  = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    outstanding   = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ytd_volume    = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status        = models.CharField(max_length=15, choices=STATUS, default='active')
    notes         = models.TextField(blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-ytd_volume']

    def __str__(self):
        return self.name


class SalesRep(models.Model):
    STATUS = [('active', 'Active'), ('probation', 'Probation'), ('inactive', 'Inactive')]
    business       = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_sales_reps')
    rep_id         = models.CharField(max_length=30)
    name           = models.CharField(max_length=100)
    role           = models.CharField(max_length=100, blank=True)
    territory      = models.CharField(max_length=100, blank=True)
    joined_date    = models.DateField(null=True, blank=True)
    monthly_target = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    mtd_achieved   = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    accounts_count = models.PositiveSmallIntegerField(default=0)
    status         = models.CharField(max_length=15, choices=STATUS, default='active')
    notes          = models.TextField(blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-mtd_achieved']

    def __str__(self):
        return self.name

    @property
    def attainment_pct(self):
        return int(float(self.mtd_achieved) / float(self.monthly_target) * 100) if self.monthly_target else 0


class SalesTarget(models.Model):
    STATUS = [('on_track', 'On Track'), ('at_risk', 'At Risk'),
              ('achieved', 'Achieved'), ('upcoming', 'Upcoming'), ('missed', 'Missed')]
    business       = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_sales_targets')
    target_id      = models.CharField(max_length=30)
    period         = models.CharField(max_length=50)
    scope          = models.CharField(max_length=50, blank=True)
    owner_name     = models.CharField(max_length=100, blank=True)
    target_value   = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    achieved_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    channel        = models.CharField(max_length=50, blank=True)
    status         = models.CharField(max_length=15, choices=STATUS, default='on_track')
    notes          = models.TextField(blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.target_id} — {self.period}"

    @property
    def attainment_pct(self):
        return int(float(self.achieved_value) / float(self.target_value) * 100) if self.target_value else 0


class FactoryTask(models.Model):
    PRIORITY = [('low', 'Low'), ('med', 'Medium'), ('high', 'High')]
    STATUS   = [('todo', 'To Do'), ('in_progress', 'In Progress'), ('done', 'Done'), ('cancelled', 'Cancelled')]
    business  = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_tasks')
    task_id   = models.CharField(max_length=30)
    title     = models.CharField(max_length=200)
    assignee  = models.CharField(max_length=100, blank=True)
    priority  = models.CharField(max_length=10, choices=PRIORITY, default='med')
    due_date  = models.DateField(null=True, blank=True)
    category  = models.CharField(max_length=100, blank=True)
    status    = models.CharField(max_length=15, choices=STATUS, default='todo')
    notes     = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['due_date', '-priority']

    def __str__(self):
        return f"{self.task_id} — {self.title}"

    @property
    def is_overdue(self):
        return bool(self.due_date and self.status not in ('done', 'cancelled')
                    and self.due_date < timezone.now().date())


class MarketingCampaign(models.Model):
    STATUS  = [('planned', 'Planned'), ('active', 'Active'), ('completed', 'Completed'), ('cancelled', 'Cancelled')]
    CHANNEL = [('Digital', 'Digital'), ('Trade', 'Trade'), ('Content', 'Content'),
               ('Event', 'Event'), ('Print', 'Print'), ('Mixed', 'Mixed')]
    business    = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_campaigns')
    campaign_id = models.CharField(max_length=30)
    name        = models.CharField(max_length=200)
    channel     = models.CharField(max_length=20, choices=CHANNEL, default='Digital')
    budget      = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    spent       = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    start_date  = models.DateField(null=True, blank=True)
    end_date    = models.DateField(null=True, blank=True)
    status      = models.CharField(max_length=15, choices=STATUS, default='planned')
    notes       = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.campaign_id} — {self.name}"

    @property
    def budget_utilization_pct(self):
        return int(float(self.spent) / float(self.budget) * 100) if self.budget else 0


# ─── FINANCE & ADMIN ──────────────────────────────────────────────────────────

class ARAPEntry(models.Model):
    TYPE   = [('receivable', 'Receivable'), ('payable', 'Payable')]
    STATUS = [('open', 'Open'), ('overdue', 'Overdue'), ('paid', 'Paid'), ('cancelled', 'Cancelled')]
    business    = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_arap')
    entry_id    = models.CharField(max_length=30)
    entry_type  = models.CharField(max_length=15, choices=TYPE, default='receivable')
    party       = models.CharField(max_length=200)
    invoice_ref = models.CharField(max_length=50, blank=True)
    amount      = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    due_date    = models.DateField(null=True, blank=True)
    status      = models.CharField(max_length=15, choices=STATUS, default='open')
    notes       = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['due_date']

    def __str__(self):
        return f"{self.entry_id} — {self.party}"

    @property
    def is_overdue(self):
        return bool(self.due_date and self.status not in ('paid', 'cancelled')
                    and self.due_date < timezone.now().date())


class BankAccount(models.Model):
    CURRENCY = [('BDT', 'BDT'), ('USD', 'USD'), ('EUR', 'EUR'), ('GBP', 'GBP')]
    business       = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_bank_accounts')
    account_id     = models.CharField(max_length=30)
    name           = models.CharField(max_length=200)
    bank           = models.CharField(max_length=200)
    account_number = models.CharField(max_length=50, blank=True)
    currency       = models.CharField(max_length=5, choices=CURRENCY, default='BDT')
    balance        = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    last_txn_date  = models.DateField(null=True, blank=True)
    is_active      = models.BooleanField(default=True)
    notes          = models.TextField(blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-balance']

    def __str__(self):
        return f"{self.name} — {self.bank}"


class LetterOfCredit(models.Model):
    STATUS = [('active', 'Active'), ('pending', 'Pending'), ('expired', 'Expired'), ('utilised', 'Utilised')]
    business     = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_letters_of_credit')
    lc_id        = models.CharField(max_length=30)
    description  = models.CharField(max_length=200)
    bank         = models.CharField(max_length=200)
    beneficiary  = models.CharField(max_length=200, blank=True)
    value        = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency     = models.CharField(max_length=5, default='BDT')
    expiry_date  = models.DateField(null=True, blank=True)
    status       = models.CharField(max_length=15, choices=STATUS, default='active')
    notes        = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['expiry_date']

    def __str__(self):
        return f"{self.lc_id} — {self.description}"

    @property
    def is_expiring_soon(self):
        if self.expiry_date and self.status == 'active':
            return 0 <= (self.expiry_date - timezone.now().date()).days <= 30
        return False


class FactoryEmployee(models.Model):
    DEPT = [
        ('Production', 'Production'), ('Cutting', 'Cutting'), ('Stitching', 'Stitching'),
        ('Lasting', 'Lasting'), ('Finishing', 'Finishing'), ('Quality', 'Quality'),
        ('Commercial', 'Commercial'), ('Design', 'Design'), ('IE', 'Industrial Engineering'),
        ('Store', 'Store'), ('Admin', 'Admin'), ('Finance', 'Finance'),
    ]
    STATUS = [('active', 'Active'), ('probation', 'Probation'), ('inactive', 'Inactive'), ('resigned', 'Resigned')]
    business           = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_employees')
    emp_id             = models.CharField(max_length=30)
    name               = models.CharField(max_length=100)
    designation        = models.CharField(max_length=100)
    department         = models.CharField(max_length=30, choices=DEPT, default='Production')
    joined_date        = models.DateField(null=True, blank=True)
    salary             = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    monthly_attendance = models.CharField(max_length=20, blank=True)
    status             = models.CharField(max_length=15, choices=STATUS, default='active')
    notes              = models.TextField(blank=True)
    created_at         = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['department', 'name']

    def __str__(self):
        return f"{self.emp_id} — {self.name}"


class ApprovalRequest(models.Model):
    TYPE = [
        ('supplier_payment', 'Bulk Supplier Payment'), ('payroll', 'Monthly Payroll'),
        ('capex', 'Capital Expenditure'), ('discount', 'Discount Approval'),
        ('loan', 'Term Loan / Drawdown'), ('other', 'Other'),
    ]
    STATUS = [('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')]
    business     = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_approvals')
    request_id   = models.CharField(max_length=30)
    request_date = models.DateField()
    request_type = models.CharField(max_length=25, choices=TYPE, default='other')
    requested_by = models.CharField(max_length=100)
    amount       = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    party        = models.CharField(max_length=200)
    status       = models.CharField(max_length=15, choices=STATUS, default='pending')
    review_notes = models.TextField(blank=True)
    notes        = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-request_date']

    def __str__(self):
        return f"{self.request_id} — {self.get_request_type_display()}"


# ─── FLOOR MANAGEMENT ─────────────────────────────────────────────────────────

class HourlyProductionEntry(models.Model):
    business          = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_hourly_entries')
    entry_date        = models.DateField()
    line              = models.CharField(max_length=50)
    hour_slot         = models.CharField(max_length=10)  # '08:00', '09:00', etc.
    target            = models.PositiveSmallIntegerField(default=0)
    actual            = models.PositiveSmallIntegerField(default=0)
    root_cause        = models.CharField(max_length=200, blank=True)
    corrective_action = models.CharField(max_length=200, blank=True)
    action_owner      = models.CharField(max_length=100, blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['entry_date', 'line', 'hour_slot']
        unique_together = ['business', 'entry_date', 'line', 'hour_slot']

    def __str__(self):
        return f"{self.entry_date} {self.line} {self.hour_slot}"

    @property
    def achievement_pct(self):
        return round(self.actual / self.target * 100, 1) if self.target else 100

    @property
    def status(self):
        pct = self.achievement_pct
        if pct >= 98:
            return 'green'
        elif pct >= 90:
            return 'amber'
        return 'red'


class PettyCash(models.Model):
    CATEGORY = [
        ('supplies', 'Office/Factory Supplies'), ('transport', 'Transport/Conveyance'),
        ('utilities', 'Utilities & Bills'), ('meals', 'Staff Meals'),
        ('maintenance', 'Repairs & Maintenance'), ('other', 'Other'),
    ]
    business    = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_petty_cash')
    voucher_id  = models.CharField(max_length=30)
    txn_date    = models.DateField()
    description = models.CharField(max_length=200)
    category    = models.CharField(max_length=20, choices=CATEGORY, default='other')
    amount      = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_to     = models.CharField(max_length=100, blank=True)
    receipt_ref = models.CharField(max_length=50, blank=True)
    notes       = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-txn_date']

    def __str__(self):
        return f"{self.voucher_id} — {self.description}"

    @property
    def requires_approval(self):
        return float(self.amount) > 5000


class WorkerAdvance(models.Model):
    STATUS = [('outstanding', 'Outstanding'), ('recovering', 'Recovering'), ('recovered', 'Fully Recovered')]
    business           = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_worker_advances')
    advance_id         = models.CharField(max_length=30)
    employee_name      = models.CharField(max_length=100)
    emp_id_ref         = models.CharField(max_length=30, blank=True)
    date_issued        = models.DateField()
    amount             = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    purpose            = models.CharField(max_length=200)
    recovery_per_month = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_recovered   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status             = models.CharField(max_length=15, choices=STATUS, default='outstanding')
    notes              = models.TextField(blank=True)
    created_at         = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_issued']

    def __str__(self):
        return f"{self.advance_id} — {self.employee_name}"

    @property
    def balance_outstanding(self):
        return float(self.amount) - float(self.amount_recovered)


# ─── FACTORY SETTINGS ─────────────────────────────────────────────────────────

class FactorySettings(models.Model):
    """Per-business configurable constants used in financial statements."""
    business           = models.OneToOneField(BusinessInstance, on_delete=models.CASCADE, related_name='fo_settings')
    # Financial statement baselines
    fixed_assets       = models.DecimalField(max_digits=16, decimal_places=2, default=25_000_000,
                             help_text='Plant, machinery & equipment value (BDT)')
    long_term_debt     = models.DecimalField(max_digits=16, decimal_places=2, default=15_000_000,
                             help_text='Outstanding term loans (BDT)')
    interest_rate_pct  = models.DecimalField(max_digits=5, decimal_places=2, default=9.00,
                             help_text='Annual interest rate on long-term debt (%)')
    tax_rate_pct       = models.DecimalField(max_digits=5, decimal_places=2, default=27.50,
                             help_text='Effective corporate tax rate (%)')
    cogs_estimate_pct  = models.DecimalField(max_digits=5, decimal_places=2, default=68.00,
                             help_text='COGS as % of revenue when FG cost data is unavailable')
    currency           = models.CharField(max_length=5, default='BDT')
    # Factory identity (used on invoices and print headers)
    factory_address    = models.TextField(blank=True)
    tax_id             = models.CharField(max_length=50, blank=True, verbose_name='BIN / TIN / Tax ID')
    bank_details       = models.TextField(blank=True, help_text='Bank name, account, routing — shown on invoices')
    # Operational defaults
    working_hours_per_day = models.PositiveSmallIntegerField(default=8)
    petty_cash_limit   = models.DecimalField(max_digits=10, decimal_places=2, default=5000,
                             help_text='Auto-approve threshold (BDT)')
    manager_approval_limit = models.DecimalField(max_digits=10, decimal_places=2, default=25000,
                             help_text='Manager approval ceiling; above this → CEO approval')
    updated_at         = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Settings — {self.business.name}"

    @property
    def interest_rate(self):
        return float(self.interest_rate_pct) / 100

    @property
    def tax_rate(self):
        return float(self.tax_rate_pct) / 100

    @property
    def cogs_rate(self):
        return float(self.cogs_estimate_pct) / 100


# ─── STOCK MOVEMENT LOG ───────────────────────────────────────────────────────

class StockMovement(models.Model):
    """Immutable log of every stock-level change for raw materials and product SKUs."""
    MOVE_TYPE = [
        ('in',       'Stock In'),
        ('out',      'Stock Out / Issue'),
        ('adjust',   'Manual Adjustment'),
        ('rework',   'Rework Write-off'),
        ('transfer', 'Transfer'),
    ]
    ITEM_TYPE = [('raw', 'Raw Material'), ('sku', 'Product SKU')]

    business    = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_stock_movements')
    item_type   = models.CharField(max_length=5, choices=ITEM_TYPE, default='raw')
    item_ref    = models.CharField(max_length=30, help_text='item_id or sku_id of the related item')
    item_name   = models.CharField(max_length=200)
    move_type   = models.CharField(max_length=10, choices=MOVE_TYPE, default='adjust')
    qty_before  = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    qty_change  = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                      help_text='Positive = increase, negative = decrease')
    qty_after   = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reference   = models.CharField(max_length=100, blank=True, help_text='PO ref, issue ID, reason')
    performed_by = models.CharField(max_length=100, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d} {self.item_name} {self.move_type} {self.qty_change:+}"


# ─── PERFORMANCE & INCENTIVES ─────────────────────────────────────────────────

class KPITemplate(models.Model):
    DEPT = [
        ('Production', 'Production'), ('Cutting', 'Cutting'), ('Stitching', 'Stitching'),
        ('Lasting', 'Lasting'), ('Finishing', 'Finishing'), ('Quality', 'Quality'),
        ('Commercial', 'Commercial'), ('Design', 'Design'), ('IE', 'Industrial Engineering'),
        ('Store', 'Store'), ('Admin', 'Admin'), ('Finance', 'Finance'), ('Sales', 'Sales'),
    ]
    business            = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_kpi_templates')
    role                = models.CharField(max_length=100)
    department          = models.CharField(max_length=30, choices=DEPT, default='Production')
    criteria            = models.JSONField(default=list, help_text='[{name, weight, description}]')
    bonus_pct_of_salary = models.DecimalField(max_digits=5, decimal_places=2, default=10.00,
                              help_text='Max bonus as % of monthly salary when score = 100')
    is_active           = models.BooleanField(default=True)
    notes               = models.TextField(blank=True)
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['department', 'role']

    def __str__(self):
        return f"{self.role} — {self.department}"

    @property
    def total_weight(self):
        return sum(c.get('weight', 0) for c in (self.criteria or []))


class EmployeeEvaluation(models.Model):
    STATUS = [('draft', 'Draft'), ('submitted', 'Submitted'), ('approved', 'Approved')]
    business      = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_evaluations')
    template      = models.ForeignKey(KPITemplate, on_delete=models.SET_NULL, null=True, blank=True,
                        related_name='evaluations')
    employee      = models.ForeignKey(FactoryEmployee, on_delete=models.SET_NULL, null=True, blank=True,
                        related_name='evaluations')
    employee_name = models.CharField(max_length=100)
    role          = models.CharField(max_length=100, blank=True)
    period_month  = models.PositiveSmallIntegerField()
    period_year   = models.PositiveSmallIntegerField()
    scores        = models.JSONField(default=list, help_text='[{name, weight, score, remarks}]')
    salary_ref    = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                        help_text='Monthly salary used for bonus calculation')
    status        = models.CharField(max_length=15, choices=STATUS, default='draft')
    evaluated_by  = models.CharField(max_length=100, blank=True)
    notes         = models.TextField(blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-period_year', '-period_month', 'employee_name']

    def __str__(self):
        return f"{self.employee_name} — {self.period_month}/{self.period_year}"

    @property
    def weighted_score(self):
        total_w = sum(s.get('weight', 0) for s in (self.scores or []))
        if not total_w:
            return 0
        return round(sum(s.get('score', 0) * s.get('weight', 0) for s in self.scores) / total_w, 1)

    @property
    def bonus_pct(self):
        if self.template:
            return float(self.template.bonus_pct_of_salary) * self.weighted_score / 100
        return 0

    @property
    def bonus_amount(self):
        return round(float(self.salary_ref) * self.bonus_pct / 100, 2)


class SalesIncentive(models.Model):
    STATUS = [('draft', 'Draft'), ('approved', 'Approved'), ('paid', 'Paid')]
    business              = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_sales_incentives')
    employee_name         = models.CharField(max_length=100)
    period_month          = models.PositiveSmallIntegerField()
    period_year           = models.PositiveSmallIntegerField()
    pairs_sold            = models.PositiveIntegerField(default=0)
    rate_per_pair         = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    new_accounts          = models.PositiveSmallIntegerField(default=0)
    bonus_per_account     = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    collection_achieved   = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    collection_target     = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    collection_bonus_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                help_text='% of achieved collection paid as bonus (only if target met)')
    status                = models.CharField(max_length=15, choices=STATUS, default='draft')
    notes                 = models.TextField(blank=True)
    created_at            = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-period_year', '-period_month', 'employee_name']

    def __str__(self):
        return f"{self.employee_name} — {self.period_month}/{self.period_year}"

    @property
    def pairs_incentive(self):
        return float(self.pairs_sold) * float(self.rate_per_pair)

    @property
    def accounts_incentive(self):
        return float(self.new_accounts) * float(self.bonus_per_account)

    @property
    def collection_incentive(self):
        if self.collection_target and float(self.collection_achieved) >= float(self.collection_target):
            return float(self.collection_achieved) * float(self.collection_bonus_rate) / 100
        return 0

    @property
    def total_incentive(self):
        return round(self.pairs_incentive + self.accounts_incentive + self.collection_incentive, 2)

    @property
    def collection_pct(self):
        if self.collection_target:
            return round(float(self.collection_achieved) / float(self.collection_target) * 100, 1)
        return 0


# ─── SAMPLE DEVELOPMENT ───────────────────────────────────────────────────────

class SampleOrder(models.Model):
    STATUS = [
        ('pending', 'Pending'), ('in_progress', 'In Progress'),
        ('ready_for_approval', 'Ready for Approval'),
        ('approved', 'Approved'), ('rejected', 'Rejected'), ('shipped', 'Shipped'),
    ]
    PRIORITY = [('standard', 'Standard'), ('urgent', 'Urgent'), ('critical', 'Critical')]
    SAMPLE_TYPE = [
        ('proto', 'Proto Sample'), ('fit', 'Fit Sample'),
        ('pre_production', 'Pre-Production Sample'), ('production', 'Production Sample'),
        ('marketing', 'Marketing Sample'),
    ]
    LAST_TYPE = [('flat', 'Flat'), ('heeled', 'Heeled'), ('platform', 'Platform'), ('custom', 'Custom')]
    CONSTRUCTION = [
        ('cement', 'Cement / Stuck-on'), ('goodyear', 'Goodyear Welt'),
        ('blake', 'Blake Stitch'), ('injection', 'Direct Injection'),
        ('vulcanize', 'Vulcanize'), ('string', 'String Lasting'),
    ]
    business          = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fo_sample_orders')
    order_ref         = models.CharField(max_length=30)
    requested_by      = models.CharField(max_length=100, blank=True, verbose_name='Merchandiser / Requester')
    buyer_name        = models.CharField(max_length=100, blank=True)
    style_name        = models.CharField(max_length=200)
    style_ref         = models.CharField(max_length=50, blank=True)
    target_date       = models.DateField(null=True, blank=True)
    sample_type       = models.CharField(max_length=20, choices=SAMPLE_TYPE, default='proto')
    priority          = models.CharField(max_length=15, choices=PRIORITY, default='standard')
    status            = models.CharField(max_length=25, choices=STATUS, default='pending')

    # Last / mould
    last_number       = models.CharField(max_length=50, blank=True)
    last_type         = models.CharField(max_length=15, choices=LAST_TYPE, blank=True)
    heel_height_mm    = models.PositiveSmallIntegerField(null=True, blank=True)
    toe_allowance_mm  = models.PositiveSmallIntegerField(null=True, blank=True)
    heel_allowance_mm = models.PositiveSmallIntegerField(null=True, blank=True)
    ball_allowance_mm = models.PositiveSmallIntegerField(null=True, blank=True)

    # Materials [{part, material_name, color, thickness, unit, qty_per_pair}]
    materials         = models.JSONField(default=list)

    # Thread & adhesive
    thread_color      = models.CharField(max_length=100, blank=True)
    thread_count      = models.CharField(max_length=50, blank=True)
    adhesive_type     = models.CharField(max_length=100, blank=True)
    primer_required   = models.BooleanField(default=False)

    # Construction
    construction_type = models.CharField(max_length=20, choices=CONSTRUCTION, default='cement')
    process_steps     = models.JSONField(default=list, help_text='[{step_no, operation, machine, notes}]')

    # Problems and instructions
    problems              = models.JSONField(default=list, help_text='[{area, description}]')
    special_instructions  = models.JSONField(default=list)

    # Approval tracking
    assigned_to   = models.CharField(max_length=100, blank=True, verbose_name='Designer / Sampleman')
    approved_by   = models.CharField(max_length=100, blank=True)
    approval_date = models.DateField(null=True, blank=True)
    remarks       = models.TextField(blank=True)
    document      = models.FileField(upload_to='factory_ops/sample_orders/', blank=True, null=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_ref} — {self.style_name}"

    @property
    def is_overdue(self):
        return bool(self.target_date and self.status not in ('approved', 'shipped', 'rejected')
                    and self.target_date < timezone.now().date())
