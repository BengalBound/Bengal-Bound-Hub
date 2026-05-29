from django.db import models
from accounts.models import User


class DiningArea(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='dining_areas')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    position = models.IntegerField(default=0)

    class Meta:
        ordering = ['position', 'name']

    def __str__(self):
        return self.name


class Table(models.Model):
    STATUS = [('available', 'Available'), ('occupied', 'Occupied'), ('reserved', 'Reserved'), ('cleaning', 'Cleaning'), ('inactive', 'Inactive')]
    SHAPE = [('square', 'Square'), ('round', 'Round'), ('rectangle', 'Rectangle')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='tables')
    area = models.ForeignKey(DiningArea, on_delete=models.SET_NULL, null=True, blank=True, related_name='tables')
    table_number = models.CharField(max_length=10)
    capacity = models.IntegerField(default=4)
    shape = models.CharField(max_length=15, choices=SHAPE, default='square')
    status = models.CharField(max_length=20, choices=STATUS, default='available')
    position_x = models.IntegerField(default=0)
    position_y = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['table_number']
        unique_together = [('business', 'table_number')]

    def __str__(self):
        return f"Table {self.table_number} ({self.business.name})"


class Reservation(models.Model):
    STATUS = [('pending', 'Pending'), ('confirmed', 'Confirmed'), ('seated', 'Seated'), ('completed', 'Completed'), ('cancelled', 'Cancelled'), ('no_show', 'No Show')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='table_reservations')
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservations')
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=30, blank=True)
    party_size = models.IntegerField(default=2)
    date = models.DateField()
    time = models.TimeField()
    duration_minutes = models.IntegerField(default=90)
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    special_requests = models.TextField(blank=True)
    occasion = models.CharField(max_length=100, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_reservations')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-time']

    def __str__(self):
        return f"{self.customer_name} — {self.date} {self.time} (Table {self.table})"


class TableOrder(models.Model):
    STATUS = [('open', 'Open'), ('paid', 'Paid'), ('voided', 'Voided')]
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, related_name='orders')
    server = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='served_orders')
    status = models.CharField(max_length=10, choices=STATUS, default='open')
    cover_count = models.IntegerField(default=1)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tip_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    opened_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-opened_at']

    def __str__(self):
        return f"Order #{self.pk} — Table {self.table}"
