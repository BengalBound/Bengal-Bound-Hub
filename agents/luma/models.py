from django.db import models
from hub.models import BusinessInstance


class BrandMention(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="brandmention_set")
    source = models.CharField(
        max_length=10,
        choices=[
            ("news", "News"),
            ("twitter", "Twitter"),
            ("reddit", "Reddit"),
            ("review", "Review"),
            ("blog", "Blog"),
            ("forum", "Forum"),
        ],
    )
    url = models.URLField()
    title = models.CharField(max_length=500, blank=True)
    snippet = models.TextField()
    sentiment = models.CharField(
        max_length=10,
        choices=[("positive", "Positive"), ("neutral", "Neutral"), ("negative", "Negative")],
    )
    urgency = models.CharField(
        max_length=10,
        choices=[("low", "Low"), ("medium", "Medium"), ("high", "High"), ("crisis", "Crisis")],
    )
    ai_summary = models.TextField(blank=True)
    response_draft = models.TextField(blank=True)
    responded = models.BooleanField(default=False)
    detected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-detected_at"]

    def __str__(self):
        return f"[{self.source}] {self.title or self.url}"


class PressRelease(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="pressrelease_set")
    headline = models.CharField(max_length=500)
    body = models.TextField()
    boilerplate = models.TextField(blank=True)
    status = models.CharField(
        max_length=15,
        choices=[("draft", "Draft"), ("approved", "Approved"), ("distributed", "Distributed")],
        default="draft",
    )
    distributed_at = models.DateTimeField(null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-generated_at"]

    def __str__(self):
        return self.headline
