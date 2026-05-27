from django.db import models
from django.utils import timezone


class ServiceBay(models.Model):
    STATUS = [('available', 'Available'), ('occupied', 'Occupied'), ('maintenance', 'Under Maintenance'), ('inactive', 'Inactive')]
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='service_bays')
    name = models.CharField(max_length=60)  # e.g. "Bay 1", "Lift 2"
    bay_type = models.CharField(max_length=40, blank=True)  # e.g. Hydraulic Lift, Drive-through
    status = models.CharField(max_length=20, choices=STATUS, default='available')

    class Meta:
        unique_together = [('business', 'name')]
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class JobCard(models.Model):
    STATUS = [
        ('received', 'Received'), ('diagnosing', 'Diagnosing'),
        ('in_progress', 'In Progress'), ('waiting_parts', 'Waiting for Parts'),
        ('waiting_approval', 'Waiting Customer Approval'),
        ('ready', 'Ready for Collection'), ('collected', 'Collected'),
        ('invoiced', 'Invoiced & Closed'), ('cancelled', 'Cancelled'),
    ]
    PRIORITY = [('low', 'Low'), ('normal', 'Normal'), ('high', 'High'), ('urgent', 'Urgent')]
    SERVICE_TYPES = [
        ('oil_change', 'Oil & Filter Change'), ('service_a', 'Service A (Minor)'), ('service_b', 'Service B (Major)'),
        ('diagnostics', 'Diagnostics'), ('repair', 'Repair'), ('tyres', 'Tyre Replacement'),
        ('brakes', 'Brake Service'), ('electrical', 'Electrical Fault'), ('ac', 'Air Conditioning'),
        ('body_work', 'Body Work'), ('pre_purchase', 'Pre-Purchase Inspection'),
        ('warranty', 'Warranty Repair'), ('recall', 'Recall / Campaign'), ('other', 'Other'),
    ]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='job_cards')
    job_number = models.CharField(max_length=20)

    # Customer
    customer_name = models.CharField(max_length=150)
    customer_phone = models.CharField(max_length=30, blank=True)
    customer_email = models.EmailField(blank=True)

    # Vehicle
    vehicle_make = models.CharField(max_length=60)
    vehicle_model = models.CharField(max_length=60, blank=True)
    vehicle_year = models.PositiveSmallIntegerField(null=True, blank=True)
    vehicle_reg = models.CharField(max_length=30, blank=True)
    vin = models.CharField(max_length=50, blank=True, verbose_name='VIN')
    colour = models.CharField(max_length=40, blank=True)
    mileage_in = models.PositiveIntegerField(null=True, blank=True)
    mileage_out = models.PositiveIntegerField(null=True, blank=True)
    fuel_level = models.CharField(max_length=10, blank=True)  # E, 1/4, 1/2, 3/4, F

    # Job
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES, default='repair')
    status = models.CharField(max_length=25, choices=STATUS, default='received')
    priority = models.CharField(max_length=10, choices=PRIORITY, default='normal')
    bay = models.ForeignKey(ServiceBay, on_delete=models.SET_NULL, null=True, blank=True, related_name='job_cards')
    assigned_to = models.ForeignKey('bredbound.BusinessEmployee', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_jobs')

    # Details
    customer_complaint = models.TextField(blank=True)
    diagnosis = models.TextField(blank=True)
    work_done = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)

    # Dates
    received_at = models.DateTimeField(default=timezone.now)
    estimated_completion = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    collected_at = models.DateTimeField(null=True, blank=True)

    # Notification
    customer_notified = models.BooleanField(default=False)
    notification_method = models.CharField(max_length=10, choices=[('sms', 'SMS'), ('email', 'Email'), ('call', 'Phone Call'), ('none', 'None')], default='none')

    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('business', 'job_number')]
        ordering = ['-received_at']

    def __str__(self):
        return f"JC-{self.job_number}: {self.vehicle_make} {self.vehicle_model} ({self.customer_name})"

    @property
    def total_amount(self):
        return sum(item.line_total for item in self.service_items.all())


class ServiceItem(models.Model):
    TYPES = [('labour', 'Labour'), ('part', 'Part'), ('fluid', 'Fluid'), ('subcontract', 'Subcontract'), ('other', 'Other')]
    job_card = models.ForeignKey(JobCard, on_delete=models.CASCADE, related_name='service_items')
    item_type = models.CharField(max_length=15, choices=TYPES, default='labour')
    description = models.CharField(max_length=200)
    part_number = models.CharField(max_length=50, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        ordering = ['item_type', 'description']

    @property
    def line_total(self):
        gross = self.quantity * self.unit_price
        return gross * (1 - self.discount_percent / 100)


class JobStatusLog(models.Model):
    job_card = models.ForeignKey(JobCard, on_delete=models.CASCADE, related_name='status_logs')
    old_status = models.CharField(max_length=25)
    new_status = models.CharField(max_length=25)
    note = models.CharField(max_length=200, blank=True)
    changed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']


class VehicleServiceHistory(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='vehicle_service_history')
    vehicle_reg = models.CharField(max_length=30)
    vin = models.CharField(max_length=50, blank=True)
    vehicle_make = models.CharField(max_length=60)
    vehicle_model = models.CharField(max_length=60, blank=True)
    vehicle_year = models.PositiveSmallIntegerField(null=True, blank=True)
    customer_name = models.CharField(max_length=150)
    customer_phone = models.CharField(max_length=30, blank=True)

    class Meta:
        unique_together = [('business', 'vehicle_reg')]
        ordering = ['vehicle_reg']

    def __str__(self):
        return f"{self.vehicle_reg} — {self.vehicle_make} {self.vehicle_model}"

    @property
    def job_cards(self):
        return self.business.job_cards.filter(vehicle_reg=self.vehicle_reg).order_by('-received_at')
