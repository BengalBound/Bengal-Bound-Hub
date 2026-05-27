from django.db import models
from hub.models import BusinessInstance, BusinessEmployee


class TravelClient(models.Model):
    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='travel_clients')
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    passport_number = models.CharField(max_length=50, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    preferred_airline = models.CharField(max_length=100, blank=True)
    frequent_flyer_number = models.CharField(max_length=100, blank=True)
    dietary_requirements = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    assigned_to = models.ForeignKey(
        BusinessEmployee, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_travel_clients'
    )

    class Meta:
        ordering = ['full_name']

    def __str__(self):
        return self.full_name


class Itinerary(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='itineraries')
    client = models.ForeignKey(TravelClient, on_delete=models.CASCADE, related_name='itineraries')
    title = models.CharField(max_length=200)
    destination = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    total_budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default='USD')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        BusinessEmployee, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='created_itineraries'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def nights(self):
        return (self.end_date - self.start_date).days


class ItineraryItem(models.Model):
    ITEM_TYPE_CHOICES = [
        ('flight', 'Flight'),
        ('hotel', 'Hotel'),
        ('transfer', 'Transfer'),
        ('activity', 'Activity'),
        ('tour', 'Tour'),
        ('meal', 'Meal'),
        ('other', 'Other'),
    ]

    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name='items')
    day_number = models.IntegerField()
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    supplier = models.CharField(max_length=200, blank=True)
    confirmation_code = models.CharField(max_length=100, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['day_number', 'start_time']

    def __str__(self):
        return f"Day {self.day_number}: {self.title}"


class TravelBooking(models.Model):
    BOOKING_TYPE_CHOICES = [
        ('flight', 'Flight'),
        ('hotel', 'Hotel'),
        ('package', 'Package'),
        ('cruise', 'Cruise'),
        ('transfer', 'Transfer'),
        ('activity', 'Activity'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('ticketed', 'Ticketed'),
        ('cancelled', 'Cancelled'),
    ]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='travel_bookings')
    client = models.ForeignKey(TravelClient, on_delete=models.CASCADE, related_name='bookings')
    itinerary = models.ForeignKey(Itinerary, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    booking_reference = models.CharField(max_length=100)
    booking_type = models.CharField(max_length=20, choices=BOOKING_TYPE_CHOICES)
    supplier = models.CharField(max_length=200)
    travel_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        BusinessEmployee, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='created_travel_bookings'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.booking_reference
