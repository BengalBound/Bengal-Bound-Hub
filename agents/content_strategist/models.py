import uuid
from django.db import models
from core.models import BaseModel


class ContentType(models.TextChoices):
    BLOG_POST = "blog_post", "Blog Post"
    EMAIL     = "email",     "Email"
    SOCIAL    = "social",    "Social Media Post"
    AD_COPY   = "ad_copy",   "Ad Copy"


class ContentStatus(models.TextChoices):
    DRAFT     = "draft",     "Draft"
    GENERATED = "generated", "Generated"
    APPROVED  = "approved",  "Approved"


class CampaignStatus(models.TextChoices):
    PLANNING  = "planning",  "Planning"
    ACTIVE    = "active",    "Active"
    PAUSED    = "paused",    "Paused"
    COMPLETED = "completed", "Completed"


class ContentPiece(BaseModel):
    id                = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business          = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="content_strategist_pieces")
    title             = models.CharField(max_length=255)
    content_type      = models.CharField(max_length=20, choices=ContentType.choices, default=ContentType.BLOG_POST)
    prompt            = models.TextField(help_text="Instructions sent to AI for content generation")
    generated_content = models.TextField(blank=True)
    status            = models.CharField(max_length=20, choices=ContentStatus.choices, default=ContentStatus.DRAFT)
    word_count        = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} [{self.content_type}] — {self.status}"


class Campaign(BaseModel):
    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business       = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="serea_campaigns")
    name           = models.CharField(max_length=255)
    goal           = models.TextField(blank=True)
    status         = models.CharField(max_length=20, choices=CampaignStatus.choices, default=CampaignStatus.PLANNING)
    content_pieces = models.ManyToManyField(ContentPiece, blank=True, related_name="campaigns")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} [{self.status}]"
