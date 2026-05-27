from django.db import models
from django.utils import timezone
from accounts.models import User


class Asset(models.Model):
    TYPE = [('equipment', 'Equipment'), ('vehicle', 'Vehicle'), ('building', 'Building'), ('it', 'IT Asset'), ('tool', 'Tool'), ('other', 'Other')]
    STATUS = [('operational', 'Operational'), ('under_maintenance', 'Under Maintenance'), ('out_of_service', 'Out of Service'), ('disposed', 'Disposed')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='maint_assets')
    name = models.CharField(max_length=200)
    asset_id = models.CharField(max_length=50, blank=True)
    asset_type = models.CharField(max_length=20, choices=TYPE, default='equipment')
    location = models.CharField(max_length=200, blank=True)
    department = models.CharField(max_length=100, blank=True)
    manufacturer = models.CharField(max_length=100, blank=True)
    model_number = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    purchase_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    warranty_expires = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=25, choices=STATUS, default='operational')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_assets')
    image = models.ImageField(upload_to='maintenance/assets/', null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.asset_id or 'No ID'})"

    @property
    def is_under_warranty(self):
        return self.warranty_expires and self.warranty_expires >= timezone.now().date()


class MaintenanceSchedule(models.Model):
    FREQ = [('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('annual', 'Annual'), ('as_needed', 'As Needed')]

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='schedules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    frequency = models.CharField(max_length=20, choices=FREQ, default='monthly')
    next_due = models.DateField()
    last_done = models.DateField(null=True, blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='maintenance_schedules')
    is_active = models.BooleanField(default=True)
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=1, default=0)

    class Meta:
        ordering = ['next_due']

    def __str__(self):
        return f"{self.title} — {self.asset}"


class WorkOrder(models.Model):
    PRIORITY = [('low', 'Low'), ('normal', 'Normal'), ('high', 'High'), ('urgent', 'Urgent')]
    STATUS = [('open', 'Open'), ('assigned', 'Assigned'), ('in_progress', 'In Progress'), ('on_hold', 'On Hold'), ('completed', 'Completed'), ('cancelled', 'Cancelled')]
    TYPE = [('corrective', 'Corrective'), ('preventive', 'Preventive'), ('predictive', 'Predictive'), ('emergency', 'Emergency')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='work_orders')
    wo_number = models.CharField(max_length=30)
    asset = models.ForeignKey(Asset, on_delete=models.SET_NULL, null=True, blank=True, related_name='work_orders')
    schedule = models.ForeignKey(MaintenanceSchedule, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    work_type = models.CharField(max_length=20, choices=TYPE, default='corrective')
    priority = models.CharField(max_length=10, choices=PRIORITY, default='normal')
    status = models.CharField(max_length=20, choices=STATUS, default='open')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_work_orders')
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reported_work_orders')
    scheduled_date = models.DateField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    downtime_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    labor_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    parts_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    completion_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"WO-{self.wo_number}: {self.title}"

    @property
    def total_cost(self):
        return self.labor_cost + self.parts_cost
