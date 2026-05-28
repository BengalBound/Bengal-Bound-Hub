from django.db import models
from hub.models import BusinessInstance


class Doctor(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="doctor_set")
    name = models.CharField(max_length=300)
    specialty = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    slot_duration = models.IntegerField(default=20)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"Dr. {self.name} ({self.specialty})"


class Appointment(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="appointment_set")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="appointments")
    patient_name = models.CharField(max_length=300)
    patient_phone = models.CharField(max_length=30)
    patient_email = models.EmailField(blank=True)
    scheduled_at = models.DateTimeField()
    duration = models.IntegerField(default=20)
    reason = models.CharField(max_length=500, blank=True)
    status = models.CharField(
        max_length=15,
        choices=[
            ("booked", "Booked"),
            ("confirmed", "Confirmed"),
            ("cancelled", "Cancelled"),
            ("rescheduled", "Rescheduled"),
            ("completed", "Completed"),
            ("no_show", "No Show"),
        ],
        default="booked",
    )
    reminder_sent = models.BooleanField(default=False)
    ai_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["scheduled_at"]

    def __str__(self):
        return f"{self.patient_name} with {self.doctor.name} @ {self.scheduled_at}"
