from django.db import models
from hub.models import BusinessInstance, BusinessEmployee

DAYS_OF_WEEK = [
    (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
    (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
]


class Room(models.Model):
    ROOM_TYPE = [
        ('classroom', 'Classroom'),
        ('lab', 'Laboratory / Computer Lab'),
        ('hall', 'Hall / Auditorium'),
        ('online', 'Online / Virtual'),
        ('sports', 'Sports Facility'),
        ('workshop', 'Workshop / Studio'),
        ('other', 'Other'),
    ]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='rooms')
    name = models.CharField(max_length=100)
    room_type = models.CharField(max_length=15, choices=ROOM_TYPE, default='classroom')
    capacity = models.PositiveIntegerField(null=True, blank=True)
    building = models.CharField(max_length=100, blank=True)
    floor = models.CharField(max_length=20, blank=True)
    equipment = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class TimeSlot(models.Model):
    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='time_slots')
    label = models.CharField(max_length=50, verbose_name='Label (e.g. Period 1, Morning Block)')
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"{self.get_day_of_week_display()} {self.label} ({self.start_time:%H:%M}–{self.end_time:%H:%M})"


class ClassSession(models.Model):
    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='class_sessions')
    subject = models.CharField(max_length=150)
    class_group = models.CharField(max_length=50, blank=True, verbose_name='Class / Group')
    instructor = models.ForeignKey(BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='teaching_sessions')
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True)
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.SET_NULL, null=True, blank=True)
    effective_from = models.DateField()
    effective_until = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['time_slot__day_of_week', 'time_slot__start_time']

    def __str__(self):
        return f"{self.subject} — {self.class_group}"


class ScheduleException(models.Model):
    session = models.ForeignKey(ClassSession, on_delete=models.CASCADE, related_name='exceptions')
    exception_date = models.DateField()
    reason = models.CharField(max_length=200)
    is_cancelled = models.BooleanField(default=True)
    substitute_instructor = models.ForeignKey(BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='substitute_sessions')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-exception_date']
