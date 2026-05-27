from django.db import models
from django.utils import timezone


class Carrier(models.Model):
    TYPES = [
        ('road', 'Road / Truck'), ('air', 'Air Freight'),
        ('sea', 'Sea / Ocean'), ('rail', 'Rail'),
        ('courier', 'Courier / Express'), ('intermodal', 'Intermodal'),
    ]
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='carriers')
    name = models.CharField(max_length=150)
    carrier_type = models.CharField(max_length=15, choices=TYPES, default='road')
    contact_name = models.CharField(max_length=100, blank=True)
    contact_phone = models.CharField(max_length=30, blank=True)
    contact_email = models.EmailField(blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [('business', 'name')]
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_carrier_type_display()})"


class Route(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='routes')
    name = models.CharField(max_length=150)
    origin = models.CharField(max_length=200)
    destination = models.CharField(max_length=200)
    distance_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estimated_hours = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    preferred_carrier = models.ForeignKey(Carrier, on_delete=models.SET_NULL, null=True, blank=True)
    base_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name}: {self.origin} → {self.destination}"


class Shipment(models.Model):
    STATUS = [
        ('draft', 'Draft'), ('booked', 'Booked'),
        ('pickup_ready', 'Ready for Pickup'), ('in_transit', 'In Transit'),
        ('at_hub', 'At Hub / Depot'), ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'), ('delayed', 'Delayed'),
        ('exception', 'Exception / Issue'), ('cancelled', 'Cancelled'),
    ]
    SHIPMENT_TYPE = [
        ('inbound', 'Inbound'), ('outbound', 'Outbound'),
        ('transfer', 'Internal Transfer'), ('return', 'Return'),
    ]
    PRIORITY = [('standard', 'Standard'), ('express', 'Express'), ('urgent', 'Urgent')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='shipments')
    shipment_number = models.CharField(max_length=30)
    shipment_type = models.CharField(max_length=15, choices=SHIPMENT_TYPE, default='outbound')
    priority = models.CharField(max_length=10, choices=PRIORITY, default='standard')

    carrier = models.ForeignKey(Carrier, on_delete=models.SET_NULL, null=True, blank=True, related_name='shipments')
    route = models.ForeignKey(Route, on_delete=models.SET_NULL, null=True, blank=True, related_name='shipments')

    # Addresses
    origin_name = models.CharField(max_length=150, blank=True)
    origin_address = models.TextField(blank=True)
    destination_name = models.CharField(max_length=150, blank=True)
    destination_address = models.TextField()

    # Customer / reference
    customer_name = models.CharField(max_length=150, blank=True)
    customer_reference = models.CharField(max_length=100, blank=True)
    purchase_order_ref = models.CharField(max_length=100, blank=True)

    # Cargo
    cargo_description = models.TextField(blank=True)
    pieces = models.PositiveIntegerField(null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    volume_m3 = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    is_hazmat = models.BooleanField(default=False)
    requires_refrigeration = models.BooleanField(default=False)

    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    tracking_number = models.CharField(max_length=100, blank=True)

    # Dates
    scheduled_pickup = models.DateTimeField(null=True, blank=True)
    scheduled_delivery = models.DateTimeField(null=True, blank=True)
    actual_pickup = models.DateTimeField(null=True, blank=True)
    actual_delivery = models.DateTimeField(null=True, blank=True)

    # Financials
    freight_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    insurance_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('business', 'shipment_number')]
        ordering = ['-created_at']

    def __str__(self):
        return f"SHP-{self.shipment_number}: {self.origin_address} → {self.destination_address}"

    @property
    def is_on_time(self):
        if self.status == 'delivered' and self.actual_delivery and self.scheduled_delivery:
            return self.actual_delivery <= self.scheduled_delivery
        return None


class ShipmentEvent(models.Model):
    EVENT_TYPES = [
        ('booked', 'Booked'), ('pickup', 'Picked Up'),
        ('departed', 'Departed'), ('arrived_hub', 'Arrived at Hub'),
        ('customs', 'Customs Clearance'), ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'), ('attempt_failed', 'Delivery Attempt Failed'),
        ('delayed', 'Delayed'), ('exception', 'Exception'), ('note', 'Note'),
    ]
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default='note')
    location = models.CharField(max_length=200, blank=True)
    note = models.CharField(max_length=300, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    recorded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.shipment} — {self.get_event_type_display()} @ {self.timestamp:%Y-%m-%d %H:%M}"


class FreightQuote(models.Model):
    STATUS = [('draft', 'Draft'), ('sent', 'Sent to Client'), ('accepted', 'Accepted'), ('rejected', 'Rejected'), ('expired', 'Expired')]
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='freight_quotes')
    quote_number = models.CharField(max_length=20)
    customer_name = models.CharField(max_length=150)
    customer_email = models.EmailField(blank=True)
    origin = models.CharField(max_length=200)
    destination = models.CharField(max_length=200)
    cargo_description = models.TextField(blank=True)
    weight_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    volume_m3 = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    carrier = models.ForeignKey(Carrier, on_delete=models.SET_NULL, null=True, blank=True)
    quoted_price = models.DecimalField(max_digits=12, decimal_places=2)
    transit_days = models.PositiveSmallIntegerField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS, default='draft')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('business', 'quote_number')]
        ordering = ['-created_at']

    def __str__(self):
        return f"FQ-{self.quote_number}: {self.customer_name}"
