from django.db import models
from hub.models import BusinessInstance, BusinessEmployee


class HousekeepingSchedule(models.Model):
    TASK_TYPE_CHOICES = [
        ('checkout_clean', 'Checkout Clean'),
        ('stayover', 'Stayover'),
        ('deep_clean', 'Deep Clean'),
        ('turndown', 'Turndown'),
        ('inspection', 'Inspection'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('skipped', 'Skipped'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='housekeeping_schedules')
    room_identifier = models.CharField(max_length=50)
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES, default='checkout_clean')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_to = models.ForeignKey(
        BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='hosp_housekeeping_tasks'
    )
    scheduled_date = models.DateField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    notes = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scheduled_date', 'priority', 'room_identifier']

    def __str__(self):
        return f"{self.room_identifier} - {self.task_type}"


class MaintenanceTicket(models.Model):
    CATEGORY_CHOICES = [
        ('plumbing', 'Plumbing'),
        ('electrical', 'Electrical'),
        ('hvac', 'HVAC'),
        ('furniture', 'Furniture'),
        ('it', 'IT'),
        ('general', 'General'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='maintenance_tickets')
    room_identifier = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=150, blank=True)
    ticket_number = models.CharField(max_length=20, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    reported_by = models.ForeignKey(
        BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reported_tickets'
    )
    assigned_to = models.ForeignKey(
        BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_tickets'
    )
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.ticket_number

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.ticket_number:
            self.ticket_number = f'MNT-{self.pk:05d}'
            MaintenanceTicket.objects.filter(pk=self.pk).update(ticket_number=self.ticket_number)


class ServiceRequest(models.Model):
    REQUEST_TYPE_CHOICES = [
        ('roomservice', 'Room Service'),
        ('extra_towels', 'Extra Towels'),
        ('wake_up', 'Wake-Up Call'),
        ('laundry', 'Laundry'),
        ('concierge', 'Concierge'),
        ('transport', 'Transport'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    PRIORITY_CHOICES = [
        ('normal', 'Normal'),
        ('urgent', 'Urgent'),
    ]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='service_requests')
    room_identifier = models.CharField(max_length=50, blank=True)
    guest_name = models.CharField(max_length=150, blank=True)
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPE_CHOICES, default='concierge')
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    assigned_to = models.ForeignKey(
        BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_service_requests'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.request_type} - {self.room_identifier}"


class ConciergeNote(models.Model):
    NOTE_TYPE_CHOICES = [
        ('preference', 'Preference'),
        ('complaint', 'Complaint'),
        ('compliment', 'Compliment'),
        ('request', 'Request'),
        ('vip_alert', 'VIP Alert'),
        ('other', 'Other'),
    ]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='concierge_notes')
    guest_name = models.CharField(max_length=150)
    note_type = models.CharField(max_length=20, choices=NOTE_TYPE_CHOICES, default='preference')
    content = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='concierge_notes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.note_type}: {self.guest_name}"
