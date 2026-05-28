import uuid
from django.db import models
from core.models import BaseModel

class TicketChannel(models.TextChoices):
    EMAIL  = "email",  "Email"
    CHAT   = "chat",   "Chat"
    WIDGET = "widget", "Widget"
    PHONE  = "phone",  "Phone"

class TicketStatus(models.TextChoices):
    OPEN        = "open",        "Open"
    IN_PROGRESS = "in_progress", "In Progress"
    RESOLVED    = "resolved",    "Resolved"
    CLOSED      = "closed",      "Closed"

class TicketPriority(models.TextChoices):
    LOW    = "low",    "Low"
    MEDIUM = "medium", "Medium"
    HIGH   = "high",   "High"
    URGENT = "urgent", "Urgent"

class SupportTicket(BaseModel):
    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business       = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="aria_support_tickets")
    subject        = models.CharField(max_length=500)
    description    = models.TextField()
    channel        = models.CharField(max_length=20, choices=TicketChannel.choices, default=TicketChannel.EMAIL)
    status         = models.CharField(max_length=20, choices=TicketStatus.choices, default=TicketStatus.OPEN)
    priority       = models.CharField(max_length=20, choices=TicketPriority.choices, default=TicketPriority.MEDIUM)
    customer_email = models.EmailField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.priority.upper()}] {self.subject}"

class TicketResponse(BaseModel):
    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket           = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name="responses")
    content          = models.TextField()
    is_ai_generated  = models.BooleanField(default=False)
    sent_at          = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]
