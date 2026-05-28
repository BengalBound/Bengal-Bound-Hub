from django.db import models
from hub.models import BusinessInstance


class TranslationJob(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="translationjob_set")
    source_language = models.CharField(max_length=10)
    target_languages = models.JSONField(default=list)
    source_text = models.TextField()
    word_count = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=[("queued", "Queued"), ("processing", "Processing"), ("completed", "Completed"), ("failed", "Failed")],
        default="queued",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.source_language} → {self.target_languages} [{self.status}]"


class TranslationOutput(models.Model):
    job = models.ForeignKey(TranslationJob, on_delete=models.CASCADE, related_name="outputs")
    target_language = models.CharField(max_length=10)
    translated_text = models.TextField()
    quality_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["target_language"]

    def __str__(self):
        return f"Output[{self.target_language}] for Job {self.job_id}"
