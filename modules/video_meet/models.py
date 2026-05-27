from django.db import models
from django.utils import timezone
from accounts.models import User


class MeetingRoom(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='meeting_rooms')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    room_code = models.CharField(max_length=50, unique=True, blank=True)
    capacity = models.PositiveIntegerField(default=20)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_rooms')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.room_code:
            import secrets
            self.room_code = secrets.token_urlsafe(8)
        super().save(*args, **kwargs)

    @property
    def meet_url(self):
        return f"https://meet.jit.si/bb-{self.room_code}"


class Meeting(models.Model):
    STATUS = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='meetings')
    room = models.ForeignKey(MeetingRoom, on_delete=models.SET_NULL, null=True, blank=True, related_name='meetings')
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    agenda = models.TextField(blank=True)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_meetings')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS, default='scheduled')
    meeting_url = models.URLField(blank=True, help_text="External link (Zoom, Teams, etc.) or auto-generated")
    is_recurring = models.BooleanField(default=False)
    recurrence_rule = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.title} — {self.start_time.strftime('%Y-%m-%d %H:%M')}"

    def save(self, *args, **kwargs):
        if not self.meeting_url and self.room:
            self.meeting_url = self.room.meet_url
        super().save(*args, **kwargs)


class MeetingAttendee(models.Model):
    STATUS = [('invited', 'Invited'), ('accepted', 'Accepted'), ('declined', 'Declined'), ('tentative', 'Tentative')]
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='attendees')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meeting_invites')
    status = models.CharField(max_length=20, choices=STATUS, default='invited')

    class Meta:
        unique_together = [('meeting', 'user')]

    def __str__(self):
        return f"{self.user.email} @ {self.meeting.title}"
