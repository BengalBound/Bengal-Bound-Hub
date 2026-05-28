import uuid
from django.db import models
from core.models import BaseModel


class PipelineProvider(models.TextChoices):
    GITHUB    = "github",    "GitHub"
    GITLAB    = "gitlab",    "GitLab"
    BITBUCKET = "bitbucket", "Bitbucket"


class PipelineStatus(models.TextChoices):
    PASSING = "passing", "Passing"
    FAILING = "failing", "Failing"
    UNKNOWN = "unknown", "Unknown"


class IncidentSeverity(models.TextChoices):
    LOW      = "low",      "Low"
    MEDIUM   = "medium",   "Medium"
    HIGH     = "high",     "High"
    CRITICAL = "critical", "Critical"


class IncidentStatus(models.TextChoices):
    OPEN         = "open",         "Open"
    INVESTIGATING = "investigating", "Investigating"
    RESOLVED     = "resolved",     "Resolved"


class Pipeline(BaseModel):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="pipelines")
    name         = models.CharField(max_length=255)
    repo_url     = models.URLField()
    provider     = models.CharField(max_length=20, choices=PipelineProvider.choices, default=PipelineProvider.GITHUB)
    last_status  = models.CharField(max_length=20, choices=PipelineStatus.choices, default=PipelineStatus.UNKNOWN)
    last_run_at  = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.provider})"


class Incident(BaseModel):
    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization   = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="incidents")
    pipeline       = models.ForeignKey(Pipeline, on_delete=models.SET_NULL, null=True, blank=True, related_name="incidents")
    title          = models.CharField(max_length=255)
    severity       = models.CharField(max_length=20, choices=IncidentSeverity.choices, default=IncidentSeverity.MEDIUM)
    status         = models.CharField(max_length=20, choices=IncidentStatus.choices, default=IncidentStatus.OPEN)
    description    = models.TextField()
    ai_root_cause  = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.severity.upper()}] {self.title}"
