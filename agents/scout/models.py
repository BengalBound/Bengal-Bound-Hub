from django.db import models
from hub.models import BusinessInstance


class Competitor(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="competitor_set")
    name = models.CharField(max_length=300)
    website = models.URLField()
    pricing_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    twitter_handle = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    last_checked = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class CompetitorChange(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="competitorchange_set")
    competitor = models.ForeignKey(Competitor, on_delete=models.CASCADE, related_name="changes")
    change_type = models.CharField(
        max_length=10,
        choices=[
            ("pricing", "Pricing"),
            ("product", "Product"),
            ("hiring", "Hiring"),
            ("ad", "Ad"),
            ("content", "Content"),
            ("pr", "PR"),
        ],
    )
    impact = models.CharField(
        max_length=10,
        choices=[("low", "Low"), ("medium", "Medium"), ("high", "High")],
    )
    description = models.TextField()
    ai_analysis = models.TextField(blank=True)
    source_url = models.URLField(blank=True)
    alert_sent = models.BooleanField(default=False)
    detected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-detected_at"]

    def __str__(self):
        return f"[{self.change_type}] {self.competitor.name}"
