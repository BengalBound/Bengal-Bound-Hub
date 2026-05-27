from django.db import models
from django.utils import timezone
from accounts.models import User

class AQLStandard(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='qc_aql_standards')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class AQLRule(models.Model):
    standard = models.ForeignKey(AQLStandard, on_delete=models.CASCADE, related_name='rules')
    batch_size_min = models.IntegerField()
    batch_size_max = models.IntegerField()
    sample_size = models.IntegerField()
    accept_threshold = models.IntegerField(help_text="Maximum failed units allowed to still pass the batch")
    reject_threshold = models.IntegerField(help_text="Minimum failed units required to reject the batch")

    class Meta:
        ordering = ['batch_size_min']

    def __str__(self):
        return f"{self.standard.name} ({self.batch_size_min}-{self.batch_size_max})"


class InspectionTemplate(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='qc_templates')
    name = models.CharField(max_length=200)
    product = models.ForeignKey('inventory.Product', on_delete=models.SET_NULL, null=True, blank=True, related_name='inspection_templates')
    aql_standard = models.ForeignKey(AQLStandard, on_delete=models.SET_NULL, null=True, blank=True, help_text="AQL standard applied for sample sizing")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class InspectionCriterion(models.Model):
    TYPE = [('pass_fail', 'Pass/Fail'), ('numeric', 'Numeric'), ('text', 'Text')]
    template = models.ForeignKey(InspectionTemplate, on_delete=models.CASCADE, related_name='criteria')
    name = models.CharField(max_length=200)
    criterion_type = models.CharField(max_length=20, choices=TYPE, default='pass_fail')
    min_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    unit = models.CharField(max_length=20, blank=True)
    is_required = models.BooleanField(default=True)
    position = models.IntegerField(default=0)

    class Meta:
        ordering = ['position']

    def __str__(self):
        return self.name


class Inspection(models.Model):
    TYPE = [('incoming', 'Incoming'), ('in_process', 'In-Process'), ('final', 'Final'), ('audit', 'Audit')]
    RESULT = [('pending', 'Pending'), ('pass', 'Passed'), ('fail', 'Failed'), ('conditional', 'Conditional')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='qc_inspections')
    template = models.ForeignKey(InspectionTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    inspection_type = models.CharField(max_length=20, choices=TYPE, default='final')
    reference = models.CharField(max_length=100, blank=True)
    product = models.ForeignKey('inventory.Product', on_delete=models.SET_NULL, null=True, blank=True)
    lot_number = models.CharField(max_length=50, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sample_size_tested = models.IntegerField(null=True, blank=True, help_text="Number of units actually tested (from AQL)")
    failed_sample_count = models.IntegerField(null=True, blank=True, help_text="Number of failed units found in the sample")
    inspector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='inspections_conducted')
    scheduled_date = models.DateField(default=timezone.now)
    completed_date = models.DateField(null=True, blank=True)
    result = models.CharField(max_length=20, choices=RESULT, default='pending')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-scheduled_date', '-created_at']

    def __str__(self):
        return f"Inspection #{self.pk} — {self.product} ({self.get_result_display()})"


class InspectionResult(models.Model):
    RESULT = [('pass', 'Pass'), ('fail', 'Fail'), ('na', 'N/A')]
    inspection = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name='results')
    criterion = models.ForeignKey(InspectionCriterion, on_delete=models.SET_NULL, null=True)
    criterion_name = models.CharField(max_length=200)
    result = models.CharField(max_length=10, choices=RESULT, blank=True)
    value = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.criterion_name}: {self.result}"


class NonConformance(models.Model):
    SEVERITY = [('minor', 'Minor'), ('major', 'Major'), ('critical', 'Critical')]
    STATUS = [('open', 'Open'), ('in_review', 'In Review'), ('resolved', 'Resolved'), ('closed', 'Closed')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='qc_nonconformances')
    inspection = models.ForeignKey(Inspection, on_delete=models.SET_NULL, null=True, blank=True, related_name='nonconformances')
    title = models.CharField(max_length=200)
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY, default='minor')
    status = models.CharField(max_length=20, choices=STATUS, default='open')
    root_cause = models.TextField(blank=True)
    corrective_action = models.TextField(blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_ncrs')
    due_date = models.DateField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_ncrs')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"NCR #{self.pk}: {self.title}"


# ── Footwear QC Extensions ────────────────────────────────────────────────────

class ShoeDefectRecord(models.Model):
    """Defect log at any of the four footwear inspection gates."""
    STAGE = [
        ('incoming', 'Incoming Raw Material'),
        ('inline_cutting', 'In-line — Cutting & Closing'),
        ('inline_lasting', 'In-line — Lasting & Bottom'),
        ('final_prepack', 'Final Pre-Pack'),
    ]
    SEVERITY = [
        ('critical', 'Critical (Zero Tolerance)'),
        ('major', 'Major'),
        ('minor', 'Minor'),
    ]
    AQL_LEVEL = [
        ('1.5', 'AQL 1.5'),
        ('2.5', 'AQL 2.5'),
        ('4.0', 'AQL 4.0'),
    ]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='shoe_defect_records')
    inspection_stage = models.CharField(max_length=20, choices=STAGE)
    inspection_date = models.DateField(default=timezone.now)
    article_code = models.CharField(max_length=50, blank=True)
    lot_reference = models.CharField(max_length=100, blank=True)
    pairs_inspected = models.PositiveIntegerField(default=0)
    pairs_affected = models.PositiveIntegerField(default=0)
    defect_description = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY, default='minor')
    aql_level = models.CharField(max_length=5, choices=AQL_LEVEL, blank=True)
    root_cause = models.TextField(blank=True)
    corrective_action = models.TextField(blank=True)
    peel_test_result = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        help_text="N/mm result — applies to Lasting & Bottom stage (pass ≥ 3.5 N/mm)"
    )
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='shoe_defects_recorded')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_inspection_stage_display()} — {self.get_severity_display()} ({self.pairs_affected} pairs)"

    @property
    def defect_rate_per_100(self):
        if self.pairs_inspected:
            return round(self.pairs_affected / self.pairs_inspected * 100, 2)
        return 0

    @property
    def peel_test_pass(self):
        if self.peel_test_result is None:
            return None
        return self.peel_test_result >= 3.5
