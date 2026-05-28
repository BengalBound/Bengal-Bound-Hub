import uuid
from django.db import models
from core.models import BaseModel


class MeetingRequestStatus(models.TextChoices):
    PENDING   = "pending",   "Pending"
    SCHEDULED = "scheduled", "Scheduled"
    CANCELLED = "cancelled", "Cancelled"
    COMPLETED = "completed", "Completed"


class EmailCategory(models.TextChoices):
    INQUIRY    = "inquiry",    "General Inquiry"
    SALES      = "sales",      "Sales / Commercial"
    SUPPORT    = "support",    "Support Request"
    COMPLAINT  = "complaint",  "Complaint"
    NEWSLETTER = "newsletter", "Newsletter / Marketing"
    INTERNAL   = "internal",   "Internal"
    SPAM       = "spam",       "Spam"
    OTHER      = "other",      "Other"


class EmailPriority(models.TextChoices):
    LOW    = "low",    "Low"
    MEDIUM = "medium", "Medium"
    HIGH   = "high",   "High"
    URGENT = "urgent", "Urgent"


class MeetingRequest(BaseModel):
    id                = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization      = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="meeting_requests"
    )
    title             = models.CharField(max_length=255)
    description       = models.TextField(blank=True)
    attendees         = models.JSONField(default=list, help_text="List of attendee email addresses")
    preferred_times   = models.JSONField(default=list, help_text="List of ISO-8601 datetime strings")
    status            = models.CharField(
        max_length=20, choices=MeetingRequestStatus.choices, default=MeetingRequestStatus.PENDING
    )
    calendar_event_id = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} [{self.status}]"


class EmailTriage(BaseModel):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="email_triages"
    )
    sender       = models.EmailField()
    subject      = models.CharField(max_length=500)
    body_preview = models.TextField(help_text="First ~500 characters of the email body")
    category     = models.CharField(
        max_length=20, choices=EmailCategory.choices, default=EmailCategory.OTHER
    )
    priority     = models.CharField(
        max_length=10, choices=EmailPriority.choices, default=EmailPriority.MEDIUM
    )
    is_processed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Email Triage"
        verbose_name_plural = "Email Triages"

    def __str__(self):
        return f"{self.subject} from {self.sender} [{self.priority}]"
