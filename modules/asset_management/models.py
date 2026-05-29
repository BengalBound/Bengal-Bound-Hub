from django.db import models
from django.utils import timezone


class AssetCategory(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='asset_categories')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, blank=True)
    useful_life_years = models.PositiveSmallIntegerField(default=5)
    depreciation_rate = models.DecimalField(max_digits=5, decimal_places=2, default=20)  # % per year

    class Meta:
        unique_together = [('business', 'name')]
        ordering = ['name']

    def __str__(self):
        return self.name


class Asset(models.Model):
    STATUS = [
        ('active', 'Active'), ('idle', 'Idle'), ('under_maintenance', 'Under Maintenance'),
        ('retired', 'Retired'), ('disposed', 'Disposed'),
    ]
    CONDITION = [('excellent', 'Excellent'), ('good', 'Good'), ('fair', 'Fair'), ('poor', 'Poor')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='assets')
    asset_tag = models.CharField(max_length=30)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    category = models.ForeignKey(AssetCategory, on_delete=models.SET_NULL, null=True, blank=True)
    serial_number = models.CharField(max_length=80, blank=True)
    manufacturer = models.CharField(max_length=100, blank=True)
    model_number = models.CharField(max_length=80, blank=True)
    location = models.CharField(max_length=150, blank=True)
    assigned_to = models.ForeignKey('bredbound.BusinessEmployee', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_assets')
    status = models.CharField(max_length=25, choices=STATUS, default='active')
    condition = models.CharField(max_length=15, choices=CONDITION, default='good')
    is_tooling = models.BooleanField(default=False, help_text="Is this a consumable tooling asset (e.g., Mold, Die)?")
    lifespan_capacity = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Total expected capacity (e.g., 100,000 shots)")
    lifespan_consumed = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Amount of capacity used so far")
    purchase_date = models.DateField(null=True, blank=True)
    purchase_cost = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    current_value = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    warranty_expiry = models.DateField(null=True, blank=True)
    image = models.ImageField(upload_to='assets/images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('business', 'asset_tag')]
        ordering = ['name']

    def __str__(self):
        return f"{self.asset_tag} — {self.name}"

    @property
    def warranty_status(self):
        if self.warranty_expiry:
            today = timezone.localdate()
            if self.warranty_expiry < today:
                return 'expired'
            elif (self.warranty_expiry - today).days <= 30:
                return 'expiring_soon'
            return 'valid'
        return 'unknown'


class AssetUsageLog(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='usage_logs')
    usage_amount = models.DecimalField(max_digits=12, decimal_places=2)
    recorded_at = models.DateTimeField(default=timezone.now)
    recorded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    reference = models.CharField(max_length=100, blank=True, help_text="Order or batch reference for this usage")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-recorded_at']

    def __str__(self):
        return f"{self.asset.asset_tag} usage: {self.usage_amount}"


class MaintenanceSchedule(models.Model):
    FREQUENCY = [
        ('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'), ('biannual', 'Biannual'), ('annual', 'Annual'),
        ('on_demand', 'On Demand'),
    ]
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='maintenance_schedules')
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    frequency = models.CharField(max_length=20, choices=FREQUENCY)
    next_due = models.DateField()
    assigned_to = models.ForeignKey('bredbound.BusinessEmployee', on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    estimated_duration_hours = models.DecimalField(max_digits=5, decimal_places=1, default=1)

    class Meta:
        ordering = ['next_due']

    def __str__(self):
        return f"{self.asset} — {self.title} ({self.frequency})"


class WorkOrder(models.Model):
    TYPES = [('preventive', 'Preventive'), ('corrective', 'Corrective'), ('inspection', 'Inspection'), ('emergency', 'Emergency')]
    STATUS = [('open', 'Open'), ('assigned', 'Assigned'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled')]
    PRIORITY = [('low', 'Low'), ('normal', 'Normal'), ('high', 'High'), ('critical', 'Critical')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='asset_work_orders')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='work_orders')
    wo_number = models.CharField(max_length=30)
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    work_type = models.CharField(max_length=20, choices=TYPES, default='corrective')
    status = models.CharField(max_length=20, choices=STATUS, default='open')
    priority = models.CharField(max_length=10, choices=PRIORITY, default='normal')
    assigned_to = models.ForeignKey('bredbound.BusinessEmployee', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_work_orders')
    schedule = models.ForeignKey(MaintenanceSchedule, on_delete=models.SET_NULL, null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('business', 'wo_number')]
        ordering = ['-created_at']

    def __str__(self):
        return f"WO-{self.wo_number}: {self.title}"


class AssetDocument(models.Model):
    TYPES = [
        ('manual', 'Manual'), ('warranty', 'Warranty Card'), ('purchase_invoice', 'Purchase Invoice'),
        ('inspection_report', 'Inspection Report'), ('certification', 'Certification'), ('other', 'Other'),
    ]
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='documents')
    doc_type = models.CharField(max_length=25, choices=TYPES)
    title = models.CharField(max_length=150)
    file = models.FileField(upload_to='assets/docs/', null=True, blank=True)
    uploaded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.get_doc_type_display()}: {self.title}"


class AssetDepreciation(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='depreciation_records')
    period_year = models.PositiveSmallIntegerField()
    period_month = models.PositiveSmallIntegerField()
    opening_value = models.DecimalField(max_digits=14, decimal_places=2)
    depreciation_amount = models.DecimalField(max_digits=14, decimal_places=2)
    closing_value = models.DecimalField(max_digits=14, decimal_places=2)
    calculated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('asset', 'period_year', 'period_month')]
        ordering = ['-period_year', '-period_month']
