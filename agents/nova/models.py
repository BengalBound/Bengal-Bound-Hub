import uuid
from django.db import models
from core.models import BaseModel


class SourceType(models.TextChoices):
    POSTGRES = "postgres", "PostgreSQL"
    MYSQL    = "mysql",    "MySQL"
    SHEETS   = "sheets",   "Google Sheets"
    API      = "api",      "REST API"
    CSV      = "csv",      "CSV Upload"


class QueryStatus(models.TextChoices):
    PENDING   = "pending",   "Pending"
    COMPLETED = "completed", "Completed"
    FAILED    = "failed",    "Failed"


class DataSource(BaseModel):
    id                = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization      = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="data_sources")
    name              = models.CharField(max_length=255)
    source_type       = models.CharField(max_length=20, choices=SourceType.choices)
    connection_config = models.JSONField(default=dict)
    is_active         = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.source_type})"


class DataQuery(BaseModel):
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization    = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="data_queries")
    data_source     = models.ForeignKey(DataSource, on_delete=models.SET_NULL, null=True, blank=True, related_name="queries")
    question        = models.TextField()
    generated_sql   = models.TextField(blank=True)
    results_preview = models.JSONField(default=list)
    status          = models.CharField(max_length=20, choices=QueryStatus.choices, default=QueryStatus.PENDING)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.question[:80]
