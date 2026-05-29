from django.db import models
from accounts.models import User

class Appointment(models.Model):
    client_name = models.CharField(max_length=150)
    client_email = models.EmailField()
    client_phone = models.CharField(max_length=20, blank=True, null=True)
    service_type = models.CharField(max_length=100, choices=(
        ('custom_website', 'Custom Website Build'),
        ('custom_webapp', 'Custom Web Application'),
        ('bengalbound_demo', 'BengalBound Demo'),
        ('ai_employee', 'AI Employee Consultation')
    ), default='custom_website')

    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=20, choices=(
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ), default='pending')

    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Optional assignment to a workspace user (employee/manager)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'role__in': ['super_admin', 'manager', 'employee']})

    def __str__(self):
        return f"{self.client_name} - {self.date} {self.time}"
