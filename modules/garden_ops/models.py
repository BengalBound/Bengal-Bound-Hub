from django.db import models
from hub.models import BusinessInstance, BusinessEmployee


class ClientSite(models.Model):
    SITE_TYPE_CHOICES = [
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('public', 'Public / Council'),
        ('estate', 'Estate / HOA'),
        ('other', 'Other'),
    ]
    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='garden_sites')
    client_name = models.CharField(max_length=200)
    site_name = models.CharField(max_length=200, blank=True)
    address = models.TextField(blank=True)
    site_type = models.CharField(max_length=20, choices=SITE_TYPE_CHOICES, default='residential')
    area_sqm = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    contact_phone = models.CharField(max_length=30, blank=True)
    contact_email = models.EmailField(blank=True)
    assigned_to = models.ForeignKey(BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='garden_sites')
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client_name} – {self.site_name or self.address[:40]}"


class GardenJob(models.Model):
    JOB_TYPE_CHOICES = [
        ('mowing', 'Mowing / Lawn Care'),
        ('planting', 'Planting'),
        ('pruning', 'Pruning / Trimming'),
        ('landscaping', 'Landscaping Design'),
        ('irrigation', 'Irrigation'),
        ('weeding', 'Weeding'),
        ('maintenance', 'General Maintenance'),
        ('seasonal', 'Seasonal Clearance'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='garden_jobs')
    site = models.ForeignKey(ClientSite, on_delete=models.CASCADE, related_name='garden_jobs')
    title = models.CharField(max_length=200)
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default='maintenance')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    scheduled_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    assigned_to = models.ForeignKey(BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='garden_jobs')
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=5, default='USD')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.site.client_name} – {self.title}"


class GardenInventoryItem(models.Model):
    CATEGORY_CHOICES = [
        ('plant', 'Plant / Seed'),
        ('tool', 'Tool / Equipment'),
        ('chemical', 'Chemical / Fertiliser'),
        ('material', 'Material / Aggregate'),
        ('pot', 'Pot / Container'),
        ('other', 'Other'),
    ]
    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='garden_inventory_items')
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='plant')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit = models.CharField(max_length=20, default='each')
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    supplier = models.CharField(max_length=200, blank=True)
    low_stock_threshold = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
