from django.db import models
from hub.models import BusinessInstance


class ResearchConfig(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="researchconfig_set")
    industry = models.CharField(max_length=200)
    keywords = models.JSONField(default=list)
    competitors = models.JSONField(default=list)
    target_markets = models.JSONField(default=list)
    alert_threshold = models.IntegerField(default=70)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Research Config: {self.industry}"


class ResearchReport(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="researchreport_set")
    period = models.CharField(max_length=50)
    narrative = models.TextField(blank=True)
    key_findings = models.JSONField(default=list)
    opportunities = models.JSONField(default=list)
    threats = models.JSONField(default=list)
    recommendations = models.JSONField(default=list)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-generated_at"]

    def __str__(self):
        return f"Report: {self.period}"
