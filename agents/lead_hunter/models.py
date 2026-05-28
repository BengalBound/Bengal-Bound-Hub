import uuid
from django.db import models
from core.models import BaseModel

class ProspectStatus(models.TextChoices):
    NEW       = "new",       "New"
    CONTACTED = "contacted", "Contacted"
    QUALIFIED = "qualified", "Qualified"
    LOST      = "lost",      "Lost"

class SequenceStatus(models.TextChoices):
    DRAFT  = "draft",  "Draft"
    ACTIVE = "active", "Active"
    PAUSED = "paused", "Paused"

class Prospect(BaseModel):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business     = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="lead_hunter_prospects")
    company_name = models.CharField(max_length=255)
    contact_name = models.CharField(max_length=255, blank=True)
    email        = models.EmailField(blank=True)
    linkedin_url = models.URLField(blank=True)
    industry     = models.CharField(max_length=100, blank=True)
    score        = models.PositiveSmallIntegerField(default=0)
    status       = models.CharField(max_length=20, choices=ProspectStatus.choices, default=ProspectStatus.NEW)
    notes        = models.TextField(blank=True)
    ai_summary   = models.TextField(blank=True)

    class Meta:
        ordering = ["-score", "-created_at"]

    def __str__(self):
        return f"{self.company_name} ({self.contact_name})"

class OutreachSequence(BaseModel):
    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business         = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="lead_hunter_outreach_sequences")
    name             = models.CharField(max_length=255)
    target_criteria  = models.JSONField(default=dict)
    status           = models.CharField(max_length=20, choices=SequenceStatus.choices, default=SequenceStatus.DRAFT)
    prospects        = models.ManyToManyField(Prospect, blank=True, related_name="sequences")

    def __str__(self):
        return self.name
