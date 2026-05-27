import json
from django.db import models
from hub.models import BusinessInstance, BusinessEmployee


class RoomType(models.Model):
    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='room_types')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    max_occupancy = models.PositiveIntegerField(default=2)
    base_rate = models.DecimalField(max_digits=10, decimal_places=2)
    amenities_json = models.TextField(blank=True, default='[]', verbose_name='Amenities (JSON)')

    class Meta:
        ordering = ['name']
        unique_together = [('business', 'code')]

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def amenity_list(self):
        try:
            data = json.loads(self.amenities_json)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, TypeError):
            return []


class Room(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('dirty', 'Dirty'),
        ('maintenance', 'Maintenance'),
        ('blocked', 'Blocked'),
    ]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='hotel_rooms')
    room_number = models.CharField(max_length=20)
    room_type = models.ForeignKey(RoomType, on_delete=models.SET_NULL, null=True, blank=True, related_name='hotel_rooms')
    floor = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='available')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['room_number']
        unique_together = [('business', 'room_number')]

    def __str__(self):
        return f"Room {self.room_number} — {self.get_status_display()}"


class GuestProfile(models.Model):
    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='guests')
    full_name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    passport_number = models.CharField(max_length=60, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['full_name']

    def __str__(self):
        return self.full_name


class Reservation(models.Model):
    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked In'),
        ('checked_out', 'Checked Out'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    SOURCE_CHOICES = [
        ('direct', 'Direct'),
        ('ota', 'OTA'),
        ('gds', 'GDS'),
        ('phone', 'Phone'),
        ('walkin', 'Walk-in'),
    ]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='reservations')
    reservation_number = models.CharField(max_length=20, blank=True, unique=True, editable=False)
    guest = models.ForeignKey(GuestProfile, on_delete=models.PROTECT, related_name='reservations')
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservations')
    room_type = models.ForeignKey(RoomType, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservations')
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    adults = models.PositiveIntegerField(default=1)
    children = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='confirmed')
    rate_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=5, default='USD')
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='direct')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_reservations'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reservation_number} — {self.guest.full_name}"

    @property
    def nights(self):
        return (self.check_out_date - self.check_in_date).days

    def save(self, *args, **kwargs):
        # Save first to get a PK, then set reservation_number if blank
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and not self.reservation_number:
            self.reservation_number = f"RES-{self.pk:06d}"
            Reservation.objects.filter(pk=self.pk).update(reservation_number=self.reservation_number)


class FolioCharge(models.Model):
    CHARGE_TYPE_CHOICES = [
        ('room', 'Room'),
        ('food', 'Food'),
        ('beverage', 'Beverage'),
        ('service', 'Service'),
        ('tax', 'Tax'),
        ('other', 'Other'),
    ]

    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='folio_charges')
    charge_type = models.CharField(max_length=15, choices=CHARGE_TYPE_CHOICES)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=5, default='USD')
    posted_at = models.DateTimeField(auto_now_add=True)
    posted_by = models.ForeignKey(
        BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='posted_charges'
    )

    class Meta:
        ordering = ['-posted_at']

    def __str__(self):
        return f"{self.get_charge_type_display()} — {self.description} ({self.amount})"


class HousekeepingTask(models.Model):
    TASK_TYPE_CHOICES = [
        ('checkout_clean', 'Checkout Clean'),
        ('stayover', 'Stayover'),
        ('deep_clean', 'Deep Clean'),
        ('inspection', 'Inspection'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='pms_housekeeping_tasks')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='pms_housekeeping_tasks')
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    assigned_to = models.ForeignKey(
        BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='pms_housekeeping_tasks'
    )
    scheduled_date = models.DateField()
    notes = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['scheduled_date', 'room__room_number']

    def __str__(self):
        return f"{self.get_task_type_display()} — Room {self.room.room_number} ({self.scheduled_date})"
