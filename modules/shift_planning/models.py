from django.db import models
from accounts.models import User


class ShiftTemplate(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='shift_templates')
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_minutes = models.IntegerField(default=0)
    color = models.CharField(max_length=7, default='#3b82f6')
    department = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.start_time} - {self.end_time})"

    @property
    def duration_hours(self):
        from datetime import datetime, date
        start = datetime.combine(date.today(), self.start_time)
        end = datetime.combine(date.today(), self.end_time)
        if end < start:
            from datetime import timedelta
            end += timedelta(days=1)
        return round((end - start).seconds / 3600 - self.break_minutes / 60, 1)


class SchedulePeriod(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='schedule_periods')
    name = models.CharField(max_length=100)
    week_start = models.DateField()
    week_end = models.DateField()
    is_published = models.BooleanField(default=False)
    published_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='published_schedules')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-week_start']

    def __str__(self):
        return f"{self.name} ({self.week_start} to {self.week_end})"


class Shift(models.Model):
    STATUS = [('scheduled', 'Scheduled'), ('confirmed', 'Confirmed'), ('completed', 'Completed'), ('cancelled', 'Cancelled'), ('absent', 'Absent')]

    period = models.ForeignKey(SchedulePeriod, on_delete=models.CASCADE, related_name='shifts')
    employee = models.ForeignKey('hr.Employee', on_delete=models.CASCADE, related_name='shifts')
    template = models.ForeignKey(ShiftTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_minutes = models.IntegerField(default=0)
    department = models.CharField(max_length=100, blank=True)
    role = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='scheduled')
    notes = models.TextField(blank=True)
    actual_start = models.TimeField(null=True, blank=True)
    actual_end = models.TimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_shifts')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.employee} — {self.date} {self.start_time}-{self.end_time}"


class ShiftSwapRequest(models.Model):
    STATUS = [('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('cancelled', 'Cancelled')]

    requester_shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='swap_requests_sent')
    target_shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='swap_requests_received', null=True, blank=True)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_swap_requests')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Swap: {self.requester_shift} ↔ {self.target_shift}"
