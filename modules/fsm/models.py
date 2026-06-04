from django.db import models
from hub.models import BusinessInstance, BusinessEmployee
from simple_history.models import HistoricalRecords

class Job(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('quoted', 'Quoted'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fsm_jobs')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    customer_name = models.CharField(max_length=150)
    customer_phone = models.CharField(max_length=30, blank=True)
    customer_email = models.EmailField(blank=True)
    
    # Location
    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Scheduling & Assignment
    scheduled_datetime = models.DateTimeField(null=True, blank=True)
    estimated_duration_hours = models.DecimalField(max_digits=4, decimal_places=2, default=1.0)
    technician = models.ForeignKey(BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='fsm_assigned_jobs')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.title} - {self.customer_name}"


class JobQuote(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='quotes')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Quote for {self.job.title}"
        
    @property
    def total_amount(self):
        return sum(item.total for item in self.items.all())


class JobQuoteItem(models.Model):
    quote = models.ForeignKey(JobQuote, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=8, decimal_places=2, default=1.0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    @property
    def total(self):
        return self.quantity * self.unit_price


class VanInventory(models.Model):
    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='fsm_van_inventories')
    technician = models.ForeignKey(BusinessEmployee, on_delete=models.CASCADE, related_name='van_inventory')
    
    item_name = models.CharField(max_length=150)
    sku = models.CharField(max_length=50, blank=True)
    quantity = models.IntegerField(default=0)
    minimum_threshold = models.IntegerField(default=5)
    
    last_restocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Van Inventories'
        unique_together = ('technician', 'sku')

    def __str__(self):
        return f"{self.item_name} - {self.technician.name}'s Van"


class CustomerSignature(models.Model):
    job = models.OneToOneField(Job, on_delete=models.CASCADE, related_name='signature')
    signature_data = models.TextField(help_text="Base64 encoded PNG signature data")
    signed_by_name = models.CharField(max_length=100)
    signed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Signature for {self.job.title}"
