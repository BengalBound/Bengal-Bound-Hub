import uuid
from django.db import models
from core.models import BaseModel


class CalendarStatus(models.TextChoices):
    DRAFT     = "draft",     "Draft"
    ACTIVE    = "active",    "Active"
    COMPLETED = "completed", "Completed"


class EntryChannel(models.TextChoices):
    BLOG   = "blog",   "Blog"
    EMAIL  = "email",  "Email"
    SOCIAL = "social", "Social"
    VIDEO  = "video",  "Video"
    AD     = "ad",     "Ad Copy"


class EntryStatus(models.TextChoices):
    PLANNED   = "planned",   "Planned"
    GENERATED = "generated", "Generated"
    APPROVED  = "approved",  "Approved"
    PUBLISHED = "published", "Published"


class ContentCalendar(BaseModel):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="content_calendars")
    name         = models.CharField(max_length=255)
    goal         = models.TextField(blank=True)
    month        = models.DateField()
    status       = models.CharField(max_length=20, choices=CalendarStatus.choices, default=CalendarStatus.DRAFT)

    def __str__(self):
        return f"{self.name} ({self.month})"


class CalendarEntry(BaseModel):
    id                = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    calendar          = models.ForeignKey(ContentCalendar, on_delete=models.CASCADE, related_name="entries")
    title             = models.CharField(max_length=255)
    channel           = models.CharField(max_length=20, choices=EntryChannel.choices)
    publish_date      = models.DateField()
    brief             = models.TextField()
    generated_content = models.TextField(blank=True)
    status            = models.CharField(max_length=20, choices=EntryStatus.choices, default=EntryStatus.PLANNED)

    class Meta:
        ordering = ["publish_date"]

    def __str__(self):
        return f"{self.title} ({self.channel})"
