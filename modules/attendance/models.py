from django.db import models
from django.utils import timezone
from accounts.models import User


class WorkSchedule(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='att_schedules')
    name = models.CharField(max_length=100)
    work_hours_per_day = models.DecimalField(max_digits=4, decimal_places=1, default=8.0)
    work_days = models.JSONField(default=list, help_text='List of weekday numbers 0=Mon 6=Sun')
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class AttendanceRecord(models.Model):
    STATUS = [('present', 'Present'), ('absent', 'Absent'), ('late', 'Late'), ('half_day', 'Half Day'), ('leave', 'On Leave')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='att_records')
    employee = models.ForeignKey('hr.Employee', on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(default=timezone.now)
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS, default='present')
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='recorded_attendance')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        unique_together = [('employee', 'date')]

    def __str__(self):
        return f"{self.employee} — {self.date} ({self.get_status_display()})"


class Timesheet(models.Model):
    STATUS = [('draft', 'Draft'), ('submitted', 'Submitted'), ('approved', 'Approved'), ('rejected', 'Rejected')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='att_timesheets')
    employee = models.ForeignKey('hr.Employee', on_delete=models.CASCADE, related_name='timesheets')
    week_start = models.DateField()
    week_end = models.DateField()
    total_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    billable_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_timesheets')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-week_start']
        unique_together = [('employee', 'week_start')]

    def __str__(self):
        return f"{self.employee} — Week of {self.week_start}"


class TimesheetEntry(models.Model):
    timesheet = models.ForeignKey(Timesheet, on_delete=models.CASCADE, related_name='entries')
    date = models.DateField()
    project = models.CharField(max_length=200, blank=True)
    task = models.CharField(max_length=200, blank=True)
    hours = models.DecimalField(max_digits=5, decimal_places=2)
    is_billable = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.date}: {self.hours}h — {self.task or self.project}"
