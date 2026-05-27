from django.db import models
from hub.models import BusinessInstance, BusinessEmployee


class CorporateAccount(models.Model):
    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='corporate_accounts')
    company_name = models.CharField(max_length=200)
    contact_name = models.CharField(max_length=150)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=50, blank=True)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default='USD')
    travel_policy_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['company_name']

    def __str__(self):
        return self.company_name


class TravelPolicy(models.Model):
    APPLIES_TO_CHOICES = [
        ('all', 'All'),
        ('specific', 'Specific'),
    ]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='travel_policies')
    name = models.CharField(max_length=150)
    applies_to = models.CharField(max_length=20, choices=APPLIES_TO_CHOICES, default='all')
    max_hotel_rate_usd = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_flight_economy = models.BooleanField(default=True)
    require_advance_booking_days = models.IntegerField(default=7)
    require_approval = models.BooleanField(default=True)
    approval_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=500)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Travel Policies'

    def __str__(self):
        return self.name


class TravelRequest(models.Model):
    TRAVEL_TYPE_CHOICES = [
        ('flight', 'Flight'),
        ('hotel', 'Hotel'),
        ('flight_hotel', 'Flight + Hotel'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('booked', 'Booked'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='travel_requests')
    request_number = models.CharField(max_length=20, blank=True)
    requester = models.ForeignKey(
        BusinessEmployee, on_delete=models.CASCADE, related_name='travel_requests'
    )
    corporate_account = models.ForeignKey(
        CorporateAccount, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='travel_requests'
    )
    trip_purpose = models.CharField(max_length=300, blank=True)
    departure_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    origin = models.CharField(max_length=150, blank=True)
    destination = models.CharField(max_length=150)
    travel_type = models.CharField(max_length=20, choices=TRAVEL_TYPE_CHOICES, default='flight_hotel')
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(
        BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_requests'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    booking_reference = models.CharField(max_length=100, blank=True)
    actual_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.request_number

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.request_number:
            self.request_number = f'TR-{self.pk:05d}'
            TravelRequest.objects.filter(pk=self.pk).update(request_number=self.request_number)

    @property
    def nights(self):
        if self.return_date:
            return (self.return_date - self.departure_date).days
        return None


class TravelExpense(models.Model):
    EXPENSE_TYPE_CHOICES = [
        ('flight', 'Flight'),
        ('hotel', 'Hotel'),
        ('meals', 'Meals'),
        ('transport', 'Transport'),
        ('other', 'Other'),
    ]

    travel_request = models.ForeignKey(TravelRequest, on_delete=models.CASCADE, related_name='expenses')
    expense_type = models.CharField(max_length=20, choices=EXPENSE_TYPE_CHOICES)
    description = models.CharField(max_length=300)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    receipt_url = models.URLField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return self.description
