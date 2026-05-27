from django.db import models
from django.utils import timezone
from accounts.models import User


class BookingService(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='booking_services')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    duration_minutes = models.IntegerField(default=60)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=5, default='USD')
    category = models.CharField(max_length=100, blank=True)
    color = models.CharField(max_length=7, default='#3b82f6')
    buffer_before = models.IntegerField(default=0, help_text='Buffer time before appointment in minutes')
    buffer_after = models.IntegerField(default=0, help_text='Buffer time after appointment in minutes')
    max_bookings_per_slot = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class StaffAvailability(models.Model):
    DAYS = [(0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')]
    staff = models.ForeignKey(User, on_delete=models.CASCADE, related_name='availability_slots')
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='staff_availability')
    day_of_week = models.IntegerField(choices=DAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"{self.staff} — {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"


class Booking(models.Model):
    STATUS = [('pending', 'Pending'), ('confirmed', 'Confirmed'), ('completed', 'Completed'), ('cancelled', 'Cancelled'), ('no_show', 'No Show'), ('rescheduled', 'Rescheduled')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='bookings')
    service = models.ForeignKey(BookingService, on_delete=models.SET_NULL, null=True, related_name='bookings')
    staff = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='booked_appointments')
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=30, blank=True)
    booked_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='user_bookings')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    notes = models.TextField(blank=True)
    customer_notes = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_paid = models.BooleanField(default=False)
    cancellation_reason = models.TextField(blank=True)
    reminder_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-start_time']

    def __str__(self):
        return f"{self.customer_name} — {self.service} on {self.date} {self.start_time}"


class BookingBlock(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='booking_blocks')
    staff = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='blocked_slots')
    reason = models.CharField(max_length=200, blank=True)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_all_day = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_blocks')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"Blocked: {self.date} {self.start_time}-{self.end_time}"
