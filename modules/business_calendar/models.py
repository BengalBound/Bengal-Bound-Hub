from django.db import models
from accounts.models import User


class BizCalendar(models.Model):
    """A named calendar within a business (like 'Team Calendar', 'Marketing')."""
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='biz_calendars')
    name = models.CharField(max_length=200)
    color = models.CharField(max_length=30, default='#c084fc')
    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_calendars')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.business.name})"


class CalendarEvent(models.Model):
    STATUS = [
        ('confirmed', 'Confirmed'),
        ('tentative', 'Tentative'),
        ('cancelled', 'Cancelled'),
    ]
    RECURRENCE = [
        ('none', 'No Repeat'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    calendar = models.ForeignKey(BizCalendar, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=300, blank=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    all_day = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS, default='confirmed')
    recurrence = models.CharField(max_length=20, choices=RECURRENCE, default='none')
    recurrence_end = models.DateField(null=True, blank=True)
    color = models.CharField(max_length=30, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_events')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_datetime']

    def __str__(self):
        return f"{self.title} ({self.start_datetime.strftime('%Y-%m-%d %H:%M')})"


class EventAttendee(models.Model):
    RSVP = [('invited', 'Invited'), ('accepted', 'Accepted'), ('declined', 'Declined')]
    event = models.ForeignKey(CalendarEvent, on_delete=models.CASCADE, related_name='attendees')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_invites')
    rsvp = models.CharField(max_length=20, choices=RSVP, default='invited')

    class Meta:
        unique_together = [('event', 'user')]

    def __str__(self):
        return f"{self.user.email} → {self.event.title}"


class EventReminder(models.Model):
    UNITS = [('minutes', 'Minutes'), ('hours', 'Hours'), ('days', 'Days')]
    event = models.ForeignKey(CalendarEvent, on_delete=models.CASCADE, related_name='reminders')
    remind_before = models.PositiveIntegerField(default=15)
    unit = models.CharField(max_length=10, choices=UNITS, default='minutes')
    sent = models.BooleanField(default=False)

    def __str__(self):
        return f"Remind {self.remind_before} {self.unit} before {self.event.title}"
