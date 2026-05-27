from django.db import models
from django.utils import timezone
from accounts.models import User


class DeliveryZone(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='delivery_zones')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    base_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Driver(models.Model):
    STATUS = [('available', 'Available'), ('on_delivery', 'On Delivery'), ('off_duty', 'Off Duty')]
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='drivers')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='driver_profiles')
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    license_number = models.CharField(max_length=50, blank=True)
    vehicle_type = models.CharField(max_length=50, blank=True)
    vehicle_plate = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='available')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class DeliveryOrder(models.Model):
    STATUS = [('pending', 'Pending'), ('assigned', 'Assigned'), ('picked_up', 'Picked Up'), ('in_transit', 'In Transit'), ('delivered', 'Delivered'), ('failed', 'Failed'), ('returned', 'Returned')]
    PRIORITY = [('low', 'Low'), ('normal', 'Normal'), ('high', 'High'), ('express', 'Express')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='delivery_orders')
    order_number = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY, default='normal')
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True, related_name='deliveries')
    zone = models.ForeignKey(DeliveryZone, on_delete=models.SET_NULL, null=True, blank=True)

    pickup_address = models.TextField()
    pickup_contact = models.CharField(max_length=100, blank=True)
    pickup_phone = models.CharField(max_length=30, blank=True)
    pickup_time = models.DateTimeField(null=True, blank=True)

    delivery_address = models.TextField()
    delivery_contact = models.CharField(max_length=100, blank=True)
    delivery_phone = models.CharField(max_length=30, blank=True)
    scheduled_date = models.DateField(default=timezone.now)
    delivery_window_start = models.TimeField(null=True, blank=True)
    delivery_window_end = models.TimeField(null=True, blank=True)

    weight_kg = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True)
    special_instructions = models.TextField(blank=True)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    proof_of_delivery = models.ImageField(upload_to='delivery/proof/', null=True, blank=True)
    signature = models.TextField(blank=True, help_text='Base64 signature')
    delivered_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)
    tracking_url = models.URLField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_deliveries')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-scheduled_date', '-created_at']

    def __str__(self):
        return f"DEL-{self.order_number}"


class DeliveryRoute(models.Model):
    STATUS = [('planned', 'Planned'), ('active', 'Active'), ('completed', 'Completed')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='delivery_routes')
    name = models.CharField(max_length=100)
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True, related_name='routes')
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS, default='planned')
    orders = models.ManyToManyField(DeliveryOrder, blank=True, related_name='routes')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.name} ({self.date})"
