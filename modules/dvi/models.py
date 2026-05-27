from django.db import models
from django.utils import timezone


class InspectionTemplate(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='dvi_templates')
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=200, blank=True)
    checkpoints = models.JSONField(default=list)  # ["Tyres", "Brakes", "Engine Oil", ...]
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('business', 'name')]
        ordering = ['name']

    def __str__(self):
        return self.name


class VehicleInspection(models.Model):
    OVERALL = [('pass', 'Pass'), ('advisory', 'Pass with Advisories'), ('fail', 'Fail'), ('incomplete', 'Incomplete')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='vehicle_inspections')
    inspection_number = models.CharField(max_length=20)
    template = models.ForeignKey(InspectionTemplate, on_delete=models.SET_NULL, null=True, blank=True)

    # Vehicle details
    vehicle_reg = models.CharField(max_length=30)
    vehicle_make = models.CharField(max_length=60)
    vehicle_model = models.CharField(max_length=60, blank=True)
    vehicle_year = models.PositiveSmallIntegerField(null=True, blank=True)
    vin = models.CharField(max_length=50, blank=True)
    mileage = models.PositiveIntegerField(null=True, blank=True)
    colour = models.CharField(max_length=40, blank=True)

    # Customer
    customer_name = models.CharField(max_length=150, blank=True)
    customer_phone = models.CharField(max_length=30, blank=True)
    customer_email = models.EmailField(blank=True)

    # Link to job card (optional)
    job_card_number = models.CharField(max_length=20, blank=True)

    overall_result = models.CharField(max_length=15, choices=OVERALL, default='incomplete')
    performed_by = models.ForeignKey('bredbound.BusinessEmployee', on_delete=models.SET_NULL, null=True, blank=True)
    inspected_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)

    # Shared report token for customer access
    share_token = models.CharField(max_length=32, blank=True, unique=True, null=True)
    report_sent = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('business', 'inspection_number')]
        ordering = ['-inspected_at']

    def __str__(self):
        return f"DVI-{self.inspection_number}: {self.vehicle_reg}"

    def generate_share_token(self):
        import secrets
        self.share_token = secrets.token_hex(16)
        self.save(update_fields=['share_token'])
        return self.share_token

    @property
    def pass_count(self):
        return self.items.filter(status='ok').count()

    @property
    def advisory_count(self):
        return self.items.filter(status='attention').count()

    @property
    def fail_count(self):
        return self.items.filter(status='critical').count()


class InspectionItem(models.Model):
    STATUS = [
        ('ok', 'OK / Pass'),
        ('attention', 'Needs Attention (Advisory)'),
        ('critical', 'Critical / Fail'),
        ('na', 'Not Applicable'),
    ]
    inspection = models.ForeignKey(VehicleInspection, on_delete=models.CASCADE, related_name='items')
    checkpoint = models.CharField(max_length=100)
    status = models.CharField(max_length=15, choices=STATUS, default='ok')
    notes = models.TextField(blank=True)
    photo = models.ImageField(upload_to='dvi/photos/', null=True, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'checkpoint']

    def __str__(self):
        return f"{self.inspection} — {self.checkpoint} [{self.status}]"


DEFAULT_CHECKPOINTS = [
    "Engine Oil Level & Condition",
    "Coolant Level",
    "Brake Fluid Level",
    "Power Steering Fluid",
    "Windscreen Washer Fluid",
    "Battery Condition",
    "Tyres — Front Left",
    "Tyres — Front Right",
    "Tyres — Rear Left",
    "Tyres — Rear Right",
    "Spare Tyre",
    "Brake Pads — Front",
    "Brake Pads — Rear",
    "Brake Discs",
    "Brake Lines & Hoses",
    "Handbrake Operation",
    "Steering & Suspension",
    "Shock Absorbers",
    "CV Joints & Boots",
    "Exhaust System",
    "Air Filter",
    "Fuel Filter",
    "Timing Belt / Chain",
    "Drive Belts",
    "Windscreen — Chips or Cracks",
    "Wipers & Washers",
    "Lights — Headlights",
    "Lights — Taillights",
    "Lights — Indicators",
    "Lights — Reverse",
    "Horn",
    "Seatbelts",
    "Air Conditioning",
    "Heater / Ventilation",
    "Interior — General Condition",
    "Exterior — Body Condition",
    "Undercarriage — Rust / Damage",
    "Wheel Alignment (Visual)",
    "OBD Fault Codes",
]
